import logging
import networkx as nx
from radiome.resource_pool import ResourcePool, InvalidResource

from .state import FileState
from .executor import Execution
from .job import ComputedResource

logger = logging.getLogger('radiome.execution')


class DependencySolver:

    def __init__(self, resource_pool):
        self._resource_pool = resource_pool

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
                references |= G.node[resource_id]['references']

            G.add_node(resource_id, job=resource, references=references)

            for field, dep in resource.dependencies.items():
                dep_id = id(dep)

                if dep_id not in G:
                    G.add_node(dep_id, job=dep)
                G.add_edge(dep_id, resource_id, field=field)

                if dep_id not in instances:
                    instances[dep_id] = dep

                if dep_id not in extra_dependencies:
                    extra_dependencies |= {dep_id}

        while extra_dependencies:
            resource_id = extra_dependencies.pop()
            resource = instances[resource_id]
            for field, dep in resource.dependencies.items():
                dep_id = id(dep)
                if dep_id not in G:
                    G.add_node(dep_id, job=dep)
                G.add_edge(dep_id, resource_id, field=field)

                if dep_id not in instances:
                    instances[dep_id] = dep
                    extra_dependencies |= {dep_id}

        try:
            nx.find_cycle(G, orientation='original')
            raise ValueError('Graph cannot have cycles')
        except nx.NetworkXNoCycle:
            pass

        return G

    def execute(self, executor=None, state=None):

        G = self.graph

        if not executor:
            executor = Execution()

        if not state:
            state = FileState()

        executor.execute(state=state, graph=G)

        logger.info('Gathering resources')
        resource_pool = ResourcePool()
        for _, attr in self.graph.nodes.items():
            job = attr['job']
            if not isinstance(job, ComputedResource):
                continue

            # Only get states which has references
            references = attr.get('references', [])
            if not references:
                continue

            if state.erred(job):
                result = InvalidResource(job, state.err(job))
            elif not state.stored(job):
                result = InvalidResource(job)
            else:
                result = state.state(job)

            for key in attr.get('references', []):
                resource_pool[key] = result

        return resource_pool
