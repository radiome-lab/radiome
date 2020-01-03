import logging
import networkx as nx
from radiome.resource_pool import Resource, ResourcePool
from radiome.utils import deterministic_hash, Hashable

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
        G = self.graph
        SGs = (G.subgraph(c) for c in nx.weakly_connected_components(G))

        ## TODO
        ## Graph trimming
        ## If it is not on resource pool, it is not important to be cached
        ## Do not check for intermediary steps from StateStorage if not important

        for SG in SGs:
            for resource in reversed(list(nx.topological_sort(SG))):
                if not isinstance(resource, Job):
                    continue
                logger.info(f'Resolving resource "{resource}"')
                executor.schedule(resource)

        # Allow delayed executors to perform all the tasks
        executor.join()

        logger.info(f'Gathering resources')
        resource_pool = ResourcePool()
        for resource, attr in self.graph.nodes.items():
            if not isinstance(resource, Job):
                continue
            result = executor.schedule(resource)
            for key in attr.get('references', []):
                resource_pool[key] = result

        return resource_pool


class Job(Hashable):

    _reference = None
    _inputs = None
    _hashinputs = None

    def __init__(self, reference=None):
        self._reference = reference
        self._inputs = {}

    def __str__(self):
        repr = f'{self.__shorthash__()},{self._reference}' if self._reference else f'{self.__shorthash__()}'
        return f'{self.__class__.__name__}({repr})'

    def __repr__(self):
        return str(self)

    def __hashcontent__(self):
        if self._hashinputs:
            inputs = self._hashinputs
        else:
            inputs = { k: deterministic_hash(v) for k, v in self._inputs.items() }
        return (self._reference, tuple(list(sorted(inputs.items(), key=lambda i: i[0]))))

    def __call__(self, **kwargs):
        raise NotImplementedError()

    def __getstate__(self):
        # Do not store other jobs recursively
        return {
            '_reference': self._reference,
            '_hashinputs': {
                k: deterministic_hash(v)
                for k, v in self._inputs.items()
            }
        }

    def __setstate__(self, state):
        self._reference = state['_reference']
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

    def __init__(self, function, reference=None):
        super().__init__(reference)
        self._function = function

    def __hashcontent__(self):
        return (
            super().__hashcontent__(),
            self._function
        )

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
        return f'Computed({self._content[0]}, {self._content[1]})'

    def __hashcontent__(self):
        if self._hashinputs:
            inputs = self._hashinputs
        else:
            inputs = { k: deterministic_hash(v) for k, v in self._inputs.items() }
        return (self._reference, tuple(list(sorted(inputs.items(), key=lambda i: i[0]))))

    def __repr__(self):
        return f'Computed({self.__shorthash__()})'

    def __call__(self, **state):
        return state[self._content[1]][self._content[1]]

    def __getstate__(self):
        # Do not store other jobs recursively
        return {
            '_reference': self._reference,
            '_hashinputs': {
                k: deterministic_hash(v)
                for k, v in self._inputs.items()
            }
        }

    def __setstate__(self, state):
        self._reference = state['_reference']
        self._hashinputs = state['_hashinputs']
        inputs = list(self._hashinputs.items())[0]
        self._content = (inputs[1], inputs[0])
