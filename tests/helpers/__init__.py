
class StateProfiler():

    def __init__(self, state):
        self._state = state
        self._count = {
            'dir': {},
            'state': {},
            'state_file': {},
            'stored': {},
            'compute': {},
        }

    def __getitem__(self, item):
        return self._state[item]

    def __contains__(self, job):
        return job in self._state

    def dir(self, job):
        self._count['dir'][job.__str__()] = self._count['dir'].get(job.__str__(), 0) + 1
        return self._state.dir(job)

    def state(self, job):
        self._count['state'][job.__str__()] = self._count['state'].get(job.__str__(), 0) + 1
        return self._state.state(job)

    def state_file(self, job):
        self._count['state_file'][job.__str__()] = self._count['state_file'].get(job.__str__(), 0) + 1
        return self._state.state_file(job)

    def stored(self, job):
        self._count['stored'][job.__str__()] = self._count['stored'].get(job.__str__(), 0) + 1
        return self._state.stored(job)

    def compute(self, job, **kwargs):
        self._count['compute'][job.__str__()] = self._count['compute'].get(job.__str__(), 0) + 1
        return self._state.compute(job, **kwargs)