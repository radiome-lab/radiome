import logging
import os
from dataclasses import dataclass
from typing import List

import s3fs

from radiome.execution import DependencySolver, workflow as wf
from radiome.execution.executor import DaskExecution
from radiome.resource_pool import FileResource, ResourcePool

logger = logging.getLogger(__name__)


@dataclass
class Context:
    working_dir: str = None
    inputs_dir: str = None
    inputs_cred: str = None
    outputs_dir: str = None
    outputs_cred: str = None
    n_cpus: int = None
    memory: int = None
    participant_label: List[str] = None
    save_working_dir: bool = True
    file_logging: bool = True
    workflow_config: List = None


def load_resource(inputs_dir: str, output_dir: str, resource_pool: ResourcePool, participant_label: List[str] = None):
    is_s3 = inputs_dir.lower().startswith("s3://")
    if is_s3:
        s3 = s3fs.S3FileSystem(anon=True)
        walk = s3.walk
    else:
        walk = os.walk

    for root, dirs, files in walk(inputs_dir, topdown=False):
        for f in files:
            logger.debug(f'Processing file {root} {f}')
            if 'nii' in f:
                filename: str = f.split('.')[0]
                if participant_label is None or any([label in filename for label in participant_label]):
                    resource_pool[filename] = FileResource(f's3://{root}/{f}' if is_s3 else os.path.join(root, f),
                                                           output_dir)
                    logger.info(f'Added {filename} to the resource pool.')


def build(context: Context, **kwargs):
    inputs_dir = context.inputs_dir
    output_dir = context.outputs_dir
    participant_label = context.participant_label
    rp = ResourcePool()
    load_resource(inputs_dir, output_dir, rp, participant_label)

    # TODO more doc on schema format
    for workflow in context.workflow_config:
        if not isinstance(workflow, dict) or len(workflow) != 1:
            raise ValueError('Invalid config schema.')
        for item, config in workflow.items():
            if not isinstance(config, dict):
                raise ValueError('Invalid config schema.')
            wf.load(item)(config, rp, context)
    DependencySolver(rp, work_dir=f'{output_dir}/derivatives').execute(executor=DaskExecution())
    # TODO: Move file from resource pool
