from unittest import TestCase
from radiome.resource_pool import Resource, ResourceKey, ResourcePool
from radiome.workflows.workflow import Workflow, Job
from itertools import product

from radiome.workflows.anat import create_workflow


class TestWorkflow(TestCase):

    def test_initial(self):

        rp = ResourcePool()

        rp['sub-ULG001_T1w'] = '/Users/ash3454/Downloads/sub-ULG001_T1w.nii.gz'

        rp = create_workflow({}, rp)