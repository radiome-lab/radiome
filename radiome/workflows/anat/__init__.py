from radiome.resource_pool import ResourcePool, ResourceKey as R

from nipype.interfaces import afni
# from nipype.interfaces import ants

from radiome.execution.nipype import NipypeJob

# TODO input validation by resouce metadata (variant, flags, type)
# TODO output validation by resouce metadata (variant, flags, type)
# TODO config schema validator
# TODO docstrings

def create_workflow(configuration, resource_pool: ResourcePool):

    for _, rp in resource_pool[[
        R('T1w'),
    ]]:
        anatomical_image = rp[R('T1w')]

        anat_deoblique = NipypeJob(
            interface=afni.Refit(deoblique=True),
            reference='deoblique'
        )
        anat_deoblique.in_file = anatomical_image

        # denoise = NipypeJob(interface=ants.DenoiseImage())
        # denoise.input_image = anat_deoblique.out_file

        # n4 = NipypeJob(interface=ants.N4BiasFieldCorrection(dimension=3, shrink_factor=2, copy_header=True))
        # n4.input_image = denoise.output_image

        anat_reorient = NipypeJob(
            interface=afni.Resample(orientation='RPI', outputtype='NIFTI_GZ'),
            reference='reorient'
        )
        # anat_reorient.in_file = n4.output_image
        anat_reorient.in_file = anat_deoblique.out_file

        rp[R('T1w', label='initial')] = anat_reorient.out_file

    return resource_pool