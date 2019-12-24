from radiome.resource_pool import Resource, ComputedResource, ResourcePool
from radiome.workflows.workflow import Job


class NipypeComputedResource(ComputedResource):
    pass


class NipypeJob(Job):
    
    def __init__(self, name, interface):
        super().__init__(name=name)
        self._interface = interface

    def __getattr__(self, attr):
        if attr in ['_name', '_inputs', '_interface']:
            return self.__dict__[attr]

        if attr in self._interface.inputs.visible_traits():
            if attr not in self._inputs:
                return getattr(self._interface.inputs, attr)
            return NipypeComputedResource(None, (self, attr))

        if attr in self._interface.output_spec.class_visible_traits():
            return NipypeComputedResource(None, (self, attr))

        raise KeyError(f'Invalid input/output name: {attr}')

    def __setattr__(self, attr, value):

        if attr in ['_name', '_inputs', '_interface']:
            self.__dict__[attr] = value
            return

        if attr not in self._interface.inputs.visible_traits():
            raise KeyError(f'Invalid input name: {attr}')

        if isinstance(value, ResourcePool):
            self._inputs[attr] = value
            return

        if isinstance(value, Resource):
            self._inputs[attr] = value
            return

        setattr(self._interface.inputs, attr, value)