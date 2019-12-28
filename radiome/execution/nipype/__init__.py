from radiome.resource_pool import Resource, ResourcePool
from radiome.workflows.workflow import Job, ComputedResource

from nipype.interfaces.base import BaseInterface


class NipypeComputedResource(ComputedResource):

    def _field(self):
        return self._content[1]

    def _classname(self, qualified=True):
        iface_cls = self._content[0]._interface.__class__
        if qualified:
            return f'{iface_cls.__module__.replace("nipype.interfaces", "")}.{iface_cls.__name__}'
        return iface_cls.__name__

    def __str__(self):
        return f'Nipype({self._classname()}:{self._field()}, {self.__shorthash__()})'

    def __repr__(self):
        return f'NipypeComputedResource({self._classname()}:{self._field()}, {self.__hexhash__()})'


class NipypeJob(Job):

    def __init__(self, interface: BaseInterface):
        super().__init__()
        self._interface = interface

    def __getattr__(self, attr):
        if attr.startswith('_'):
            return self.__dict__[attr]

        if attr in self._interface.output_spec.class_visible_traits():
            return NipypeComputedResource((self, attr))

        raise KeyError(f'Invalid input/output name: {attr}')

    def __setattr__(self, attr, value):
        if attr.startswith('_'):
            self.__dict__[attr] = value
            return

        if attr not in self._interface.inputs.visible_traits():
            raise KeyError(f'Invalid input name: {attr}')

        if isinstance(value, (Resource, ResourcePool)):
            self._inputs[attr] = value
            return

        setattr(self._interface.inputs, attr, value)

    def __call__(self, **kwargs):
        iface = copy.deepcopy(self._interface)
        for k, v in kwargs.items():
            setattr(iface.inputs, k, v)
        res = iface.run()  # add error handling
        return res.outputs.get()
