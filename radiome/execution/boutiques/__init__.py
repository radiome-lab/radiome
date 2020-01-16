import copy

from radiome.resource_pool import Resource, ResourcePool
from radiome.execution.job import Job, ComputedResource


class BoutiquesJob(Job):

    def __init__(self, id: str, reference=None):
        super().__init__(reference=reference)
        self._id = id

    def __hashcontent__(self):
        return self._id.__class__, super().__hashcontent__()

    def __getattr__(self, attr):
        if attr.startswith('_') and attr in self.__dict__:
            return self.__dict__[attr]

        # TODO add schema validation based on boutiques metadata
        return ComputedResource((self, attr))

        raise AttributeError(f'Invalid input/output name: {attr}')

    def __setattr__(self, attr, value):
        if attr.startswith('_'):
            self.__dict__[attr] = value
            return

        # TODO add schema validation based on boutiques metadata
        if not isinstance(value, (Resource, ResourcePool)):
            value = Resource(value)

        self._inputs[attr] = value

    def __getstate__(self):
        return {
            **super().__getstate__(),
            '_id': self._id
        }

    def __setstate__(self, state):
        super().__setstate__(state)
        self._id = state['_id']

    def __call__(self, **kwargs):
        # TODO run boutiques