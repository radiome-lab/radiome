from unittest import TestCase
from radiome.resource_pool import ResourceKey as R, Resource, ResourcePool
from radiome.execution import ResourceSolver, Job, PythonJob
import radiome.workflows.anat as anat

import matplotlib.pyplot as plt
import networkx as nx


class TestExecution(TestCase):

    def test_initial(self):

        def reversed(path):
            return {
                'reversed': path[::-1],
            }

        def basename(path):
            import os
            return {
                'path': os.path.basename(path),
                'dir': os.path.dirname(path),
            }

        rp = ResourcePool()

        rp['sub-A00008326_ses-BAS1_T1w'] = Resource('s3://fcp-indi/data/Projects/RocklandSample/RawDataBIDSLatest/sub-A00008326/ses-BAS1/anat/sub-A00008326_ses-BAS1_T1w.nii.gz')
        rp['sub-A00008399_ses-BAS1_T1w'] = Resource('s3://fcp-indi/data/Projects/RocklandSample/RawDataBIDSLatest/sub-A00008399/ses-BAS1/anat/sub-A00008399_ses-BAS1_T1w.nii.gz')

        for strat, srp in rp[[
            R('T1w'),
        ]]:
            anatomical_image = srp[R('T1w')]

            file_basename = PythonJob(function=basename)
            file_basename.path = anatomical_image

            srp[R('T1w', label='base')] = file_basename.path
            srp[R('T1w', label='dir')] = file_basename.dir

            file_reversed = PythonJob(function=reversed)
            file_reversed.path = file_basename.path

            srp[R('T1w', label='baserev')] = file_reversed.reversed

        self.assertIn(R('sub-A00008326_ses-BAS1_label-base_T1w'), rp)

        G = ResourceSolver(rp).graph

        res_rp = ResourceSolver(rp).execute()

        self.assertIn(R('sub-A00008326_ses-BAS1_label-base_T1w'), res_rp)
        self.assertEqual(res_rp[R('sub-A00008326_ses-BAS1_label-base_T1w')].content, 'sub-A00008326_ses-BAS1_T1w.nii.gz')
        self.assertEqual(res_rp[R('sub-A00008326_ses-BAS1_label-baserev_T1w')].content, 'sub-A00008326_ses-BAS1_T1w.nii.gz'[::-1])
