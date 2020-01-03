import logging
import networkx as nx
from radiome.resource_pool import Resource, ResourcePool
from radiome.utils import deterministic_hash, Hashable

from .state import FileState
from .executor import Execution
from .job import Job

logger = logging.getLogger('radiome.execution')

# pos = nx.spring_layout(G)
# nx.draw(G, pos, node_size=20, edge_color='r', font_size=20, with_labels=True)
# plt.savefig("graph.png", format="png")

class ResourceSolver:

    def __init__(self, resource_pool):
        self._resource_pool = resource_pool

    @property
    def graph(self):
        G = nx.DiGraph(resource_pool=self._resource_pool)

        extra_dependencies = set()
        for key, resource in self._resource_pool:
            references = {key}
            if resource in G:
                references |= G.node[resource]['references']

            G.add_node(resource, references=references)

            for field, dep in resource.dependencies.items():
                G.add_edge(dep, resource, field=field)
                if dep not in extra_dependencies:
                    extra_dependencies |= {dep}

        observed_dependencies = set()
        while extra_dependencies:
            resource = extra_dependencies.pop()
            observed_dependencies |= {resource}
            for field, dep in resource.dependencies.items():
                G.add_edge(dep, resource, field=field)
                if dep not in observed_dependencies:
                    extra_dependencies |= {dep}

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

        executor.execute(state, G)

        ## TODO
        ## Graph trimming
        ## If it is not on resource pool, it is not important to be cached
        ## Do not check for intermediary steps from StateStorage if not important

        logger.info(f'Gathering resources')
        resource_pool = ResourcePool()
        for resource, attr in self.graph.nodes.items():
            if not isinstance(resource, Job):
                continue

            result = state[resource].state
            for key in attr.get('references', []):
                resource_pool[key] = result

        return resource_pool
