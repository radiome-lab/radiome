import copy
import importlib
import logging
import os
import sys
import types
from pathlib import Path

from nipype.interfaces.base import File

from radiome.core.execution import Job, ComputedResource
from radiome.core.resource_pool import Resource, ResourcePool

logger = logging.getLogger(__name__)


class NipypeJob(Job):
    """ Nipype job mock for testing.

    Mock that emulates the behavior and APIs of NipypeJob, but do not execute the commandline of nipype jobs.
    It will create fake outputs based on the outputs traits.

    """

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

        logger.info(iface.cmdline)

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


class mock_nipype:
    """ Context manager which replaces Nipype job with mock at runtime.

    Patch the nipype job with mocks at runtime, then recover it when exiting.
    """

    name = 'radiome.execution.nipype'

    def __enter__(self):
        if self.name in sys.modules:
            del sys.modules[self.name]
        sys.modules[self.name] = types.ModuleType('MockNipype')
        sys.modules[self.name].__dict__['NipypeJob'] = NipypeJob

    def __exit__(self, exc_type, exc_val, exc_tb):
        del sys.modules[self.name]
        sys.modules[self.name] = importlib.import_module(self.name)
