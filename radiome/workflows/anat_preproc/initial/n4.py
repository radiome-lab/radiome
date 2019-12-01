import nipype.interfaces.utility as util
import nipype.pipeline.engine as pe
from nipype.interfaces import ants
from voluptuous import Schema, Required, In, MultipleInvalid
from radiome.resource_pool import ResourcePool, Resource


def create_workflow() -> pe.Workflow:
    n4_workflow = pe.Workflow(name='n4')

    input_node = pe.Node(util.IdentityInterface(fields=['in_file']), name='input_spec')
    output_node = pe.Node(util.IdentityInterface(fields=['out_file']), name='output_spec')
    n4_node = pe.Node(interface=ants.N4BiasFieldCorrection(dimension=3, shrink_factor=2, copy_header=True),
                      name='anat_n4')

    n4_workflow.connect(input_node, 'in_file', n4_node, 'input_image')
    n4_workflow.connect(n4_node, 'output_image', output_node, 'out_file')

    return n4_workflow


config_schema = Schema({
    Required('already_skullstripped'): bool,
    Required('skullstrip_option'): In(['AFNI', 'BET', 'niworkflows-ants']),
    Required('n4_correction'): bool
})


def register_workflow(workflow: pe.Workflow, config: dict, resource_pool: ResourcePool):
    try:
        config_schema(config)
    except MultipleInvalid as e:
        raise ValueError(f'Invalid config: {e}')

    if config['already_skullstripped'] and config['skullstrip_option'] == 'niworkflows-ants':
        return

    if not config['n4_correction']:
        return

    resource_map = resource_pool.group_by(name='tag', key='anatomical')
    for resource_key, resource in resource_map.items():
        node = resource.workflow_node
        slot = resource.slot
        n4_workflow = create_workflow()
        workflow.connect(node, slot, n4_workflow, 'input_spec.in_file')
        resource_pool[resource_key] = Resource(n4_workflow, 'output_spec.out_file')
