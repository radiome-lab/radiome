# core.execution package

## Subpackages


* core.execution.nipype package


    * Module contents


## Submodules

## core.execution.executor module


### class core.execution.executor.DaskExecution(client=None)
Bases: `core.execution.executor.Execution`


#### execute(graph)

#### execute_subgraph(SG)

### class core.execution.executor.Execution()
Bases: `object`


#### execute(graph)

### exception core.execution.executor.MissingDependenciesException()
Bases: `Exception`


### core.execution.executor.cloudpickle_dumps(x)

### core.execution.executor.cloudpickle_loads(header, frames)
## core.execution.job module


### class core.execution.job.ComputedResource(job, field=None)
Bases: `core.execution.job.Job`, `radiome.core.resource_pool.Resource`


#### property output_name()

### class core.execution.job.FakeJob(job)
Bases: `core.execution.job.Job`


### class core.execution.job.Job(reference=None)
Bases: `radiome.core.utils.Hashable`


#### dependencies()

#### resources()

### class core.execution.job.PythonJob(function, reference=None)
Bases: `core.execution.job.Job`

## core.execution.loader module


### core.execution.loader.load(item: str)
Load a module through full name or github url.

Args:

    item: Full name or github url for the module.

Returns:

    A “create_workflow” callable.

Raises:

    ValueError: The imported module doesn’t have a create_workflow callable.

## core.execution.utils module


### core.execution.utils.cwd(new_dir)
## Module contents


### class core.execution.DependencySolver(resource_pool, output_dir='.', work_dir='.')
Bases: `object`


#### execute(executor=None)

#### property graph()

### class core.execution.State(work_dir, resource)
Bases: `radiome.core.utils.Hashable`


#### resources()
