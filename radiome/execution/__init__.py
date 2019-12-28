import networkx as nx
from dask import delayed
from radiome.resource_pool import Resource, ResourcePool


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

    def execute(self, execution=None):
        if execution is None:
            execution = Execution()

        for SG in nx.weakly_connected_component_subgraphs(self.graph):
            for resource in nx.topological_sort(SG):
                resource.resolve(execution)

        # Allow delayed executors to perform all the tasks
        execution.join()

        resource_pool = ResourcePool()
        for resource, attr in self.graph.nodes.items():
            result = resource.resolve(execution)
            for key in attr.get('references', []):
                resource_pool[key] = result

        return resource_pool

class Execution:

    results = {}

    def schedule(self, job):
        if job not in self.results:
            self.results[job] = job(**{
                k: v.resolve(self)
                for k, v in job.dependencies.items()
            })
        return self.results[job]

    def join(self):
        pass

class DaskJob():
    def __init__(self, job):
        self._job = job
    def __call__(self, **kwargs):
        return self._job(**kwargs)
    def __hash__(self):
        return hash(self._job)
    def __eq__(self, other):
        return hash(self._job) == hash(other)
    def __dask_graph__(self):
        return None
    def __repr__(self):
        return f'Dask({self._job.__repr__()})'

class DaskExecution(Execution):

    results = {}

    def schedule(self, job):
        hjob = DaskJob(job)
        if hjob not in self.results:
            self.results[hjob] = delayed(hjob)(**{
                k: v.resolve(self)
                for k, v in job.dependencies.items()
            })
        return self.results[hjob]

    def join(self):
        self.results = delayed(dict)(self.results).compute()

class ComputedResource(Resource):

    def __str__(self):
        return f'Computed({self.__shorthash__()})'

    def __repr__(self):
        return f'Computed({self.__hexhash__()})'

    def resolve(self, execution):
        result = execution.schedule(self._content[0])
        return result[self._content[1]]

    @property
    def dependencies(self):
        return self._content[0].dependencies


class Job:

    _inputs = None

    def __init__(self):
        self._inputs = {}

    def __repr__(self):
        return f'{self.__class__.__name__}({self.__hexhash__()})'

    def __hash__(self):
        return hash(tuple(sorted(self._inputs.items(), key=lambda i: i[0])))

    def __hexhash__(self):
        return hex(abs(hash(self)))

    def __shorthash__(self):
        return self.__hexhash__()[-8:]

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __call__(self, **kwargs):
        raise NotImplementedError()

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