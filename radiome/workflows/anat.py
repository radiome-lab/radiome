from ..resource_pool import ResourcePool, ResourceKey

from nipype.interfaces import afni
from nipype.interfaces import ants
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util

from radiome.workflows.workflow import Job
from radiome.workflows.nipype import NipypeJob

# TODO input validation by resouce metadata (variant, flags, type)
# TODO output validation by resouce metadata (variant, flags, type)
# TODO config schema validator
# TODO docstrings

def create_workflow(configuration, resource_pool: ResourcePool):

    for strat, rp in resource_pool[[
        ResourceKey('T1w'),
    ]]:
        anatomical_image = rp[ResourceKey('T1w')]

        anat_deoblique = NipypeJob(interface=afni.Refit(deoblique=True), name='anat_deoblique')
        anat_deoblique.in_file = anatomical_image

        denoise = NipypeJob(interface=ants.DenoiseImage(), name='anat_denoise')
        denoise.input_image = anat_deoblique.out_file

        n4 = NipypeJob(interface=ants.N4BiasFieldCorrection(dimension=3, shrink_factor=2, copy_header=True),
                       name='anat_n4')
        n4.input_image = denoise.output_image

        anat_reorient = NipypeJob(interface=afni.Resample(orientation='RPI', outputtype='NIFTI_GZ'),
                                  name='anat_reorient')
        
        rp[ResourceKey('T1w', desc='initial-T1')] = anat_reorient.out_file

    return resource_pool