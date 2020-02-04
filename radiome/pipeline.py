import logging
import os
from typing import List

import s3fs
import yaml

from radiome.execution import DependencySolver, workflow as wf, FileState
from radiome.execution.executor import DaskExecution
from radiome.resource_pool import FileResource, ResourcePool

logger = logging.getLogger(__name__)


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


def build(inputs_dir: str, output_dir: str, config_file_dir: str, participant_label: List[str] = None, **kwargs):
    rp = ResourcePool()
    load_resource(inputs_dir, output_dir, rp, participant_label)
    context = {
        'working_dir': output_dir,
        **kwargs
    }
    with open(config_file_dir, 'r') as f:
        data: List = yaml.safe_load(f)
        logger.info(f'Loaded the config file {config_file_dir}.')
    # TODO more doc on schema format
    for workflow in data:
        if not isinstance(workflow, dict) or len(workflow) != 1:
            raise ValueError('Invalid config schema.')
        for item, config in workflow.items():
            if not isinstance(config, dict):
                raise ValueError('Invalid config schema.')
            wf.load(item)(config, rp, context)
    DependencySolver(rp).execute(executor=DaskExecution(), state=FileState(output_dir))
