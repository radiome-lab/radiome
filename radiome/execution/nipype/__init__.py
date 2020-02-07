import copy

from radiome.resource_pool import Resource, ResourcePool
from radiome.execution.job import Job, ComputedResource

from nipype.interfaces.base import BaseInterface
from nipype.interfaces.base.traits_extension import File

from pathlib import Path


class NipypeJob(Job):

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
                if isinstance(res.outputs.trait('out_file').trait_type, File)
                else v
            )
            for k, v in res.outputs.get().items()
        }
