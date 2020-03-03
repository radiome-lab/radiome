import copy
import logging
import os
from pathlib import Path

from nipype.interfaces.base import File

from radiome.execution import Job, ComputedResource
from radiome.resource_pool import Resource, ResourcePool

logger = logging.getLogger(__name__)


class NipypeJob(Job):
    def __init__(self, interface, reference=None):
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

        # pick a file
        input_file = None
        for k, v in iface.inputs.get().items():
            if isinstance(iface.inputs.trait(k).trait_type, File):
                input_file = v
                break
        if input_file is None:
            input_file = os.path.abspath(__file__)

        # Return fake values from outputs
        res = iface.output_spec()
        return {
            k: (
                Path(input_file)
                if isinstance(res.trait(k).trait_type, File)
                else 'test'
            )
            for k, _ in res.get().items()
        }
