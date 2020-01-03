import logging
import os
import tempfile

import cloudpickle

from radiome.resource_pool import Resource
from radiome.execution import ComputedResource, Job
from radiome.execution.utils import cwd

from radiome.utils import Hashable

logger = logging.getLogger('radiome.execution.executor')
logger_lock = logger.getChild('lock')
logger_state = logger.getChild('state')


class State:

    def __init__(self, scratch=None):
        if not scratch:
            scratch = tempfile.mkdtemp(prefix='rdm.')
        self._scratch = scratch

        logger.info(f'Memoizing jobs to {scratch}')

    def __contains__(self, job):
        return self.stored(job)

    def __getitem__(self, job):
        return JobState(self, job)

    def dir(self, job):
        job_repr = job.__repr__()
        job_dir = os.path.join(self._scratch, job_repr)
        os.makedirs(job_dir, exist_ok=True)
        return job_dir

    def state(self, job):
        if not self.stored(job):
            raise ValueError(f'Job {job} not stored.')

        with open(self.state_file(job), 'rb') as f:
            return cloudpickle.load(f)

    def state_file(self, job):
        return os.path.join(self.dir(job), 'state.pkl')

    def stored(self, job):
        f = self.state_file(job)
        is_stored = os.path.isfile(f)
        logger.info(f'{job.__repr__()}: {f} is stored: {is_stored}')
        return is_stored


class JobState:

    def __init__(self, state, job):
        self._state = state
        self._job = job

    def __repr__(self):
        return f'JobState({self._job.__repr__()})'

    @property
    def dir(self):
        return self._state.dir(self._job)

    @property
    def state(self):
        return self._state.state(self._job)

    @property
    def state_file(self):
        return self._state.state_file(self._job)

    @property
    def stored(self):
        return self._state.stored(self._job)

    def __getstate__(self):
        return {
            '_state': self._state,
            '_job': self._job,
        }

    def __setstate__(self, state):
        self._state = state['_state']
        self._job = state['_job']

    def __call__(self, **kwargs):
        job = self._job
        logger_state.info(f'{self.__repr__()}: might compute')

        if self.stored:
            logger_state.info(f'{self.__repr__()}: loading stored')
            with open(self.state_file, 'rb') as f:
                return cloudpickle.load(f)

        logger_state.info(f'{self.__repr__()}: computing')
        with cwd(self.dir):
            state = job(**kwargs)
            with open(self.state_file, 'wb') as f:
                cloudpickle.dump(state, f)
            logger_state.info(f'{self.__repr__()}: stored')
            return state


class Execution:

    def __init__(self, state=None):
        if state is None:
            state = State()
        self._state = state

    def schedule(self, job):
        return self._state[job](**{
            k: self.schedule(v)
            for k, v in job.dependencies.items()
        })

    def join(self):
        pass


from distributed import Client, Lock, wait, get_client

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

    def __init__(self, state=None, client=None):
        super().__init__(state=state)

        self._self_client = False
        if not client:
            client = Client(processes=True)
            self._self_client = True
        self._client = client
        self._futures = {}
        self._joined = False

    def __del__(self):
        if self._self_client:
            self._client.close()

    def schedule(self, job):
        state_job = DaskJobState(self._client, self._state, job)

        if not state_job.stored:

            job_hash = hash(job)

            if self._joined:
                done = 'done' if self._futures[job_hash].done() else 'undone'
                logger.warning(f'Computing job {job} when already joined and future says it is {done}')

            if job_hash not in self._futures:

                dependencies = {
                    k: self.schedule(v) if isinstance(v, Job) else v()
                    for k, v in job.dependencies.items()
                }

                self._futures[job_hash] = self._client.submit(state_job, **dependencies)

                logger.info(f'Computing job {job} with deps {dependencies}')
            
            return self._futures[job_hash]

        return state_job.state

    async def _result(self, futures):
        for f in futures:
            await f._state.wait()

    def join(self):
        logger.info(f'Joining execution of {len(self._futures)} executions: {list(str(s.key) for s in self._futures.values())}')

        self._client.sync(self._result, list(self._futures.values()))
        self._joined = True


executors = [
    Execution,
    DaskExecution,
]