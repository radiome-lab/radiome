import logging
import os
import types
import tempfile

import cloudpickle

from radiome.execution.utils import cwd

logger = logging.getLogger('radiome.execution.executor')
logger_state = logger.getChild('state')


class JobState:

    def __init__(self, state, job):
        self._state = state
        self._job = job

    def __repr__(self):
        return f'JobState({self._job.__repr__()})'

    @property
    def job(self):
        return self._job

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

    def __call__(self, **kwargs):
        return self._state.compute(self._job, **kwargs)

    def __getstate__(self):
        return {
            '_state': self._state,
            '_job': self._job,
        }

    def __setstate__(self, state):
        self._state = state['_state']
        self._job = state['_job']


class FileState:

    def __init__(self, scratch=None):
        if not scratch:
            scratch = tempfile.mkdtemp(prefix='rdm.')
        self._scratch = scratch

        logger.info(f'Memoizing jobs to {scratch}')

    def __contains__(self, job):
        return self.stored(job)

    def dir(self, job):
        job_repr = job.__shorthash__()
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

    def err_file(self, job):
        return os.path.join(self.dir(job), 'err.pkl')

    def erred(self, job):
        f = self.err_file(job)
        is_erred = os.path.isfile(f)
        logger.info(f'{job.__repr__()}: {f} is stored: {is_erred}')
        return is_erred

    def stored(self, job):
        f = self.state_file(job)
        is_stored = os.path.isfile(f)
        logger.info(f'{job.__repr__()}: {f} is stored: {is_stored}')
        return is_stored

    def err(self, job):
        if not self.erred(job):
            raise ValueError(f'Job {job} not erred.')

        with open(self.err_file(job), 'rb') as f:
            return cloudpickle.load(f)

    def compute(self, job, *args, **kwargs):
        logger_state.info(f'{job.__repr__()}: might compute')

        if self.erred(job):
            raise self.err(job)

        if self.stored(job):
            logger_state.info(f'{job.__repr__()}: loading stored')
            with open(self.state_file(job), 'rb') as f:
                return cloudpickle.load(f)

        logger_state.info(f'{job.__repr__()}: computing')
        with cwd(self.dir(job)):
            try:

                if not kwargs and len(args) > 0 and isinstance(args[0], types.GeneratorType):
                    kwargs = dict(args[0])

                state = job(**kwargs)
                with open(self.state_file(job), 'wb') as f:
                    cloudpickle.dump(state, f)
                logger_state.info(f'{job.__repr__()}: stored')
                return state
            except Exception as e:
                logger_state.info(f'{job.__repr__()}: err')
                with open(self.err_file(job), 'wb') as f:
                    cloudpickle.dump(e, f)
                raise e
