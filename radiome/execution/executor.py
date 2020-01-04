import logging
import networkx as nx

from radiome.execution.job import Job

from .state import JobState

logger = logging.getLogger('radiome.execution.executor')
logger_lock = logger.getChild('lock')


class Execution:

    def __init__(self, state=None):
        self._state = state

    def execute(self, state, graph):
        SGs = (graph.subgraph(c) for c in nx.weakly_connected_components(graph))

        for SG in SGs:
            for resource in reversed(list(nx.topological_sort(SG))):
                if not isinstance(resource, Job):
                    continue
                self.schedule(state, resource)

    def schedule(self, state, job):
        return state[job](**{
            k: self.schedule(state, job_dependency) if isinstance(job_dependency, Job) else job_dependency()
            for k, job_dependency in job.dependencies.items()
        })


from distributed import Client, LocalCluster, Lock, get_client

def dask_lock(method):
    def inner(state_instance, *args, **kwargs):
        unlock = False
        try:
            if not state_instance._lock.locked():
                logger_lock.info(f'{method.__name__}: Acquiring lock for job {state_instance._job}')
                state_instance._lock.acquire()
                unlock = True
            return method(state_instance, *args, **kwargs)
        except Exception as e:
            logger_lock.exception(e)
            raise e
        finally:
            if unlock:
                logger_lock.info(f'{method.__name__}: Releasing lock for job {state_instance._job}')
                state_instance._lock.release()
    return inner

class DaskJobState(JobState):

    def __init__(self, client, state, job):
        super().__init__(state, job)
        self._lock = Lock(self._job.__shorthash__(), client=client)

    def __repr__(self):
        return f'DaskJobState({self._job.__str__()})'

    def __dask_tokenize__(self):
        return hash(self._job)

    def __getstate__(self):
        return {
            '_state': self._state,
            '_job': self._job,
        }

    def __setstate__(self, state):
        self._state = state['_state']
        self._job = state['_job']
        self._lock = Lock(self._job.__shorthash__(), client=get_client())

    @property
    @dask_lock
    def state(self):
        return super().state

    @property
    @dask_lock
    def stored(self):
        return super().stored

    @dask_lock
    def __call__(self, **kwargs):
        return super().__call__(**kwargs)


class DaskExecution(Execution):

    def __init__(self, client=None):
        super().__init__()

        self._self_client = False
        if not client:
            cluster = LocalCluster(processes=True, dashboard_address=None)
            client = Client(cluster)
            self._self_client = True
        self._client = client

        self._futures = {}
        self._joined = False

    def __del__(self):
        if self._self_client:
            self._client.close()

    def execute(self, state, graph):
        super().execute(state, graph)
        logger.info(f'Joining execution of {len(self._futures)} executions: {list(str(s.key) for s in self._futures.values())}')
        self._client.sync(self._result, list(self._futures.values()))
        self._joined = True


    def schedule(self, state, job):
        state_job = DaskJobState(self._client, state, job)

        if not state_job.stored:

            job_hash = hash(job)

            if self._joined:
                done = 'done' if self._futures[job_hash].done() else 'undone'
                logger.warning(f'Computing job {job} when already joined and future says it is {done}')

            if job_hash not in self._futures:

                dependencies = {
                    k: self.schedule(state, v) if isinstance(v, Job) else v()
                    for k, v in job.dependencies.items()
                }

                self._futures[job_hash] = self._client.submit(state_job, **dependencies)

                logger.info(f'Computing job {job} with deps {dependencies}')

            return self._futures[job_hash]

        return state_job.state

    async def _result(self, futures):
        for f in futures:
            await f._state.wait()


executors = [
    Execution,
    DaskExecution,
]
