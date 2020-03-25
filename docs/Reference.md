
# radiome.core
Top-level package for radiome.

## radiome.core.resource_pool


### Strategy
```python
Strategy(self, forks=None, **kwargs)
```


#### FORK_SEP


#### FORMAT


#### KEYVAL_SEP


### ResourceKey
```python
ResourceKey(
    self,
    key:
    typing.Union[str, typing.Dict[str, str], ForwardRef('ResourceKey'), NoneType] = None,
    tags: typing.Union[typing.Set[str], NoneType] = None,
    **kwargs)
```
Representation of a resource, matching BIDS specification.

Stores information contained in BIDS naming specs.
E.g. `sub-001_ses-001_T1w.nii.gz`

Entities are the key-value information encoded in the format
`key-value` in the file name.

The suffix is the last part of the name, after the last underscore.

Strategy is specific to radiome, and it is encoded in the `desc` entity,
in the format `desc-strategy` in which strategy is encoded as `key-value`
separated by `+`. E.g. `desc-skullstripping-afni+registration-ants`
In case there is an actual value for this entity, the strategy will
be encoded as `key-value#strategy`.

The resource key object can work as a filter, in case an entity of suffix
is a quantifier: * and ^


#### branching_entities


#### entities
Retrieve a copy of entities.

#### ENTITY_SEP


#### FORMAT


#### KEYVAL_SEP


#### STRAT_SEP


#### strategy
Retrieve the strategy. An empty strategy will be
created if not set.

#### suffix
Retrieve the suffix.

#### supported_entities


#### tags
Retrieve a copy of the tags.

#### valid_suffixes


#### keys
```python
ResourceKey.keys()
```
Get a list of keys of defined entities and strategy.

#### isfilter
```python
ResourceKey.isfilter()
```
Check if key is a filter.

It will be considered a filter if it contains a quantifier.

Returns:
    True, if an entity or suffix is a quantifier.
    False, otherwise.


#### isbroad
```python
ResourceKey.isbroad()
```
Check if key is a broad key (*).

Returns:
    True, if there is no entity and suffix matches all.
    False, otherwise.


### ResourceKey
```python
ResourceKey(
    self,
    key:
    typing.Union[str, typing.Dict[str, str], ForwardRef('ResourceKey'), NoneType] = None,
    tags: typing.Union[typing.Set[str], NoneType] = None,
    **kwargs)
```
Representation of a resource, matching BIDS specification.

Stores information contained in BIDS naming specs.
E.g. `sub-001_ses-001_T1w.nii.gz`

Entities are the key-value information encoded in the format
`key-value` in the file name.

The suffix is the last part of the name, after the last underscore.

Strategy is specific to radiome, and it is encoded in the `desc` entity,
in the format `desc-strategy` in which strategy is encoded as `key-value`
separated by `+`. E.g. `desc-skullstripping-afni+registration-ants`
In case there is an actual value for this entity, the strategy will
be encoded as `key-value#strategy`.

The resource key object can work as a filter, in case an entity of suffix
is a quantifier: * and ^


#### branching_entities


#### entities
Retrieve a copy of entities.

#### ENTITY_SEP


#### FORMAT


#### KEYVAL_SEP


#### STRAT_SEP


#### strategy
Retrieve the strategy. An empty strategy will be
created if not set.

#### suffix
Retrieve the suffix.

#### supported_entities


#### tags
Retrieve a copy of the tags.

#### valid_suffixes


#### keys
```python
ResourceKey.keys()
```
Get a list of keys of defined entities and strategy.

#### isfilter
```python
ResourceKey.isfilter()
```
Check if key is a filter.

It will be considered a filter if it contains a quantifier.

Returns:
    True, if an entity or suffix is a quantifier.
    False, otherwise.


#### isbroad
```python
ResourceKey.isbroad()
```
Check if key is a broad key (*).

Returns:
    True, if there is no entity and suffix matches all.
    False, otherwise.


### StrategyResourcePool
```python
StrategyResourcePool(self, strategy: ResourceKey,
                     resource_pool: ResourcePool)
```

A non-safe resource pool proxy for a specific strategy.


## workflow
```python
workflow(validate_inputs: bool = True, use_attr: bool = True)
```

Decorator for a workflow. Control the behavior of create_workflow.

Args:
    validate_inputs: Validate inputs against the schema in spec.yml.
    use_attr: Use AttrDict instead of regular dicts. Retrieve values via attribute.

Returns:
    Should use as a decorator, return a decorated function.



## radiome.core.context


### Context
```python
Context(self, working_dir: typing.Union[str, os.PathLike], inputs_dir:
        typing.Union[str, os.PathLike, radiome.core.utils.s3.S3Resource],
        outputs_dir:
        typing.Union[str, os.PathLike, radiome.core.utils.s3.S3Resource],
        participant_label: typing.List, n_cpus: int, memory: int,
        save_working_dir: bool, pipeline_config: typing.Dict,
        diagnostics: bool)
```
Context(working_dir: Union[str, os.PathLike], inputs_dir: Union[str, os.PathLike, radiome.core.utils.s3.S3Resource], outputs_dir: Union[str, os.PathLike, radiome.core.utils.s3.S3Resource], participant_label: List, n_cpus: int, memory: int, save_working_dir: bool, pipeline_config: Dict, diagnostics: bool)

# radiome.core.jobs


## radiome.core.jobs.job


### PythonJob
```python
PythonJob(self, function, reference=None)
```
Radiome job for Python functions.

This job is to set up Python function in the steps of a workflow. Inputs of function should be
set using attributes. Python functions must return a dict, which is mapping from names to values.



### ComputedResource
```python
ComputedResource(self, job, field=None)
```
Represents the future result from a job, but not the true result.

ComputedResource stores information that is needed to compute the result, but not the result itself.
It can be used as inputs of other jobs and thus create a connection between jobs.



### NipypeJob
```python
NipypeJob(self, interface: BaseInterface, reference=None)
```
Radiome job for nipype interfaces,

NipypeJob is a uniform wrapper for all nipype interfaces such that nipype interfaces
can receive results from or become inputs of other jobs.



# radiome.core.utils


## radiome.core.utils.mocks


### NipypeJob
```python
NipypeJob(self, interface, reference=None)
```
Nipype jobs mock for testing.

Mock that emulates the behavior and APIs of NipypeJob, but do not execute the commandline of nipype jobs.
It will create fake outputs based on the outputs traits.



### mock_nipype
```python
mock_nipype()
```
Context manager which replaces Nipype jobs with mock at runtime.

Patch the nipype jobs with mocks at runtime, then recover it when exiting.


## radiome.core.utils.s3


### S3Resource
```python
S3Resource(self,
           content: str,
           working_dir: str,
           aws_cred_path: str = None,
           aws_cred_profile: str = None)
```
Amazon AWS S3 Resource.

An representation of S3 resource. It is bind to a specific s3 bucket url and credentials.
Once the resource is initialized, files can be downloaded, cached and uoloaded to this
bucket.



#### upload
```python
S3Resource.upload(path)
```

Upload path to the S3 bucket.

Args:
    path: The source directory.


#### walk
```python
S3Resource.walk()
```

Iterate the S3 bucket, the behavior is the same as os.walk.

