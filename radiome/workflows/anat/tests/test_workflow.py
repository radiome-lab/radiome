from unittest import TestCase

import os
import s3fs
import tempfile
import shutil

from radiome.resource_pool import R, Resource, ResourcePool
from radiome.workflows.anat import create_workflow
from radiome.execution import ResourceSolver, Execution


class TestWorkflow(TestCase):

    def setUp(self):

        self.scratch = tempfile.mkdtemp()

        self.subs = [
            's3://fcp-indi/data/Projects/RocklandSample/RawDataBIDSLatest/sub-A00008326/ses-BAS1/anat/sub-A00008326_ses-BAS1_T1w.nii.gz',
            's3://fcp-indi/data/Projects/RocklandSample/RawDataBIDSLatest/sub-A00008399/ses-BAS1/anat/sub-A00008399_ses-BAS1_T1w.nii.gz',
        ]

        s3 = s3fs.S3FileSystem(anon=True)
        for i, s in enumerate(self.subs):
            local = os.path.join(self.scratch, os.path.basename(s))
            s3.get(s, os.path.join(self.scratch, os.path.basename(s)))
            self.subs[i] = local

    def test_workflow1(self):

        rp = ResourcePool()

        for s in self.subs:
            rp[os.path.basename(s).split('.', 1)[0]] = Resource(s)

        create_workflow({}, rp)

        exec = Execution(caching=self.scratch)
        res_rp = ResourceSolver(rp).execute()
        
        self.assertIn(R('sub-A00008326_ses-BAS1_label-initial_T1w'), res_rp)

    def tearDown(self):
        shutil.rmtree(self.scratch)