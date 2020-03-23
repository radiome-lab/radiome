# -*- coding: utf-8 -*-

"""Top-level package for radiome."""

__author__ = """Cameron Craddock, Anibal Solon, Pu Zhao"""
__email__ = 'cameron.craddock@gmail.com, anibalsolon@gmail.com, puzhao@utexas.edu'
__version__ = '0.1.0'

from .workflow import workflow, AttrDict
from .context import Context
from .resource_pool import ResourceKey, Resource, ResourcePool
