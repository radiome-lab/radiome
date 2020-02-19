import logging
import os
from dataclasses import dataclass
from typing import List, Union

from radiome.execution import DependencySolver, workflow as wf
from radiome.execution.executor import DaskExecution
from radiome.resource_pool import ResourcePool, Resource
from radiome.utils.s3 import S3Resource

logger = logging.getLogger(__name__)


@dataclass
class Context:
    working_dir: Union[str, os.PathLike] = None
    inputs_dir: Union[str, os.PathLike, S3Resource] = None
    outputs_dir: Union[str, os.PathLike, S3Resource] = None
    participant_label: [List] = None
    n_cpus: int = None
    memory: int = None
    save_working_dir: bool = True
    file_logging: bool = True
    workflow_config: List = None


def load_resource(inputs_dir: Union[str, S3Resource], working_dir: str, resource_pool: ResourcePool,
                  participant_label: List[str] = None):
    is_s3 = isinstance(inputs_dir, S3Resource)

    def add_to_resource(root, dirs, f):
        logger.debug(f'Processing file {root}/{f}')
        if 'nii' in f:
            filename: str = f.split('.')[0]
            if participant_label is None or any([label in filename for label in participant_label]):
                resource_pool[filename] = inputs_dir % f's3://{os.path.join(root, f)}' if is_s3 else Resource(
                    os.path.join(root, f))
                logger.info(f'Added {filename} to the resource pool.')

    if is_s3:
        inputs_dir.walk(add_to_resource, file_only=True)
    else:
        for root, dirs, files in os.walk(inputs_dir, topdown=False):
            for f in files:
                add_to_resource(root, dirs, f)


def build(context: Context, **kwargs):
    rp = ResourcePool()
    load_resource(context.inputs_dir, context.working_dir, rp, context.participant_label)

    # TODO more doc on schema format
    for workflow in context.workflow_config:
        if not isinstance(workflow, dict) or len(workflow) != 1:
            raise ValueError('Invalid config schema.')
        for item, config in workflow.items():
            if not isinstance(config, dict):
                raise ValueError('Invalid config schema.')
            wf.load(item)(config, rp, context)
    DependencySolver(rp, work_dir=f'{context.outputs_dir}/derivatives').execute(executor=DaskExecution())
    # TODO: Move file from resource pool
