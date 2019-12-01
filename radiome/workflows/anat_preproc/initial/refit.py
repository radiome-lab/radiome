import nipype.interfaces.utility as util
import nipype.pipeline.engine as pe
from nipype.interfaces import afni
from radiome.resource_pool import ResourcePool, Resource


def create_workflow() -> pe.Workflow:
    refit_workflow = pe.Workflow(name='refit')
    input_node = pe.Node(util.IdentityInterface(fields=['in_file']), name='input_spec')
    output_node = pe.Node(util.IdentityInterface(fields=['out_file']), name='output_spec')

    anat_deoblique = pe.Node(interface=afni.Refit(), name='anat_deoblique')
    anat_deoblique.inputs.deoblique = True

    refit_workflow.connect(input_node, 'in_file', anat_deoblique, 'in_file')
    refit_workflow.connect(anat_deoblique, 'out_file', output_node, 'out_file')
    return refit_workflow


def register_workflow(workflow: pe.Workflow, c: dict, resource_pool: ResourcePool):
    resource_map = resource_pool.group_by(name='tag', key='anatomical')
    for resource_key, resource in resource_map.items():
        node = resource.workflow_node
        slot = resource.slot
        refit_workflow = create_workflow()
        workflow.connect(node, slot, refit_workflow, 'input_spec.in_file')
        resource_pool[resource_key] = Resource(refit_workflow, 'output_spec.out_file')
