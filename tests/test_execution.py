from unittest import TestCase
from radiome.resource_pool import ResourceKey as R, Resource, ResourcePool
from radiome.execution import ResourceSolver, Job, PythonJob
import radiome.workflows.anat as anat

import matplotlib.pyplot as plt
import networkx as nx


class TestExecution(TestCase):

    def test_initial(self):

        def basename(path):
            import os
            return {
                'path': os.path.basename(path),
                'dir': os.path.dirname(path),
            }

        def reversed(path):
            return {
                'reversed': path[::-1],
            }

        def subject_id(filename):
            return {
                'sub': filename.split('_')[0],
            }

        def join_path(dir, base):
            return {
                'path': f'{dir}/{base}'
            }

        rp = ResourcePool()

        A00008326_file = 's3://fcp-indi/data/Projects/RocklandSample/RawDataBIDSLatest/sub-A00008326/ses-BAS1/anat/sub-A00008326_ses-BAS1_T1w.nii.gz'
        A00008326_dir = 's3://fcp-indi/data/Projects/RocklandSample/RawDataBIDSLatest/sub-A00008326/ses-BAS1/anat'
        A00008326_base = 'sub-A00008326_ses-BAS1_T1w.nii.gz'

        A00008399_file = 's3://fcp-indi/data/Projects/RocklandSample/RawDataBIDSLatest/sub-A00008399/ses-BAS1/anat/sub-A00008399_ses-BAS1_T1w.nii.gz'
        A00008399_dir = 's3://fcp-indi/data/Projects/RocklandSample/RawDataBIDSLatest/sub-A00008399/ses-BAS1/anat'
        A00008399_base = 'sub-A00008399_ses-BAS1_T1w.nii.gz'

        rp['sub-A00008326_ses-BAS1_T1w'] = Resource(A00008326_file)
        rp['sub-A00008399_ses-BAS1_T1w'] = Resource(A00008399_file)

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
            

            filename_subject_id = PythonJob(function=subject_id)
            filename_subject_id.filename = file_basename.path
            srp[R('T1w', label='sub')] = filename_subject_id.sub


            file_join_path = PythonJob(function=join_path)
            file_join_path.dir = file_basename.dir
            file_join_path.base = file_reversed.reversed
            srp[R('T1w', label='crazypath')] = file_join_path.path


        G = ResourceSolver(rp).graph

        res_rp = ResourceSolver(rp).execute()

        self.assertIn(R('sub-A00008326_ses-BAS1_label-base_T1w'), res_rp)
        self.assertEqual(res_rp[R('sub-A00008326_ses-BAS1_label-base_T1w')].content, A00008326_base)
        self.assertEqual(res_rp[R('sub-A00008326_ses-BAS1_label-baserev_T1w')].content, A00008326_base[::-1])
        self.assertEqual(res_rp[R('sub-A00008326_ses-BAS1_label-sub_T1w')].content, 'sub-A00008326')
        self.assertEqual(res_rp[R('sub-A00008326_ses-BAS1_label-crazypath_T1w')].content, f'{A00008326_dir}/{A00008326_base[::-1]}')

        self.assertIn(R('sub-A00008399_ses-BAS1_label-base_T1w'), res_rp)
        self.assertEqual(res_rp[R('sub-A00008399_ses-BAS1_label-base_T1w')].content, A00008399_base)
        self.assertEqual(res_rp[R('sub-A00008399_ses-BAS1_label-baserev_T1w')].content, A00008399_base[::-1])
        self.assertEqual(res_rp[R('sub-A00008399_ses-BAS1_label-sub_T1w')].content, 'sub-A00008399')
        self.assertEqual(res_rp[R('sub-A00008399_ses-BAS1_label-crazypath_T1w')].content, f'{A00008399_dir}/{A00008399_base[::-1]}')
