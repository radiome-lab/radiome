import os
import unittest
from unittest import mock

from nipype.interfaces import afni
from radiome.core.resource_pool import ResourceKey
from radiome.core.utils.mocks import mock_nipype, Namespace, WorkflowDriver
from .helpers import data_path


class MockTestCase(unittest.TestCase):
    @mock.patch.dict(os.environ, {'PATH': ''})
    def test_mock_nipype(self):
        with mock_nipype():
            from radiome.core.jobs import NipypeJob
            job = NipypeJob(
                interface=afni.Refit(deoblique=True),
                reference='deoblique'
            )
            in_file = data_path(__file__, 'mocks/sub-0050682_T1w.nii.gz')
            res = job(in_file=in_file)
            self.assertEqual(str(res['out_file']), in_file)

    def test_namespace(self):
        ns = Namespace(a='b')
        self.assertIsNone(ns.b)
        self.assertEqual(ns.a, 'b')

    def test_workflow_driver(self):
        wf = WorkflowDriver(data_path(__file__, 'fake_workflow'), data_path(__file__, 'mocks'))
        res_rp = wf.run(config={'msg': 'mocks!'})
        self.assertEqual(res_rp[ResourceKey('T1w')].content, 'mocks!')


if __name__ == '__main__':
    unittest.main()
