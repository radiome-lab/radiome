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
# logger_lock.setLevel('ERROR')


class State:

    def __init__(self, scratch=None):
        if not scratch:
            scratch = tempfile.mkdtemp(prefix='rdm.')
        self._scratch = scratch

        logger.info(f'Memoizing jobs to {scratch}')

    def __contains__(self, job):
        return JobState(self, job).cached

    def __getitem__(self, job):
        return JobState(self, job)


class JobState:

    def __init__(self, state, job):
        self._state = state
        self._job = job

    def __repr__(self):
        return f'JobState({self._job.__repr__()})'

    @property
    def dir(self):
        job_dir = os.path.join(self._state._scratch, self._job.__shorthash__())
        os.makedirs(job_dir, exist_ok=True)
        return job_dir

    @property
    def state(self):
        job = self._job

        if not self.cached:
            raise ValueError(f'Job {job} not cached.')

        # TODO add cache
        with open(self.cache, 'rb') as f:
            return cloudpickle.load(f)

    @property
    def cache(self):
        return os.path.join(self.dir, 'state.pkl')

    @property
    def cached(self):
        is_cached = os.path.isfile(self.cache)
        logger.info(f'{self.__repr__()}: {self.cache} is cached: {is_cached}')

        with open(self.cache + '.txt', 'w') as f:
            f.write(str(self._job.__hashcontent__()) + ' ')
            f.write(str(self._job) + ' ')
            f.write(self._job.__repr__() + '\n')
            
        return is_cached

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

        if self.cached:
            logger_state.info(f'{self.__repr__()}: loading cached')
            with open(self.cache, 'rb') as f:
                return cloudpickle.load(f)

        logger_state.info(f'{self.__repr__()}: computing')
        with cwd(self.dir):
            state = job(**kwargs)
            with open(self.cache, 'wb') as f:
                cloudpickle.dump(state, f)
            logger_state.info(f'{self.__repr__()}: cached')
            return state


class Execution:

    def __init__(self, state=None):
        if state is None:
            state = State()
        self._state = state
        self._count = {}

    def schedule(self, job):
        return self._state[job](**{
            k: self.schedule(v)
            for k, v in job.dependencies.items()
        })

    def join(self):
        pass


from distributed import Client, Lock, wait, get_client


class DaskJobState(JobState):

    def __init__(self, client, state, job):
        super().__init__(state, job)
        self._lock = Lock(self._job.__repr__(), client=client)

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
        self._lock = Lock(hash(self._job), client=get_client())

    @property
    def state(self):
        unlock = False
        try:
            if not self._lock.locked():
                logger_lock.info(f'State: Acquiring lock for job {self._job}')
                self._lock.acquire()
                unlock = True
            return super().state
        except Exception as e:
            logger_lock.exception(e)
            raise e
        finally:
            if unlock:
                logger_lock.info(f'State: Releasing lock for job {self._job}')
                self._lock.release()

    @property
    def cached(self):
        unlock = False
        try:
            if not self._lock.locked():
                logger_lock.info(f'Cached: Acquiring lock for job {self._job}')
                self._lock.acquire()
                unlock = True
            return super().cached
        except Exception as e:
            logger_lock.exception(e)
            raise e
        finally:
            if unlock:
                logger_lock.info(f'Cached: Releasing lock for job {self._job}')
                self._lock.release()

    def __call__(self, **kwargs):
        unlock = False
        try:
            if not self._lock.locked():
                logger_lock.info(f'Call: Acquiring lock for job {self._job}')
                self._lock.acquire()
                unlock = True
            return super().__call__(**kwargs)
        except Exception as e:
            logger_lock.exception(e)
            raise e
        finally:
            if unlock:
                logger_lock.info(f'Call: Releasing lock for job {self._job}')
                self._lock.release()


class DaskExecution(Execution):

    def __init__(self, state=None):
        super().__init__(state=state)

        # TODO parametrize
        self._client = Client(processes=True)
        self._futures = {}
        self._futures_ordered = []
        self._joined = False

    def schedule(self, job):
        state_job = DaskJobState(self._client, self._state, job)

        if not state_job.cached:

            if self._joined:
                done = 'done' if self._futures[job].done() else 'undone'
                logger.warning(f'Computing job {job} when already joined and future says it is {done}')

            if job not in self._futures:

                dependencies = {
                    k: self.schedule(v) if isinstance(v, Job) else v()
                    for k, v in job.dependencies.items()
                }

                self._futures[job] = self._client.submit(state_job, **dependencies)
                self._futures_ordered.append(self._futures[job])

                logger.info(f'Computing job {job} with deps {dependencies}')
            
            return self._futures[job]

        return state_job.state

    async def _result(self, futures):
        for f in futures:
            await f._state.wait()

    def join(self):
        logger.info(f'Joining execution of {len(self._futures_ordered)} executions: {list(str(s.key) for s in reversed(self._futures_ordered))}')

        self._client.sync(self._result, self._futures_ordered)
        self._joined = True
