from __future__ import with_statement
import contextlib, os


@contextlib.contextmanager
def cwd(new_dir):
    old_dir = os.getcwd()
    try:
        os.chdir(new_dir)
        yield new_dir
    finally: 
        os.chdir(old_dir)
