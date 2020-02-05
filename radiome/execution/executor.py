import logging
import tempfile

import networkx as nx
from distributed import Client, LocalCluster, Lock, Future, get_client, get_worker
from radiome.execution.job import Job
from .dask import DaskJobState


logger = logging.getLogger('radiome.execution.executor')
logger_lock = logger.getChild('lock')


import cloudpickle
from distributed.protocol.serialize import register_serialization_family

def cloudpickle_dumps(x):
    header = {'serializer': 'cloudpickle'}
    logger.info(f'Dumping {x}')
    frames = [cloudpickle.dumps(x)]
    return header, frames

def cloudpickle_loads(header, frames):
    if len(frames) > 1:
        frame = ''.join(frames)
    else:
        frame = frames[0]
    x = cloudpickle.loads(frame)
    logger.info(f'Loading {x}')
    return x

register_serialization_family('cloudpickle', cloudpickle_dumps, cloudpickle_loads)


class MissingDependenciesException(Exception):
    pass


class Execution:

    def __init__(self, state=None):
        self._state = state

    def execute(self, state, graph):
        SGs = (graph.subgraph(c) for c in nx.weakly_connected_components(graph))
        results = {}

        edge = lambda G, f, t: G.edges[(f, t)]['field']
        result = lambda G, n: \
            results[hash(G.nodes[n]['job'])] \
            if isinstance(G.nodes[n]['job'], Job) \
            else G.nodes[n]['job']()

        for SG in SGs:
            for resource in nx.topological_sort(SG):
                job = SG.nodes[resource]['job']
                if not isinstance(job, Job):
                    continue

                dependencies = {
                    edge(SG, dependency, resource): result(SG, dependency)
                    for dependency in SG.predecessors(resource)
                }

                if any(isinstance(d, Exception) for d in dependencies.values()):
                    results[hash(job)] = MissingDependenciesException()
                    continue

                logger.info(f'Computing job {job} with deps {dependencies}')
                
                try:
                    results[hash(job)] = job(**dependencies)
                except Exception as e:
                    results[hash(job)] = e
                    logger.exception(e)
                
        return results


class DaskExecution(Execution):

    _self_client = False

    def __init__(self, client=None):
        super().__init__()

        if not client:
            cluster = LocalCluster(
                # TODO review resources
                resources={"memory": 30, "cpu": 10, "storage": 20},
                n_workers=10,
                threads_per_worker=10,
                processes=True,
                dashboard_address=None
            )
            client = Client(
                cluster,
                serializers=['cloudpickle'],
                deserializers=['cloudpickle']
            )
            self._self_client = True
        self._client = client

    def __del__(self):
        if self._self_client:
            self._client.close()

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        self._client = get_client()

    async def _result(self, futures):
        for f in futures:
            await f._state.wait()

    def execute(self, state, graph):
        SGs = list(graph.subgraph(c) for c in nx.weakly_connected_components(graph))
        futures = []
        for SG in SGs:
            futures += [self._client.submit(
                self.execute_subgraph, 
                # state=state,
                SG=SG,
                pure=False,
                resources={
                    'storage': sum([
                        SG.nodes[resource]['job'].resources()['storage']
                        for resource in nx.topological_sort(SG)
                        if isinstance(SG.nodes[resource]['job'], Job)
                    ])
                }
            )]

        logger.info(f'Joining execution of {len(futures)} executions: {list(str(s.key) for s in futures)}')

        results = {
            k: v
            for d in self._client.gather(futures, errors='skip')
            for k, v in d.items()
        }
        return results

    def execute_subgraph(
        self,
        # state,
        SG
    ):
        futures = {}

        client = self._client
        worker = get_worker()

        logger.info(f'Computing subgraph')

        edge = lambda G, f, t: G.edges[(f, t)]['field']
        result = lambda G, n: \
            futures[hash(G.nodes[n]['job'])] \
            if isinstance(G.nodes[n]['job'], Job) \
            else G.nodes[n]['job']()

        for resource in nx.topological_sort(SG):
            job = SG.nodes[resource]['job']
            # state_job = DaskJobState(self._client, state, job)
            state_job = job

            if not isinstance(job, Job):
                continue

            dependencies = {
                edge(SG, dependency, resource): result(SG, dependency)
                for dependency in SG.predecessors(resource)
            }
            
            logger.info(f'Computing job {job} with deps {dependencies}')

            resources = job.resources()
            try:
                del resources['storage']
            except:
                pass

            futures[hash(job)] = client.submit(
                job,
                **dependencies,
                resources=resources,
                workers=[worker.address],
                key=str(job),
                pure=False
            )

        logger.info(f'Gathering subgraph')

        return {
            k: v if v is not None else futures[k].exception()
            for k, v in self._client.gather(
                futures, errors='skip'
            ).items()
        }


executors = [
    Execution,
    DaskExecution,
]
