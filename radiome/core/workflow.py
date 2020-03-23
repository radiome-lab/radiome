import sys
from functools import wraps

from radiome.core import schema


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def workflow(validate_inputs: bool = True, use_attr: bool = True):
    def decorate(func):
        @wraps(func)
        def create_workflow(config, rp, ctx):
            if validate_inputs:
                config = schema.normalize_inputs(sys.modules[func.__module__].__file__, config)
            if use_attr:
                config = AttrDict(config)
            return func(config, rp, ctx)

        return create_workflow

    return decorate
