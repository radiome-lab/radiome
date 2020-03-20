import copy
import importlib
import logging
import os
import sys
import tempfile
import types
from pathlib import Path

import yaml
from nipype.interfaces.base import File

from radiome.core import cli
from radiome.core.execution import Job, ComputedResource, pipeline
from radiome.core.resource_pool import Resource, ResourcePool

logger = logging.getLogger(__name__)


class NipypeJob(Job):
    """ Nipype jobs mock for testing.

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
    """ Context manager which replaces Nipype jobs with mock at runtime.

    Patch the nipype jobs with mocks at runtime, then recover it when exiting.
    """

    name = 'radiome.core.jobs'

    def __enter__(self):
        if self.name in sys.modules:
            del sys.modules[self.name]
        sys.modules[self.name] = types.ModuleType('MockNipype')
        sys.modules[self.name].__dict__['NipypeJob'] = NipypeJob

    def __exit__(self, exc_type, exc_val, exc_tb):
        del sys.modules[self.name]
        sys.modules[self.name] = importlib.import_module(self.name)


class Namespace(types.SimpleNamespace):
    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        else:
            return None


class WorkflowDriver:
    def __init__(self, module_path, inputs_dir, output_dir=None, working_dir=None, config=None,
                 participant_label=None,
                 aws_input_creds_path=None,
                 aws_input_creds_profile=None):
        args = Namespace(bids_dir=inputs_dir, outputs_dir=output_dir or tempfile.mkdtemp(),
                         working_dir=working_dir,
                         participant_label=participant_label,
                         aws_input_creds_path=aws_input_creds_path,
                         aws_input_creds_profile=aws_input_creds_profile)
        with tempfile.NamedTemporaryFile(suffix='.yml', mode='a+', delete=False) as tf:
            yaml.dump({'radiomeSchemaVersion': 1.0,
                       'class': 'pipeline',
                       'name': 'test',
                       'steps': [
                           {'step1': {
                               'run': module_path,
                               'in': config
                           }}
                       ]}, tf)
            tf.seek(0)
            args.config_file = tf.name

        self._args = args

    def run(self):
        return pipeline.build(cli.build_context(self._args))
