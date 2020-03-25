import copy
import logging
from pathlib import Path

import cloudpickle
from nipype.interfaces.base import File, BaseInterface, Undefined

from radiome.core.resource_pool import Resource, ResourcePool
from radiome.core.utils import Hashable

logger = logging.getLogger('radiome.execution.jobs')


class Job(Hashable):
    _reference = None
    _inputs = None

    _estimates = None

    def __init__(self, reference=None):
        self._reference = reference
        self._inputs = {}

        if not self._estimates:
            self._estimates = {
                'cpu': 1,
                'memory': 3,
                'storage': 5 / 1024,
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
        inputs = {
            k: FakeJob(v) if isinstance(v, Job) else v
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
            '_inputs': {
                k: FakeJob(v) if isinstance(v, Job) else v
                for k, v in self._inputs.items()
            },
            '_estimates': self._estimates,
            '_hash': self._hash,
        }

    def __setstate__(self, state):
        self._reference = state['_reference']
        self._inputs = state['_inputs']
        self._estimates = state['_estimates']
        self._hash = state['_hash']

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
            self._hash = None
            return

        raise AttributeError(f'Invalid input type: {type(value)}. It must be a Resource or ResourcePool')

    def dependencies(self):
        return self._inputs.copy()

    def resources(self):
        return self._estimates.copy()


class FakeJob(Job):
    def __init__(self, job):
        super().__init__(job._reference)
        self._hash = job.__longhash__()
        self._repr = job.__repr__()
        self._str = job.__str__()

    def __longhash__(self):
        return self._hash

    def __str__(self):
        return self._str

    def __repr__(self):
        return self._repr

    def __getstate__(self):
        return {
            '_reference': self._reference,
            '_hash': self._hash,
            '_repr': self._repr,
            '_str': self._str,
        }

    def __setstate__(self, state):
        self._reference = state['_reference']
        self._hash = state['_hash']
        self._repr = state['_repr']
        self._str = state['_str']


class PythonJob(Job):
    """  Radiome job for Python functions.

    This job is to set up Python function in the steps of a workflow. Inputs of function should be
    set using attributes. Python functions must return a dict, which is mapping from names to values.

    """
    _function = None

    def __init__(self, function, reference=None):
        """
        Create a Python job.

        Args:
            function: Python function be to executed.
            reference: Name for the job.
        """
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
    """  Represents the future result from a job, but not the true result.

    ComputedResource stores information that is needed to compute the result, but not the result itself.
    It can be used as inputs of other jobs and thus create a connection between jobs.

    """
    _bids_name = None

    def __init__(self, job, field=None):
        self._job = job
        self._field = field
        self._content = (job, field)
        self._inputs = {'state': job}
        self._bids_name = self._bids_name or 'unnamed'

        self._estimates = {
            'cpu': 1,
            'memory': .2,
            'storage': 5 / 1024,
        }

    def __str__(self):
        job = self._job.__str__()
        return f'Computed({job},{self._field})'

    def __repr__(self):
        job = self._job.__repr__()
        return f'Computed({job},{self._field},{self.__shorthash__()})'

    def __hashcontent__(self):
        return self._reference, self._job, self._field

    def __call__(self, state):
        if self._field:
            return state[self._field]
        return state

    def __getstate__(self):
        # Do not store other jobs recursively
        return {
            '_reference': self._reference,
            '_field': self._field,
            '_job': FakeJob(self._job),
            '_estimates': self._estimates,
        }

    def __setstate__(self, state):
        self._estimates = state['_estimates']
        self._reference = state['_reference']
        self._field = state['_field']
        self._job = state['_job']
        self._content = (self._job, self._field)
        self._inputs = {'state': self._job}

    @property
    def bids_name(self):
        return self._bids_name


class NipypeJob(Job):
    """  Radiome job for nipype interfaces,

    NipypeJob is a uniform wrapper for all nipype interfaces such that nipype interfaces
    can receive results from or become inputs of other jobs.

    """

    def __init__(self, interface: BaseInterface, reference=None):
        super().__init__(reference=reference)
        self._interface = copy.deepcopy(interface)

    def __hashcontent__(self):
        return self._interface.__class__, super().__hashcontent__()

    def __getattr__(self, attr):
        if attr.startswith('_') and attr in self.__dict__:
            return self.__dict__[attr]

        if attr in self._interface.output_spec.class_visible_traits():
            return ComputedResource(job=self, field=attr)

        raise AttributeError(f'Invalid input/output name: {attr}')

    def __setattr__(self, attr, value):
        if attr.startswith('_'):
            self.__dict__[attr] = value
            return

        if attr not in self._interface.inputs.visible_traits():
            raise AttributeError(f'Invalid input name: {attr}')

        if not isinstance(value, (Resource, ResourcePool)):
            value = Resource(value)
        self._inputs[attr] = value

    def __getstate__(self):
        return {
            **super().__getstate__(),
            '_interface': self._interface
        }

    def __setstate__(self, state):
        super().__setstate__(state)
        self._interface = state['_interface']

    def __call__(self, **kwargs):
        iface = self._interface
        for k, v in kwargs.items():
            setattr(iface.inputs, k, v)

        res = iface.run()  # add error handling
        return {
            k: (
                Path(v)
                if isinstance(res.outputs.trait(k).trait_type, File) and v is not Undefined
                else v
            )
            for k, v in res.outputs.get().items()
        }
