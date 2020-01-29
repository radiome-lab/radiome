import cloudpickle
from radiome.resource_pool import Resource, ResourcePool
from radiome.utils import deterministic_hash, Hashable


class Job(Hashable):
    _reference = None
    _inputs = None
    _hashinputs = None

    _estimates = None

    def __init__(self, reference=None):
        self._reference = reference
        self._inputs = {}

        if not self._estimates:
            self._estimates = {
                'cpu': 1,
                'memory': 3,
                'storage': 5/1024,
            }

    def __str__(self):
        if self._reference:
            job_repr = f'{self.__shorthash__()},{self._reference}'
        else:
            job_repr = f'{self.__shorthash__()}'
        return f'{self.__class__.__name__}({job_repr})'

    def __repr__(self):
        return str(self)

    def __hashcontent__(self):
        if self._hashinputs:
            inputs = self._hashinputs
        else:
            inputs = {
                k: deterministic_hash(v)
                for k, v in self._inputs.items()
            }
        return (
            self._reference,
            tuple(list(sorted(inputs.items(), key=lambda i: i[0])))
        )

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

        return ComputedResource(job=self, field=attr)

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

    def __init__(self, function, reference=None):
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

    def __init__(self, job, field=None):
        self._job = job
        self._field = field
        self._content = (job, field)
        self._inputs = {'state': job}
        self._estimates = {
            'cpu': 1,
            'memory': .2,
            'storage': 5/1024,
        }

    def __str__(self):
        return f'Computed({self._job.__str__()},{self._field})'

    def __repr__(self):
        return f'Computed({self._job.__str__()},{self._field},{self.__shorthash__()})'

    def __hashcontent__(self):
        if self._hashinputs:
            inputs = self._hashinputs
        else:
            inputs = {k: deterministic_hash(v) for k, v in self._inputs.items()}
        return self._reference, tuple(list(sorted(inputs.items(), key=lambda i: i[0])))

    def __call__(self, state):
        if self._field:
            return state[self._field]
        return state

    def __getstate__(self):
        # Do not store other jobs recursively
        return {
            '_reference': self._reference,
            '_field': self._field,
            '_hashinputs': {
                k: deterministic_hash(v)
                for k, v in self._inputs.items()
            }
        }

    def __setstate__(self, state):
        self._reference = state['_reference']
        self._hashinputs = state['_hashinputs']
        self._field = state['_field']
        self._job = self._hashinputs['state']
        self._content = (self._job, self._field)
