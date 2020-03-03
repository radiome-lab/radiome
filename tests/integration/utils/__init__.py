import importlib
import sys
import types

from radiome.utils import mocks
import logging

logger = logging.getLogger(__name__)


class MockJob:
    name = 'radiome.execution.nipype'

    def __enter__(self):
        if self.name in sys.modules:
            del sys.modules[self.name]
        sys.modules[self.name] = types.ModuleType('MockNipype')
        sys.modules[self.name].__dict__['NipypeJob'] = mocks.NipypeJob

    def __exit__(self, exc_type, exc_val, exc_tb):
        del sys.modules[self.name]
        sys.modules[self.name] = importlib.import_module(self.name)
