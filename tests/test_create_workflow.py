from unittest import TestCase

from radiome.workflows import anat_preproc
import nipype.pipeline.engine as pe


class TestCreateWorkflow(TestCase):
    def test_create_workflow(self):
        wf = pe.Workflow(name='mock')
        self.assertTrue(anat_preproc.create_workflow(wf, {'n4': True, 'denoise': True}, {}))
        self.assertTrue(anat_preproc.create_workflow(wf, {'n4': True, 'denoise': False}, {}))
        self.assertTrue(anat_preproc.create_workflow(wf, {'n4': False, 'denoise': True}, {}))
        self.assertTrue(anat_preproc.create_workflow(wf, {'n4': False, 'denoise': False}, {}))

        # test invalid config
        with self.assertRaises(ValueError):
            anat_preproc.create_workflow(wf, {'n4': 'True', 'denoise': 'True'}, {})
