import nipype.interfaces.utility as util
import nipype.pipeline.engine as pe
from nipype.interfaces import afni
from nipype.interfaces import ants

from radiome import resource_pool


def create_refit_workflow() -> pe.Workflow:
    refit_workflow = pe.Workflow(name='refit')
    input_node = pe.Node(util.IdentityInterface(fields=['anat', 'brain_mask']), name='input_spec')
    output_node = pe.Node(util.IdentityInterface(fields=['refit_output']), name='output_spec')

    anat_deoblique = pe.Node(interface=afni.Refit(), name='anat_deoblique')
    anat_deoblique.inputs.deoblique = True

    refit_workflow.connect(input_node, 'anat', anat_deoblique, 'in_file')
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

    output_node = pe.Node(util.IdentityInterface(fields=['resample_output']), name='output_spec')
    anat_reorient_node = pe.Node(interface=afni.Resample(), name='anat_reorient')

    anat_reorient_node.inputs.orientation = 'RPI'
    anat_reorient_node.inputs.outputtype = 'NIFTI_GZ'

    resample_workflow.connect(anat_reorient_node, 'out_file', output_node, 'resample_output')

    return resample_workflow


def create_workflow(workflow, config, resource: resource_pool):
    pass
