from nipype.interfaces import afni

from radiome.core import workflow, AttrDict, Context, ResourceKey as R, ResourcePool
from radiome.core.jobs import NipypeJob


@workflow()
def create_workflow(config: AttrDict, resource_pool: ResourcePool, context: Context):
    for _, rp in resource_pool[['T1w']]:
        anat_image = rp[R('T1w')]
        anat_deoblique = NipypeJob(
            interface=afni.Refit(deoblique=True),
            reference='deoblique'
        )
        anat_deoblique.in_file = anat_image
        output_node = anat_deoblique.out_file

        anat_reorient = NipypeJob(
            interface=afni.Resample(orientation='RPI', outputtype='NIFTI_GZ'),
            reference='reorient'
        )
        anat_reorient.in_file = output_node
        rp[R('T1w', label='reorient')] = anat_reorient.out_file
