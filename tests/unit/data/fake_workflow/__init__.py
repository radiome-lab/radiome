from radiome.core.jobs import PythonJob
from radiome.core.resource_pool import Resource


def create_workflow(config, resource_pool, context):
    func = PythonJob(function=lambda x: {
        'y': x
    })
    func.x = Resource(config['msg'])
    resource_pool['T1w'] = func.y
    return 'test'
