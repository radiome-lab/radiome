import os
import shutil
import tempfile
from unittest import TestCase


class TestWorkflowCase(TestCase):

    def setUp(self):
        self.old_dir = os.getcwd()
        self.scratch = tempfile.mkdtemp(prefix='rdm.')
        os.chdir(self.scratch)

        self.setUpData()

    def setUpData(self):
        pass

    def tearDown(self):
        shutil.rmtree(self.scratch)
        os.chdir(self.old_dir)
