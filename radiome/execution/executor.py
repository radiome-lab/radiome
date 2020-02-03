import logging
import tempfile

import networkx as nx
from distributed import Client, LocalCluster, Lock, get_client, get_worker

from radiome.execution.job import Job


logger = logging.getLogger('radiome.execution.executor')
logger_lock = logger.getChild('lock')


class Execution:

    def __init__(self, state=None):
        self._state = state

    def execute(self, state, graph):
        SGs = (graph.subgraph(c) for c in nx.weakly_connected_components(graph))
        results = {}
        for SG in SGs:
            for resource in nx.topological_sort(SG):
                job = SG.nodes[resource]['job']
                if not isinstance(job, Job):
                    continue

                dependencies = {
                    k: results[str(hash(j))] if isinstance(j, Job) else j()
                    for k, j in job.dependencies().items()
                }

                logger.info(f'Computing job {job} with deps {dependencies}')
                
                try:
                    results[str(hash(job))] = job(**dependencies)
                except Exception as e:
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
                n_workers=2,
                processes=False,
                dashboard_address=None,
                local_directory=tempfile.mkdtemp()
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

    async def _result(self, futures):
        for f in futures:
            await f._state.wait()

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        self._client = get_client()

    def execute(self, state, graph):
        SGs = (graph.subgraph(c) for c in nx.weakly_connected_components(graph))
        futures = []
        for SG in SGs:
            logger.info({
                'storage': sum([
                    SG.nodes[resource]['job'].resources()['storage']
                    for resource in nx.topological_sort(SG)
                    if isinstance(SG.nodes[resource]['job'], Job)
                ])
            })
            futures += [self._client.submit(
                self.execute_subgraph, 
                # state=state,
                subgraph=SG,
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
        results = {k: v for d in self._client.gather(futures) for k, v in d.items()}
        return results

    def execute_subgraph(
        self,
        # state,
        subgraph
    ):
        futures = {}

        client = self._client
        worker = get_worker()

        logger.info(f'Computing subgraph')

        for resource in nx.topological_sort(subgraph):
            job = subgraph.nodes[resource]['job']
            # state_job = DaskJobState(self._client, state, job)
            state_job = job

            if not isinstance(job, Job):
                continue

            dependencies = {
                k: futures[str(hash(j))] if isinstance(j, Job) else j()
                for k, j in job.dependencies().items()
            }

            logger.info(f'Computing job {job} with deps {dependencies}')

            resources = job.resources()
            try:
                del resources['storage']
            except:
                pass

            futures[str(hash(job))] = client.submit(
                state_job,
                **dependencies,
                resources=resources,
                workers=[worker.address],
                key=str(job),
                pure=False
            )

        logger.info(f'Gathering subgraph')
        return client.gather(futures)


executors = [
    Execution,
    DaskExecution,
]
