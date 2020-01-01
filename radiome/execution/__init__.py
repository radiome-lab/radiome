import logging
import networkx as nx
from radiome.resource_pool import Resource, ResourcePool

from .executor import Execution


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

    def execute(self, executor=None):
        if executor is None:
            executor = Execution()

        G = self.graph
        SGs = (G.subgraph(c) for c in nx.weakly_connected_components(G))

        ## TODO
        ## Graph trimming
        ## If it is not on resource pool, it is not important to be cached
        ## Do not check for intermediary steps from StateStorage if not important

        for SG in SGs:
            for resource in reversed(list(nx.topological_sort(SG))):
                logger.info(f'Resolving resource "{resource}"')
                executor.schedule(resource)

        # Allow delayed executors to perform all the tasks
        executor.join()

        resource_pool = ResourcePool()
        for resource, attr in self.graph.nodes.items():
            result = executor.schedule(resource)
            for key in attr.get('references', []):
                resource_pool[key] = result

        return resource_pool


class Job:

    _inputs = None
    _hashinputs = None

    def __init__(self):
        self._inputs = {}

    def __repr__(self):
        return f'{self.__class__.__name__}({self.__shorthash__()})'

    def __hash__(self):
        if self._hashinputs:
            inputs = self._hashinputs
        else:
            inputs = { k: hash(v) for k, v in self._inputs.items() }
        return hash(tuple(sorted(inputs.items(), key=lambda i: i[0])))

    def __hexhash__(self):
        return hex(abs(hash(self)))

    def __shorthash__(self):
        return self.__hexhash__()[-8:]

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __call__(self, **kwargs):
        raise NotImplementedError()

    def __getstate__(self):
        # Do not store other jobs recursively
        return {
            '_hashinputs': {
                k: hash(v)
                for k, v in self._inputs.items()
            }
        }

    def __setstate__(self, state):
        self._hashinputs = state['_hashinputs']

    def __getattr__(self, attr):
        if attr.startswith('_'):
            return self.__dict__[attr]

        return ComputedResource((self, attr))

    def __setattr__(self, attr, value):
        if attr.startswith('_'):
            self.__dict__[attr] = value
            return

        if isinstance(value, (Resource, ResourcePool)):
            self._inputs[attr] = value
            return

    @property
    def dependencies(self):
        return {k: v for k, v in self._inputs.items()}


class PythonJob(Job):

    def __init__(self, function):
        super().__init__()
        self._function = function

    def __hash__(self):
        return hash((super().__hash__(), self._function))

    def __call__(self, **kwargs):
        return self._function(**kwargs)

    def __getstate__(self):
        return {
            **super().__getstate__(),
            '_function': self._function
        }

    def __setstate__(self, state):
        super().__setstate__(state)
        self._function = state['_function']


class ComputedResource(Job, Resource):

    def __init__(self, content):
        self._content = content
        self._inputs = { content[1]: content[0] }

    def __str__(self):
        return f'Computed({self.__shorthash__()})'

    def __repr__(self):
        return f'Computed({self.__shorthash__()})'

    def __call__(self, **state):
        return state[self._content[1]][self._content[1]]

    def __setstate__(self, state):
        super().__setstate__(state)
        input = list(self._hashinputs.items())[0]
        self._content = (input[1], input[0])
