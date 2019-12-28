from dask import delayed


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