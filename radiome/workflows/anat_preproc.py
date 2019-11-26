from typing import Dict

import nipype.interfaces.utility as util
import nipype.pipeline.engine as pe
from nipype.interfaces import afni
from nipype.interfaces import ants
from voluptuous import Schema, Required, MultipleInvalid

from radiome import resource_pool


def create_refit_workflow() -> pe.Workflow:
    refit_workflow = pe.Workflow(name='refit')
    input_node = pe.Node(util.IdentityInterface(fields=['in_file']), name='input_spec')
    output_node = pe.Node(util.IdentityInterface(fields=['refit_output']), name='output_spec')

    anat_deoblique = pe.Node(interface=afni.Refit(), name='anat_deoblique')
    anat_deoblique.inputs.deoblique = True

    refit_workflow.connect(input_node, 'in_file', anat_deoblique, 'in_file')
    refit_workflow.connect(anat_deoblique, 'out_file', output_node, 'refit_output')
    return refit_workflow


def create_denoise_workflow() -> pe.Workflow:
    denoise_workflow = pe.Workflow(name='denoise')

    input_node = pe.Node(util.IdentityInterface(fields=['input_image']), name='input_spec')
    output_node = pe.Node(util.IdentityInterface(fields=['denoise_output']), name='output_spec')
    denoise_node = pe.Node(interface=ants.DenoiseImage(), name='anat_denoise')

    denoise_workflow.connect(input_node, 'input_image', denoise_node, 'input_image')
    denoise_workflow.connect(denoise_node, 'output_image', output_node, 'denoise_output')

    return denoise_workflow


def create_n4_workflow() -> pe.Workflow:
    n4_workflow = pe.Workflow(name='n4')

    input_node = pe.Node(util.IdentityInterface(fields=['input_image']), name='input_spec')
    output_node = pe.Node(util.IdentityInterface(fields=['n4_output']), name='output_spec')
    n4_node = pe.Node(interface=ants.N4BiasFieldCorrection(dimension=3, shrink_factor=2, copy_header=True),
                      name='anat_n4')

    n4_workflow.connect(input_node, 'input_image', n4_node, 'input_image')
    n4_workflow.connect(n4_node, 'output_image', output_node, 'n4_output')

    return n4_workflow


def create_resample_workflow() -> pe.Workflow:
    resample_workflow = pe.Workflow(name='resample')

    input_node = pe.Node(util.IdentityInterface(fields=['in_file']), name='input_spec')
    output_node = pe.Node(util.IdentityInterface(fields=['resample_output']), name='output_spec')
    anat_reorient_node = pe.Node(interface=afni.Resample(), name='anat_reorient')

    anat_reorient_node.inputs.orientation = 'RPI'
    anat_reorient_node.inputs.outputtype = 'NIFTI_GZ'

    resample_workflow.connect(input_node, 'in_file', anat_reorient_node, 'in_file')
    resample_workflow.connect(anat_reorient_node, 'out_file', output_node, 'resample_output')

    return resample_workflow


config_schema = Schema({
    Required('n4'): bool,
    Required('denoise'): bool
})


def create_workflow(workflow: pe.Workflow, config: Dict, resource: resource_pool) -> pe.Workflow:
    try:
        config_schema(config)
    except MultipleInvalid as e:
        raise ValueError(f'Wrong config file: {e}')

    wf = pe.Workflow(name='anat_preproc')
    input_node = pe.Node(util.IdentityInterface(fields=['anat', 'brain_mask']), name='input_spec')
    output_node = pe.Node(util.IdentityInterface(fields=['refit', 'reorient']), name='output_spec')

    refit_workflow = create_refit_workflow()
    wf.connect(input_node, 'anat', refit_workflow, 'input_spec.in_file')
    wf.connect(refit_workflow, 'output_spec.refit_output', output_node, 'refit')

    denoise_workflow = create_denoise_workflow()
    n4_workflow = create_n4_workflow()
    resample_workflow = create_resample_workflow()

    use_denoise = config['denoise']
    use_n4 = config['n4']

    if use_denoise and use_n4:
        wf.connect(refit_workflow, 'output_spec.refit_output', denoise_workflow, 'input_spec.input_image')
        wf.connect(denoise_workflow, 'output_spec.denoise_output', n4_workflow, 'input_spec.input_image')
        wf.connect(n4_workflow, 'output_spec.n4_output', resample_workflow, 'input_spec.in_file')
    elif use_denoise and not use_n4:
        wf.connect(refit_workflow, 'output_spec.refit_output', denoise_workflow, 'input_spec.input_image')
        wf.connect(denoise_workflow, 'output_spec.denoise_output', resample_workflow, 'input_spec.in_file')
    elif use_n4 and not use_denoise:
        wf.connect(refit_workflow, 'output_spec.refit_output', n4_workflow, 'input_spec.input_image')
        wf.connect(n4_workflow, 'output_spec.n4_output', resample_workflow, 'input_spec.in_file')
    else:
        wf.connect(refit_workflow, 'output_spec.refit_output', resample_workflow, 'input_spec.in_file')

    wf.connect(resample_workflow, 'output_spec.resample_output', output_node, 'reorient')

    return wf
