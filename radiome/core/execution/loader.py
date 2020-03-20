import importlib
import importlib.util
import logging
import os
import sys
import tempfile
from functools import wraps
from types import ModuleType
from typing import Callable, Optional
from urllib.parse import urlparse

from git.repo.base import Repo

from radiome.core import schema
from radiome.core.jobs import ComputedResource

logger = logging.getLogger(__name__)


def _import_name(name: str) -> Optional[ModuleType]:
    """
    Import a Python module dynamically through a full name,
    e.g., radiome.workflows.anatomical.initial.

    Args:
        name: Full name of the module.

    Returns:
        If module is found and imported successfully, the module
        will be returned. Otherwise, None will be returned.
    """
    if name in sys.modules:
        # Necessary for mocking function to work
        importlib.reload(sys.modules[name])
        return sys.modules[name]
    elif importlib.util.find_spec(name) is not None:
        return importlib.import_module(name)
    else:
        return None


def _import_path(path: str, module_name: str, entry_file: str = '__init__.py') -> Optional[ModuleType]:
    """
    Import a Python module dynamically through file path.

    Args:
        entry_file: Entry point for the module, default is __init__.py
        path: Path where the module locates.
        module_name: The name of module to be imported.

    Returns:
        If module is found and imported successfully, the module
        will be returned. Otherwise, None will be returned.
    """
    spec = importlib.util.spec_from_file_location(module_name, f'{path}/{entry_file}')
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


def _resolve_git(url: str, destination: str) -> str:
    """
    Clone a gh:// url to a local folder.

    Args:
        url: git url, the format is gh://organization/repo
        destination: the destination directory for the repo, must be empty

    Returns:
        The destination directory.

    Raises:
        ValueError: The github url is not valid.
        FileExistsError: The destination directory is not empty.
    """
    url = url.lower()
    if not url.startswith('gh://'):
        raise ValueError(f'{url} is not a valid gh:// url.')
    if len(os.listdir(destination)):
        raise FileExistsError(f'The working directory {destination} is not empty!')
    parsed = urlparse(url)
    org, repo = parsed.netloc, parsed.path[1:]
    git_url = f'git://github.com/{org}/{repo}.git'
    try:
        Repo.clone_from(git_url, destination)
    except Exception as e:
        raise ValueError(f'The github url can not be cloned. Message: {e}')
    logger.info(f'Cloned {url} to {destination}')
    return destination


def _set_bids_outputs(func: Callable, name: str):
    @wraps(func)
    def create_workflow(config, rp, ctx):
        ComputedResource._bids_name = name
        res = func(config, rp, ctx)
        ComputedResource._bids_name = None
        return res

    return create_workflow


def load(item: str) -> Callable:
    """
    Load a module through full name or github url.

    Args:
        item: Full name or github url for the module.

    Returns:
        A "create_workflow" callable.

    Raises:
        ValueError: The imported module doesn't have a create_workflow callable.
    """
    if item.startswith('gh://'):
        scratch = tempfile.mkdtemp(prefix='rdm.workflow.')
        module_name = 'radiome_workflow_' + urlparse(item).path[1:]
        module = _import_path(_resolve_git(item, scratch), module_name)
        logger.info(f'Loaded the workflow {item} via git repo.')
    else:
        module = _import_name(item)
        if module is None:
            module = _import_path(item, 'radiome_workflow_' + os.path.basename(item))
            logger.info(f'Loaded the workflow {item} via path.')
        else:
            logger.info(f'Loaded the workflow {item} via module name.')
    if module and hasattr(module, 'create_workflow') and callable(module.create_workflow):
        return _set_bids_outputs(module.create_workflow, schema.get_name(module))
    raise ValueError(f'Invalid workflow {item}. Cannot find the create_workflow function.')
