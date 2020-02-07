import logging
import contextlib
import os

logger = logging.getLogger('radiome.execution.utils')

@contextlib.contextmanager
def cwd(new_dir):
    new_dir = os.path.abspath(new_dir)
    old_dir = os.getcwd()
    try:
        logger.info(f'Changing directory to {new_dir}')
        os.chdir(new_dir)
        yield new_dir
    finally:
        os.chdir(old_dir)
