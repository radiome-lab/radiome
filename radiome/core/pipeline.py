import functools
import logging
import os
import shutil

from radiome.core import schema
from radiome.core.execution import DependencySolver, loader, Context
from radiome.core.execution.executor import DaskExecution
from radiome.core.resource_pool import ResourcePool, Resource
from radiome.core.utils.s3 import S3Resource

logger = logging.getLogger(__name__)


def load_resource(resource_pool: ResourcePool, ctx: Context):
    inputs_dir = ctx.inputs_dir
    participant_label = ctx.participant_label
    is_s3 = isinstance(inputs_dir, S3Resource)
    walk = inputs_dir.walk if is_s3 else functools.partial(os.walk, inputs_dir, topdown=False)
    for root, dirs, files in walk():
        for f in files:
            logger.debug(f'Processing file {root}/{f}.')
            if 'nii' in f:
                filename: str = f.split('.')[0]
                if participant_label is None or any([label in filename for label in participant_label]):
                    resource_pool[filename] = inputs_dir % os.path.join(root, f) \
                        if is_s3 \
                        else Resource(os.path.join(root, f))
                    logger.info(f'Added {filename} to the resource pool.')


def build(context: Context, **kwargs) -> ResourcePool:
    rp = ResourcePool()
    load_resource(rp, context)
    for entry, params in schema.steps(context.pipeline_config):
        loader.load(entry)(params, rp, context)

    print('Executing pipeline.......')
    res_rp = DependencySolver(rp, context).execute(executor=DaskExecution())
    print('Execution Completed.')

    if not context.save_working_dir:
        shutil.rmtree(context.working_dir)
    return res_rp
