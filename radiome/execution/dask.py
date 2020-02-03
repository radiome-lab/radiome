from distributed import Client, LocalCluster, Lock, get_client

from .state import JobState

logger = logging.getLogger('radiome.execution.executor')
logger_lock = logger.getChild('lock')


def dask_lock(method):
    def inner(state_instance, *args, **kwargs):
        unlock = False
        try:
            if not state_instance.lock.locked():
                logger_lock.info(f'{method.__name__}: Acquiring lock for job {state_instance.job}')
                state_instance.lock.acquire()
                unlock = True
            return method(state_instance, *args, **kwargs)
        except Exception as e:
            logger_lock.exception(e)
            raise e
        finally:
            if unlock:
                logger_lock.info(f'{method.__name__}: Releasing lock for job {state_instance.job}')
                state_instance.lock.release()
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
    def lock(self):
        return self._lock

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

