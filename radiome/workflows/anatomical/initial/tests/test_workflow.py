from unittest import TestCase

import os
import s3fs
import time
import tempfile
import shutil
import nibabel as nb

from radiome.resource_pool import R, Resource, ResourcePool
from radiome.workflows.anatomical.initial import create_workflow
from radiome.execution import DependencySolver
from radiome.execution.executor import executors
from radiome.execution.state import FileState

from radiome.tests.case import TestWorkflowCase


class TestWorkflow(TestWorkflowCase):

    def setUpData(self):
        self.subs = [
            's3://fcp-indi/data/Projects/RocklandSample/RawDataBIDSLatest/sub-A00008326/ses-BAS1/anat/sub-A00008326_ses-BAS1_T1w.nii.gz',
            's3://fcp-indi/data/Projects/RocklandSample/RawDataBIDSLatest/sub-A00008399/ses-BAS1/anat/sub-A00008399_ses-BAS1_T1w.nii.gz',
        ]

        s3 = s3fs.S3FileSystem(anon=True)
        for i, s in enumerate(self.subs):
            local = os.path.join(self.scratch, os.path.basename(s))
            s3.get(s, os.path.join(self.scratch, os.path.basename(s)))
            self.subs[i] = local

        for s in self.subs:
            self.assertTrue(os.path.exists(s))

    def test_workflow1(self):

        timing = {}

        for executor in executors:

            rp = ResourcePool()

            for s in self.subs:
                rp[os.path.basename(s).split('.', 1)[0]] = Resource(s)

            create_workflow({}, rp)

            state = FileState(scratch=f'{self.scratch}/{executor.__name__}')

            start_time = time.time()
            res_rp = DependencySolver(rp).execute(executor=executor(), state=state)
            elapsed_time = time.time() - start_time

            timing[executor] = elapsed_time

            for sub in [
                'A00008326',
                'A00008399',
            ]:

                self.assertIn(R(f'sub-{sub}_ses-BAS1_label-initial_T1w'), res_rp)

                self.assertEqual(
                    nb.load(res_rp[R(f'sub-{sub}_ses-BAS1_T1w')]()).shape,
                    nb.load(res_rp[R(f'sub-{sub}_ses-BAS1_label-initial_T1w')]()).shape
                )
