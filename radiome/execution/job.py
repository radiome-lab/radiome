from collections import Callable

import cloudpickle
from radiome.resource_pool import Resource, ResourcePool
from radiome.utils import deterministic_hash, Hashable


class Job(Hashable):
    _reference = None
    _inputs = None
    _hashinputs = None

    def __init__(self, reference=None):
        self._reference = reference
        self._inputs = {}

    def __str__(self):
        job_repr = f'{self.__shorthash__()},{self._reference}' if self._reference else f'{self.__shorthash__()}'
        return f'{self.__class__.__name__}({job_repr})'

    def __repr__(self):
        return str(self)

    def __hashcontent__(self):
        if self._hashinputs:
            inputs = self._hashinputs
        else:
            inputs = {k: deterministic_hash(v) for k, v in self._inputs.items()}
        return self._reference, tuple(list(sorted(inputs.items(), key=lambda i: i[0])))

    def __call__(self, **kwargs):
        raise NotImplementedError()

    def __getstate__(self):
        # Do not store other jobs recursively
        return {
            '_reference': self._reference,
            '_hashinputs': {
                k: deterministic_hash(v)
                for k, v in self._inputs.items()
            }
        }

    def __setstate__(self, state):
        self._reference = state['_reference']
        self._hashinputs = state['_hashinputs']

    def __getattr__(self, attr):
        if attr.startswith('_'):
            if attr in self.__dict__:
                return self.__dict__[attr]
            else:
                raise AttributeError(f'Invalid input/output name: {attr}')

        return ComputedResource((self, attr))

    def __setattr__(self, attr, value):
        if attr.startswith('_'):
            self.__dict__[attr] = value
            return

        if isinstance(value, (Resource, ResourcePool)):
            self._inputs[attr] = value
            return

        raise AttributeError(f'Invalid input type: {type(value)}. It must be a Resource or ResourcePool')

    @property
    def dependencies(self):
        return self._inputs.copy()


class PythonJob(Job):

    def __init__(self, function: Callable, reference=None):
        super().__init__(reference)
        self._function = function

    def __hashcontent__(self):
        return (
            super().__hashcontent__(),
            cloudpickle.dumps(self._function)
        )

    def __call__(self, **kwargs):
        return self._function(**kwargs)

    def __getstate__(self):
        return {
            **super().__getstate__(),
            '_function': self._function
        }

    def __setstate__(self, state):
        super().__setstate__(state)
        self._function = state['_function']


class ComputedResource(Job, Resource):

    def __init__(self, content):
        self._content = content
        self._inputs = {content[1]: content[0]}

    def __str__(self):
        return f'Computed({self._content[0].__str__()},{self._content[1]})'

    def __repr__(self):
        return f'Computed({self._content[0].__str__()},{self._content[1]},{self.__shorthash__()})'

    def __hashcontent__(self):
        if self._hashinputs:
            inputs = self._hashinputs
        else:
            inputs = {k: deterministic_hash(v) for k, v in self._inputs.items()}
        return self._reference, tuple(list(sorted(inputs.items(), key=lambda i: i[0])))

    def __call__(self, **state):
        return state[self._content[1]][self._content[1]]

    def __getstate__(self):
        # Do not store other jobs recursively
        return {
            '_reference': self._reference,
            '_hashinputs': {
                k: deterministic_hash(v)
                for k, v in self._inputs.items()
            }
        }

    def __setstate__(self, state):
        self._reference = state['_reference']
        self._hashinputs = state['_hashinputs']
        inputs = list(self._hashinputs.items())[0]
        self._content = (inputs[1], inputs[0])
