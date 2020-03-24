import sys
from functools import wraps

from radiome.core import schema


class AttrDict(dict):
    """ Dict that supports retrieving value via attribute.

    AttrDict has the same methods as dict. Besides, you can retrieve value using key as attribute.
    For example: d = {'a': 1}, thus, d.a == 1.

    """

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def workflow(validate_inputs: bool = True, use_attr: bool = True):
    """
    Decorator for a workflow. Control the behavior of create_workflow.

    Args:
        validate_inputs: Validate inputs against the schema in spec.yml.
        use_attr: Use AttrDict instead of regular dicts. Retrieve values via attribute.

    Returns:
        Should use as a decorator, return a decorated function.

    """

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
