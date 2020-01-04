from unittest import TestCase
from radiome.resource_pool import ResourceKey as R, Resource, ResourcePool
from radiome.execution import DependencySolver
from radiome.execution.executor import Execution, DaskExecution
from radiome.execution.job import PythonJob

from .helpers import StateProfiler


import logging
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)

def basename(path):
    import os
    return {
        'path': os.path.basename(path),
        'dirname': os.path.dirname(path),
    }

def reversed_string(path):
    return {
        'reversed': str(path[::-1]),
    }

def subject_id(filename):
    return {
        'sub': filename.split('_')[0],
    }

def join_path(dirname, base):
    return {
        'path': f'{dirname}/{base}'
    }

def timestamp(delay):
    import time
    time.sleep(delay)

    return {
        'time': time.time()
    }

A00008326_file = 's3://fcp-indi/data/Projects/RocklandSample/RawDataBIDSLatest/sub-A00008326/ses-BAS1/anat/sub-A00008326_ses-BAS1_T1w.nii.gz'
A00008326_dir = 's3://fcp-indi/data/Projects/RocklandSample/RawDataBIDSLatest/sub-A00008326/ses-BAS1/anat'
A00008326_base = 'sub-A00008326_ses-BAS1_T1w.nii.gz'

A00008399_file = 's3://fcp-indi/data/Projects/RocklandSample/RawDataBIDSLatest/sub-A00008399/ses-BAS1/anat/sub-A00008399_ses-BAS1_T1w.nii.gz'
A00008399_dir = 's3://fcp-indi/data/Projects/RocklandSample/RawDataBIDSLatest/sub-A00008399/ses-BAS1/anat'
A00008399_base = 'sub-A00008399_ses-BAS1_T1w.nii.gz'


class TestExecution(TestCase):

    def setUp(self):
        self.rp = ResourcePool()
        self.rp['sub-A00008326_ses-BAS1_T1w'] = Resource(A00008326_file)
        self.rp['sub-A00008399_ses-BAS1_T1w'] = Resource(A00008399_file)

    def test_initial(self):

        for strat, srp in self.rp[[
            R('T1w'),
        ]]:
            anatomical_image = srp[R('T1w')]

            file_basename = PythonJob(function=basename)
            file_basename.path = anatomical_image
            srp[R('T1w', label='base')] = file_basename.path
            srp[R('T1w', label='dir')] = file_basename.dirname


            file_reversed = PythonJob(function=reversed_string)
            file_reversed.path = file_basename.path
            srp[R('T1w', label='baserev')] = file_reversed.reversed


            filename_subject_id = PythonJob(function=subject_id)
            filename_subject_id.filename = file_basename.path
            srp[R('T1w', label='sub')] = filename_subject_id.sub


            file_join_path = PythonJob(function=join_path)
            file_join_path.dirname = file_basename.dirname
            file_join_path.base = file_reversed.reversed
            srp[R('T1w', label='crazypath')] = file_join_path.path

        for executor in [Execution, DaskExecution]:

            res_rp = DependencySolver(self.rp).execute(executor=executor())

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

    def test_intermediary(self):

        for strat, srp in self.rp[[
            R('T1w'),
        ]]:
            anatomical_image = srp[R('T1w')]

            file_basename = PythonJob(function=basename)
            file_basename.path = anatomical_image
            srp[R('T1w', label='base')] = file_basename.path
            srp[R('T1w', label='dir')] = file_basename.dirname

            file_reversed = PythonJob(function=reversed_string)
            file_reversed.path = file_basename.path

            filename_subject_id = PythonJob(function=subject_id)
            filename_subject_id.filename = file_basename.path

            file_join_path = PythonJob(function=join_path)
            file_join_path.dirname = file_basename.dirname
            file_join_path.base = file_reversed.reversed
            srp[R('T1w', label='crazypath')] = file_join_path.path

        # Create footprint for file_reversed, filename_subject_id and file_join_path
        # Since file_join_path is cached, file_reversed and filename_subject_id should not execute
        #
        # * Requires a ExecutionLogger
        # * Maybe this policy could be parametrized

        res_rp = DependencySolver(self.rp).execute(executor=Execution())

        self.assertIn(R('sub-A00008326_ses-BAS1_label-base_T1w'), res_rp)
        self.assertEqual(res_rp[R('sub-A00008326_ses-BAS1_label-crazypath_T1w')].content, f'{A00008326_dir}/{A00008326_base[::-1]}')

        self.assertIn(R('sub-A00008399_ses-BAS1_label-base_T1w'), res_rp)
        self.assertEqual(res_rp[R('sub-A00008399_ses-BAS1_label-crazypath_T1w')].content, f'{A00008399_dir}/{A00008399_base[::-1]}')

    def test_parallel(self):

        wait = 3

        delayed1 = PythonJob(function=timestamp, reference='time1')
        delayed1.delay = Resource(wait)
        self.rp[R('T1w', label='time1')] = delayed1.time

        delayed2 = PythonJob(function=timestamp, reference='time2')
        delayed2.delay = Resource(wait)
        self.rp[R('T1w', label='time2')] = delayed2.time


        res_rp = DependencySolver(self.rp).execute(executor=DaskExecution())

        self.assertIn(R('label-time1_T1w'), res_rp)
        self.assertIn(R('label-time2_T1w'), res_rp)

        time1 = res_rp[R('label-time1_T1w')].content
        time2 = res_rp[R('label-time2_T1w')].content

        # To ensure parallelism, both tasks should be run 'at the same time'
        #  so the difference between their finish time execution will be
        #  lesser than the time each one took to compute
        self.assertLess(time1 - time2, wait)


        res_rp = DependencySolver(self.rp).execute(executor=Execution())

        self.assertIn(R('label-time1_T1w'), res_rp)
        self.assertIn(R('label-time2_T1w'), res_rp)

        time1 = res_rp[R('label-time1_T1w')].content
        time2 = res_rp[R('label-time2_T1w')].content

        self.assertGreaterEqual(abs(time1 - time2), wait)
