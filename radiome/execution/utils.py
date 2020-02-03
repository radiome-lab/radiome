import contextlib
import os

@contextlib.contextmanager
def cwd(new_dir):
    old_dir = os.getcwd()
    try:
        os.chdir(new_dir)
        yield new_dir
    finally:
        os.chdir(old_dir)
