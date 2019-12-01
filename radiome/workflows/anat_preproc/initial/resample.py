import nipype.interfaces.utility as util
import nipype.pipeline.engine as pe
from nipype.interfaces import afni
from radiome.resource_pool import ResourcePool, Resource


def create_workflow() -> pe.Workflow:
    resample_workflow = pe.Workflow(name='resample')

    input_node = pe.Node(util.IdentityInterface(fields=['in_file']), name='input_spec')
    output_node = pe.Node(util.IdentityInterface(fields=['out_file']), name='output_spec')
    anat_reorient_node = pe.Node(interface=afni.Resample(), name='anat_reorient')

    anat_reorient_node.inputs.orientation = 'RPI'
    anat_reorient_node.inputs.outputtype = 'NIFTI_GZ'

    resample_workflow.connect(input_node, 'in_file', anat_reorient_node, 'in_file')
    resample_workflow.connect(anat_reorient_node, 'out_file', output_node, 'out_file')

    return resample_workflow


def register_workflow(workflow: pe.Workflow, c: dict, resource_pool: ResourcePool):
    resource_map = resource_pool.group_by(name='tag', key='anatomical')
    for resource_key, resource in resource_map.items():
        node = resource.workflow_node
        slot = resource.slot
        resample_workflow = create_workflow()
        workflow.connect(node, slot, resample_workflow, 'input_spec.in_file')
        resource_pool[resource_key] = Resource(resample_workflow, 'output_spec.out_file')
