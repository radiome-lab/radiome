import nipype.interfaces.utility as util
import nipype.pipeline.engine as pe
from nipype.interfaces import ants
from voluptuous import Schema, Required, In, MultipleInvalid

from radiome.resource_pool import ResourcePool, Resource


def create_workflow() -> pe.Workflow:
    denoise_workflow = pe.Workflow(name='denoise')

    input_node = pe.Node(util.IdentityInterface(fields=['in_file']), name='input_spec')
    output_node = pe.Node(util.IdentityInterface(fields=['out_file']), name='output_spec')
    denoise_node = pe.Node(interface=ants.DenoiseImage(), name='anat_denoise')

    denoise_workflow.connect(input_node, 'in_file', denoise_node, 'input_image')
    denoise_workflow.connect(denoise_node, 'output_image', output_node, 'out_file')

    return denoise_workflow


config_schema = Schema({
    Required('already_skullstripped'): bool,
    Required('skullstrip_option'): In(['AFNI', 'BET', 'niworkflows-ants']),
    Required('non_local_means_filtering'): bool,
    Required('n4_correction'): bool
})


def register_workflow(workflow: pe.Workflow, config: dict, resource_pool: ResourcePool):
    try:
        config_schema(config)
    except MultipleInvalid as e:
        raise ValueError(f'Invalid config: {e}')

    if config['already_skullstripped'] and config['skullstrip_option'] == 'niworkflows-ants':
        return

    if not config['non_local_means_filtering']:
        return

    resource_map = resource_pool.group_by(name='tag', key='anatomical')
    for resource_key, resource in resource_map.items():
        node = resource.workflow_node
        slot = resource.slot
        denoise_workflow = create_workflow()
        workflow.connect(node, slot, denoise_workflow, 'input_spec.in_file')
        resource_pool[resource_key] = Resource(denoise_workflow, 'output_spec.out_file')
