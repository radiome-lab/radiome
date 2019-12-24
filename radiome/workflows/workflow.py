


class Workflow:

    def __init__(self):
        pass

    def __call__(self, resource_pool):

        for key, resource in resource_pool:

            # generate graph
            # check required/not-computed dependencies
            # generate thinner graph
            pass

class Job:

    _name = ''
    _inputs = {}

    def __init__(self, name):
        self._name = name
        self._inputs = {}