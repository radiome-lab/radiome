import logging
import os
import tempfile

import cloudpickle

from radiome.execution.utils import cwd

logger = logging.getLogger('radiome.execution.executor')
logger_lock = logger.getChild('lock')
logger_lock.setLevel('ERROR')


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
        job_dir = os.path.join(self._state._scratch, self._job.__hexhash__())
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
        return os.path.isfile(self.cache)

    def __call__(self, **kwargs):
        job = self._job

        if self.cached:
            logger.info(f'Loading cached job {self._job}')
            with open(self.cache, 'rb') as f:
                return cloudpickle.load(f)

        logger.info(f'Computing job {self._job}')
        with cwd(self.dir):
            state = job(**kwargs)
            with open(self.cache, 'wb') as f:
                cloudpickle.dump(state, f)
            logger.info(f'Cached job {self._job}: {state}')
            return state


class Execution:

    def __init__(self, state=None):
        if state is None:
            state = State()
        self._state = state
        self._count = {}

    def schedule(self, job):
        return self._state[job](**{
            k: v.resolve(self)
            for k, v in job.dependencies.items()
        })

    def join(self):
        pass


from distributed import Client, Lock, wait

class DaskJob():
    def __init__(self, job):
        self._job = job
    def __call__(self, **kwargs):
        return self._job(**kwargs)
    def __repr__(self):
        return f'Dask({self._job.__repr__()})'
    def __getattr__(self, attr):
        if '_job' not in self.__dict__:
            raise AttributeError
        return getattr(self.__dict__['_job'], attr)
        
    def __getstate__(self):
        return {'_job': self.__dict__['_job']}
    def __setstate__(self, state):
        self.__dict__['_job'] = state['_job']

    def __dask_graph__(self):
        return None
    def __dask_optimize__(dsk, keys, **kwargs):
        print(dsk, keys, kwargs)
        return dsk
    def __dask_tokenize__(self):
        return hash(self._job)


class DaskJobState(JobState):

    def __init__(self, state, job):
        super().__init__(state, job)
        self._lock = Lock(str(self._job))

    @property
    def state(self):
        unlock = False
        try:
            if not self._lock.locked():
                logger_lock.info(f'State: Acquiring lock for job {self._job}')
                # self._lock.acquire()
                unlock = True
            return super().state
        except Exception as e:
            raise e
        finally:
            if unlock:
                logger_lock.info(f'State: Releasing lock for job {self._job}')
                # self._lock.release()

    @property
    def cached(self):
        unlock = False
        try:
            if not self._lock.locked():
                logger_lock.info(f'Cached: Acquiring lock for job {self._job}')
                # self._lock.acquire()
                unlock = True
            return super().cached
        except Exception as e:
            raise e
        finally:
            if unlock:
                logger_lock.info(f'Cached: Releasing lock for job {self._job}')
                # self._lock.release()

    def __call__(self, **kwargs):
        unlock = False
        try:
            if not self._lock.locked():
                logger_lock.info(f'Call: Acquiring lock for job {self._job}')
                # self._lock.acquire()
                unlock = True
            return super().__call__(**kwargs)
        except Exception as e:
            raise e
        finally:
            if unlock:
                logger_lock.info(f'Call: Releasing lock for job {self._job}')
                # self._lock.release()


class DaskExecution(Execution):

    def __init__(self, state=None):
        super().__init__(state=state)

        # TODO parametrize
        self._client = Client(processes=False)
        self._futures = {}
        self._joined = False

    def schedule(self, job):
        state_job = DaskJobState(self._state, job)

        if not state_job.cached:
            if self._joined:
                logger.warning(f'Computing job {job} when already joined')
            dependencies = {
                k: self.schedule(v)
                for k, v in job.dependencies.items()
            }
            self._futures[job] = self._client.submit(state_job, **dependencies)
            logger.warning(f'Computing job {job} with deps {dependencies}')
            return self._futures[job]

        return state_job.state

    async def _result(self, futures):
        for f in futures:
            await f._state.wait()

    def join(self):
        self._client.sync(self._result, self._futures.values())
        self._joined = True
