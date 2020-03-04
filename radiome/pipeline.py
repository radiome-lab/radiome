import functools
import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union, Dict

from radiome import schema
from radiome.execution import DependencySolver, loader
from radiome.execution.executor import DaskExecution
from radiome.resource_pool import ResourcePool, Resource
from radiome.utils.s3 import S3Resource

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Context:
    working_dir: Union[str, os.PathLike]
    inputs_dir: Union[str, os.PathLike, S3Resource]
    outputs_dir: Union[str, os.PathLike, S3Resource]
    participant_label: List
    n_cpus: int
    memory: int
    save_working_dir: bool
    pipeline_config: Dict


def load_resource(resource_pool: ResourcePool, context: Context):
    inputs_dir = context.inputs_dir
    participant_label = context.participant_label
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


def build(context: Context, **kwargs):
    rp = ResourcePool()
    load_resource(rp, context)
    for entry, params in schema.steps(context.pipeline_config):
        loader.load(entry)(params, rp, context)
    output_dir = os.path.join(context.working_dir, 'outputs') if isinstance(context.outputs_dir,
                                                                            S3Resource) else context.outputs_dir
    Path(output_dir).mkdir(parents=True, exist_ok=True)
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
