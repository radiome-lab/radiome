import unittest
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
from radiome.resource_pool import ResourcePool, Resource, ResourceKey, Strategy
from radiome.workflows.anat_preproc.initial import register_workflow as initial


class WorkflowTestCase(unittest.TestCase):
    def test_initial(self):
        input_node = pe.Node(util.IdentityInterface(
            fields=['anat', 'brain_mask']), name='inputspec')
        rp = ResourcePool()
        rp['sub-10021_space-mni_T1w'] = Resource(input_node, 'anat')
        workflow = pe.Workflow(name='global')
        config = {
            'already_skullstripped': False,
            'skullstrip_option': 'AFNI',
            'non_local_means_filtering': True,
            'n4_correction': True,
        }
        initial(workflow, config, rp)
        self.assertEqual(len(workflow.list_node_names()), 5)
        self.assertIn('anat_denoise', workflow.list_node_names())
        self.assertIn('anat_deoblique', workflow.list_node_names())
        self.assertIn('anat_n4', workflow.list_node_names())
        self.assertIn('anat_reorient', workflow.list_node_names())
        self.assertIn('inputspec', workflow.list_node_names())

        with self.assertRaises(ValueError):
            initial(workflow, {'already_skullstripped': 1, 'non_local_means_filtering': 1, 'n4_correction': 0}, rp)


if __name__ == '__main__':
    unittest.main()
