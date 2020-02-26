import logging
import os
import shutil
from dataclasses import dataclass
from typing import List, Union, Dict

from radiome.execution import DependencySolver, loader
from radiome.execution.executor import DaskExecution
from radiome.resource_pool import ResourcePool, Resource
from radiome import schema
from radiome.utils.s3 import S3Resource

logger = logging.getLogger(__name__)


@dataclass
class Context:
    working_dir: Union[str, os.PathLike] = None
    inputs_dir: Union[str, os.PathLike, S3Resource] = None
    outputs_dir: Union[str, os.PathLike, S3Resource] = None
    participant_label: List = None
    n_cpus: int = None
    memory: int = None
    save_working_dir: bool = True
    file_logging: bool = True
    pipeline_config: Dict = None


def load_resource(resource_pool: ResourcePool, context: Context):
    inputs_dir = context.inputs_dir
    participant_label = context.participant_label
    is_s3 = isinstance(inputs_dir, S3Resource)

    def add_to_resource(root, dirs, f):
        logger.debug(f'Processing file {root}/{f}.')
        if 'nii' in f:
            filename: str = f.split('.')[0]
            if participant_label is None or any([label in filename for label in participant_label]):
                resource_pool[filename] = inputs_dir % f's3://{os.path.join(root, f)}' \
                    if is_s3 \
                    else Resource(os.path.join(root, f))
                logger.info(f'Added {filename} to the resource pool.')

    if is_s3:
        inputs_dir.walk(add_to_resource, file_only=True)
    else:
        for root, dirs, files in os.walk(inputs_dir, topdown=False):
            for f in files:
                add_to_resource(root, dirs, f)


def build(context: Context, **kwargs):
    rp = ResourcePool()
    load_resource(rp, context)
    for entry, params in schema.steps(context.pipeline_config):
        loader.load(entry)(params, rp, context)
    output_dir = os.path.join(context.working_dir, 'outputs') if isinstance(context.outputs_dir,
                                                                            S3Resource) else context.outputs_dir
    DependencySolver(rp, work_dir=context.working_dir, output_dir=output_dir).execute(executor=DaskExecution())
    if isinstance(context.outputs_dir, S3Resource):
        try:
            context.outputs_dir.upload(output_dir)
        except Exception:
            raise
        else:
            if not context.save_working_dir:
                shutil.rmtree(context.working_dir)
    else:
        if not context.save_working_dir:
            shutil.rmtree(context.working_dir)