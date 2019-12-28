from radiome.resource_pool import ResourcePool, ResourceKey as R

from nipype.interfaces import afni
from nipype.interfaces import ants
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util

from radiome.execution import Job
from radiome.execution.nipype import NipypeJob

# TODO input validation by resouce metadata (variant, flags, type)
# TODO output validation by resouce metadata (variant, flags, type)
# TODO config schema validator
# TODO docstrings

def create_workflow(configuration, resource_pool: ResourcePool):

    for strat, rp in resource_pool[[
        R('T1w'),
    ]]:
        anatomical_image = rp[R('T1w')]

        anat_deoblique = NipypeJob(interface=afni.Refit(deoblique=True))
        anat_deoblique.in_file = anatomical_image

        # denoise = NipypeJob(interface=ants.DenoiseImage())
        # denoise.input_image = anat_deoblique.out_file

        # n4 = NipypeJob(interface=ants.N4BiasFieldCorrection(dimension=3, shrink_factor=2, copy_header=True))
        # n4.input_image = denoise.output_image

        anat_reorient = NipypeJob(interface=afni.Resample(orientation='RPI', outputtype='NIFTI_GZ'))
        # anat_reorient.in_file = n4.output_image
        anat_reorient.in_file = anat_deoblique.out_file

        rp[R('T1w', label='initial')] = anat_reorient.out_file

        # Testing from here
        # anat_reorient_another = NipypeJob(interface=afni.Resample(orientation='RPI', outputtype='NIFTI_GZ'),
        #                           name='anat_reorient_another')
        # anat_reorient_another.in_file = n4.bias_image
        # rp[R('T1w', label='initial-another')] = anat_reorient_another.out_file

        # anat_reorient_bias = NipypeJob(interface=afni.Resample(orientation='RPI', outputtype='NIFTI_GZ'),
        #                           name='anat_reorient_bias')
        # anat_reorient_bias.in_file = n4.bias_image
        # rp[R('T1w', label='initial-bias')] = anat_reorient_bias.out_file

    return resource_pool