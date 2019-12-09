from typing import Tuple

import nipype.pipeline.engine as pe
from nipype.interfaces import afni, ants
from voluptuous import Schema, In, MultipleInvalid

from radiome.resource_pool import ResourcePool, Resource, ResourceKey


def register_refit(workflow: pe.Workflow, input_node: pe.Node, input_name: str) -> Tuple[pe.Node, str]:
    anat_deoblique = pe.Node(interface=afni.Refit(), name='anat_deoblique')
    anat_deoblique.inputs.deoblique = True
    workflow.connect(input_node, input_name, anat_deoblique, 'in_file')
    return anat_deoblique, 'out_file'


def register_denoise(workflow: pe.Workflow, input_node: pe.Node, input_name: str) -> Tuple[pe.Node, str]:
    denoise_node = pe.Node(interface=ants.DenoiseImage(), name='anat_denoise')
    workflow.connect(input_node, input_name, denoise_node, 'input_image')
    return denoise_node, 'output_image'


def register_n4(workflow: pe.Workflow, input_node: pe.Node, input_name: str) -> Tuple[pe.Node, str]:
    n4_node = pe.Node(interface=ants.N4BiasFieldCorrection(dimension=3, shrink_factor=2, copy_header=True),
                      name='anat_n4')
    workflow.connect(input_node, input_name, n4_node, 'input_image')
    return n4_node, 'output_image'


def register_resample(workflow: pe.Workflow, input_node: pe.Node, input_name: str) -> Tuple[pe.Node, str]:
    anat_reorient_node = pe.Node(interface=afni.Resample(), name='anat_reorient')
    anat_reorient_node.inputs.orientation = 'RPI'
    anat_reorient_node.inputs.outputtype = 'NIFTI_GZ'
    workflow.connect(input_node, input_name, anat_reorient_node, 'in_file')
    return anat_reorient_node, 'out_file'


config_schema = Schema({
    'already_skullstripped': bool,
    'skullstrip_option': In(['AFNI', 'BET', 'niworkflows-ants']),
    'non_local_means_filtering': bool,
    'n4_correction': bool,
})


def register_workflow(workflow: pe.Workflow, config: dict, resource_pool: ResourcePool):
    try:
        config_schema(config)
    except MultipleInvalid as e:
        raise ValueError(f'Invalid config: {e}')

    anat_resource = resource_pool['T1w']
    generated_resources = {}

    for resource_key, resource in anat_resource.items():
        if resource_key not in resource_pool['refit'] and resource_key not in resource_pool['reorient']:
            workflow_node = resource.workflow_node
            slot = resource.slot

            output_node, output_name = register_refit(workflow, workflow_node, slot)
            generated_resources[ResourceKey(str(resource_key), {'refit'})] = Resource(output_node, output_name)

            skip_denoise_n4 = 'already_skullstripped' in config and not config['already_skullstripped'] and config[
                'skullstrip_option'] == 'niworkflows-ants'

            if not skip_denoise_n4:
                if 'non_local_means_filtering' in config and config['non_local_means_filtering']:
                    output_node, output_name = register_denoise(workflow, output_node, output_name)

                if 'n4_correction' in config and config['n4_correction']:
                    output_node, output_name = register_n4(workflow, output_node, output_name)

            output_node, output_name = register_resample(workflow, output_node, output_name)
            generated_resources[ResourceKey(str(resource_key), {'reorient'})] = Resource(output_node, output_name)

    # TODO how to add new resource
    # for resource_key, resource in generated_resources.items():
        # resource_pool[resource_key] = resource
