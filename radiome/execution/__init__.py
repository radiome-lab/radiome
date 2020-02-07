import os
import logging
import shutil

import networkx as nx
from pathlib import Path

from radiome.resource_pool import InvalidResource, ResourcePool
from radiome.utils import Hashable

from .executor import Execution
from .job import ComputedResource, Job
from .utils import cwd

logger = logging.getLogger('radiome.execution.state')

class State(Hashable):
    _master = True

    def __init__(self, work_dir, resource):
        self._work_dir = os.path.abspath(work_dir)
        self._resource = resource

    def __call__(self, **dependencies):
        if isinstance(self._resource, Job):
            resource_hash = hash(self._resource)
            resource_dir = os.path.join(self._work_dir, str(resource_hash))
            try:
                os.makedirs(resource_dir)
            except:
                pass
            logger.info(f'{resource_dir}: {os.path.exists(resource_dir)}')
            with cwd(resource_dir):
                result = self._resource(**dependencies)
        else:
            result = self._resource(**dependencies)
        return result

    def __str__(self):
        return self._resource.__str__()

    def __repr__(self):
        return self._resource.__repr__()

    def __longhash__(self):
        return self._resource.__longhash__()

    def __del__(self):
        if not isinstance(self._resource, Job):
            return
        if not self._master:
            return

        resource_hash = hash(self._resource)
        try:
            shutil.rmtree(f'./{resource_hash}')
        except:
            pass
        
    def __getstate__(self):
        return {
            '_resource': self._resource,
            '_work_dir': self._work_dir,
        }

    def __setstate__(self, state):
        self._resource = state['_resource']
        self._master = False
        self._work_dir = state['_work_dir']

    def resources(self):
        if isinstance(self._resource, Job):
            return self._resource.resources()
        return {
            'cpu': 0,
            'memory': 0,
            'storage': 0,
        }

    def __getattr__(self, attr):
        if attr == 'resource':
            return self._resource
        if attr in self.__dict__:
            return self.__dict__[attr]
        raise AttributeError(f'Invalid attr: {attr}')


class DependencySolver:

    def __init__(self, resource_pool, work_dir='.'):
        self._resource_pool = resource_pool
        self._work_dir = os.path.abspath(work_dir)

    @property
    def graph(self):
        G = nx.DiGraph(resource_pool=self._resource_pool)

        instances = {}

        extra_dependencies = set()
        for key, resource in self._resource_pool:
            resource_id = id(resource)
            references = {key}

            if resource_id not in instances:
                instances[resource_id] = resource

            if resource_id in G:
                references |= G.nodes[resource_id]['references']

            G.add_node(resource_id, job=State(self._work_dir, resource), references=references)

            for field, dep in resource.dependencies().items():
                dep_id = id(dep)

                if dep_id not in G:
                    G.add_node(dep_id, job=State(self._work_dir, dep))
                G.add_edge(dep_id, resource_id, field=field)

                if dep_id not in instances:
                    instances[dep_id] = dep

                if dep_id not in extra_dependencies:
                    extra_dependencies |= {dep_id}

        while extra_dependencies:
            resource_id = extra_dependencies.pop()
            resource = instances[resource_id]
            for field, dep in resource.dependencies().items():
                dep_id = id(dep)
                if dep_id not in G:
                    G.add_node(dep_id, job=State(self._work_dir, dep))
                G.add_edge(dep_id, resource_id, field=field)

                if dep_id not in instances:
                    instances[dep_id] = dep
                    extra_dependencies |= {dep_id}

        try:
            nx.find_cycle(G, orientation='original')
            raise ValueError('Graph cannot have cycles')
        except nx.NetworkXNoCycle:
            pass

        relabeling = {}
        for resource in nx.topological_sort(G):
            job = G.nodes[resource]['job']
            jobid = id(job)
            job.__update_hash__()
            G.nodes[resource]['job'] = job

        return G

    def execute(self, executor=None):

        G = self.graph

        if not executor:
            executor = Execution()

        logger.info(f'Executing with {executor.__class__.__name__}')

        results = executor.execute(graph=G)

        logger.info('Gathering resources')
        resource_pool = ResourcePool()
        for _, attr in self.graph.nodes.items():

            job = attr['job']
            if not isinstance(job.resource, ComputedResource):
                continue

            job_hash = hash(job)

            references = attr.get('references', [])
            if not references:
                continue

            if job_hash in results and not isinstance(results[job_hash], Exception):
                result = results[job_hash]
            else:
                result = InvalidResource(job)

            for key in attr.get('references', []):
                if isinstance(result, Path):
                    logger.info(f'Setting {result} in {key}')
                    ext = os.path.basename(result).split('.', 1)[-1]
                    output = f'./{key}.{ext}'
                    logger.info(f'Copying file from "{result}" to "{output}"')
                    shutil.copyfile(result, output)
                    result = output
                resource_pool[key] = result

        return resource_pool
