from cerberus.validator import Validator
from nipype.interfaces import afni
from nipype.interfaces import ants

from radiome.execution.nipype import NipypeJob
from radiome.resource_pool import ResourcePool, ResourceKey as R
from .schema import schema


# TODO input validation by resouce metadata (variant, flags, type)
# TODO output validation by resouce metadata (variant, flags, type)
# TODO config schema validator
# TODO docstrings


def create_workflow(configuration, resource_pool: ResourcePool, context):
    validator = Validator(schema, allow_unknown=True, purge_unknown=True)
    if not validator.validate(configuration):
        raise ValueError(
            f'Invalid config file {",".join([str(key) + " " + str(val) for key, val in validator.errors.items()])}')

    for _, rp in resource_pool[['T1w']]:
        anatomical_image = rp[R('T1w')]

        anat_deoblique = NipypeJob(
            interface=afni.Refit(deoblique=True),
            reference='deoblique'
        )
        anat_deoblique.in_file = anatomical_image
        output_node = anat_deoblique.out_file

        if configuration['non_local_means_filtering']:
            denoise = NipypeJob(interface=ants.DenoiseImage())
            denoise.input_image = output_node
            output_node = denoise.output_image

        if configuration['n4_bias_field_correction']:
            n4 = NipypeJob(interface=ants.N4BiasFieldCorrection(dimension=3, shrink_factor=2, copy_header=True))
            n4.input_image = output_node
            output_node = n4.output_image

        anat_reorient = NipypeJob(
            interface=afni.Resample(orientation='RPI', outputtype='NIFTI_GZ'),
            reference='reorient'
        )
        # anat_reorient.in_file = n4.output_image
        anat_reorient.in_file = output_node
        rp[R('T1w', label='initial')] = anat_reorient.out_file.with_output_name('initial')

    return resource_pool
