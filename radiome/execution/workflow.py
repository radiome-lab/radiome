import importlib
import importlib.util
import logging
import os
import sys
import tempfile
from typing import Callable
from urllib.parse import urlparse

from git.repo.base import Repo

logger = logging.getLogger(__name__)


def _import_name(name: str):
    if name in sys.modules:
        return sys.modules[name]
    elif importlib.util.find_spec(name) is not None:
        return importlib.import_module(name)
    else:
        return None


def _import_path(path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, f'{path}/__init__.py')
    if spec is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        return module
    except BaseException:
        del sys.modules[module_name]
        return None


def _resolve_git(url: str, working_directory: str) -> str:
    if not url.startswith('git://') or not url.endswith('.git'):
        raise ValueError(f'Invalid url {url}')
    if not os.path.exists(working_directory):
        raise ValueError(f'Invalid working directory {working_directory}')
    if len(os.listdir(working_directory)):
        raise ValueError(f'The working directory {working_directory} is not empty!')
    Repo.clone_from(url, working_directory)
    logger.debug(f'Cloned {url} and saved to {working_directory}')
    # TODO: handle exception
    return working_directory


def load(item: str) -> Callable:
    if item.startswith('git://'):
        scratch = tempfile.mkdtemp(prefix='rdm.workflow.')
        module_name = 'radiome_workflow_' + urlparse(item).path[1:-4].replace('/', '_')
        module = _import_path(_resolve_git(item, scratch), module_name)
        logger.info(f'Load the workflow {item} successfully via git repo.')
    else:
        module = _import_name(item)
        logger.info(f'Load the workflow {item} successfully via module name.')
    # TODO check signature
    if module and hasattr(module, 'create_workflow') and callable(module.create_workflow):
        return module.create_workflow
    raise ValueError(f'Invalid workflow {item}. Cannot find the create_workflow function.')
