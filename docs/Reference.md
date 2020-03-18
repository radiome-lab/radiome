
# radiome.core
Top-level package for radiome.

## radiome.core.resource_pool


### Strategy
```python
Strategy(self, forks=None, **kwargs)
```


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


### StrategyResourcePool
```python
StrategyResourcePool(self, strategy: ResourceKey,
                     resource_pool: ResourcePool)
```

A non-safe resource pool proxy for a specific strategy.


## radiome.core.schema


### validate_spec
```python
validate_spec(module: module)
```

Check that a module has spec.yml file and the spec.yaml is valid.

Args:
    module: The module that has been imported.

Raises:
    FileNotFoundError: The spec.yml is not found.
    ValidationError: Errors in validating spec.yml file.


# radiome.core.execution


## radiome.core.execution.loader


## radiome.core.execution.executor


## radiome.core.execution.context


# radiome.core.utils


## radiome.core.utils.mocks


### NipypeJob
```python
NipypeJob(self, interface, reference=None)
```
Nipype job mock for testing.

Mock that emulates the behavior and APIs of NipypeJob, but do not execute the commandline of nipype jobs.
It will create fake outputs based on the outputs traits.



### mock_nipype
```python
mock_nipype()
```
Context manager which replaces Nipype job with mock at runtime.

Patch the nipype job with mocks at runtime, then recover it when exiting.


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

