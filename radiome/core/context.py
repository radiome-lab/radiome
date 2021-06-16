import os
from dataclasses import dataclass
from typing import Union, List, Dict

from radiome.core.utils.s3 import S3Resource


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
    diagnostics: bool
