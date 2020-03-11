# core package

## Subpackages


* core.execution package


    * Subpackages


        * core.execution.nipype package


            * Module contents


    * Submodules


    * core.execution.executor module


    * core.execution.job module


    * core.execution.loader module


    * core.execution.utils module


    * Module contents


* core.utils package


    * Submodules


    * core.utils.bids module


    * core.utils.mocks module


    * core.utils.s3 module


    * Module contents


## Submodules

## core.cli module


### core.cli.build_context(args)

### core.cli.main(args=None)

### core.cli.parse_args(args)

### core.cli.print_info()
## core.pipeline module


### class core.pipeline.Context(working_dir: Union[str, os.PathLike], inputs_dir: Union[str, os.PathLike, radiome.core.utils.s3.S3Resource], outputs_dir: Union[str, os.PathLike, radiome.core.utils.s3.S3Resource], participant_label: List, n_cpus: int, memory: int, save_working_dir: bool, pipeline_config: Dict)
Bases: `object`


#### inputs_dir(: Union[str, os.PathLike, S3Resource] = None)

#### memory(: int = None)

#### n_cpus(: int = None)

#### outputs_dir(: Union[str, os.PathLike, S3Resource] = None)

#### participant_label(: List = None)

#### pipeline_config(: Dict = None)

#### save_working_dir(: bool = None)

#### working_dir(: Union[str, os.PathLike] = None)

### core.pipeline.build(context: core.pipeline.Context, \*\*kwargs)

### core.pipeline.load_resource(resource_pool: radiome.core.resource_pool.ResourcePool, context: core.pipeline.Context)
## core.resource_pool module


### class core.resource_pool.InvalidResource(resource: core.resource_pool.Resource, exception: Exception = None)
Bases: `core.resource_pool.Resource`


#### property content()

### core.resource_pool.R()
alias of `core.resource_pool.ResourceKey`


### class core.resource_pool.Resource(content: Any)
Bases: `radiome.core.utils.Hashable`


#### property content()

#### dependencies()

### class core.resource_pool.ResourceKey(key: Union[str, Dict[str, str], ResourceKey, None] = None, tags: Optional[Set[str]] = None, \*\*kwargs)
Bases: `radiome.core.utils.Hashable`

Representation of a resource, matching BIDS specification.

Stores information contained in BIDS naming specs.
E.g. sub-001_ses-001_T1w.nii.gz

Entities are the key-value information encoded in the format
key-value in the file name.

The suffix is the last part of the name, after the last underscore.

Strategy is specific to radiome, and it is encoded in the desc entity,
in the format desc-strategy in which strategy is encoded as key-value
separated by +. E.g. desc-skullstripping-afni+registration-ants
In case there is an actual value for this entity, the strategy will
be encoded as key-value#strategy.

The resource key object can work as a filter, in case an entity of suffix
is a quantifier: \* and ^


#### ENTITY_SEP( = '_')

#### FORMAT( = '([^\\\\-_]+\\\\-[^_\\\\#]+(_ES[^\\\\-_]+\\\\-[^_\\\\#]+)\*)?([^\\\\-_]+)?')

#### KEYVAL_SEP( = '-')

#### STRAT_SEP( = '#')

#### branching_entities(: List[str] = ['sub', 'ses', 'run', 'task'])

#### property entities()
Retrieve a copy of entities.


#### isbroad()
Check if key is a broad key (\*).

Returns:

    True, if there is no entity and suffix matches all.
    False, otherwise.


#### isfilter()
Check if key is a filter.

It will be considered a filter if it contains a quantifier.

Returns:

    True, if an entity or suffix is a quantifier.
    False, otherwise.


#### keys()
Get a list of keys of defined entities and strategy.


#### property strategy()
Retrieve the strategy. An empty strategy will be
created if not set.


#### property suffix()
Retrieve the suffix.


#### supported_entities(: List[str] = ['sub', 'ses', 'run', 'task', 'acq', 'space', 'atlas', 'roi', 'label', 'hemi', 'from', 'to', 'desc'])

#### property tags()
Retrieve a copy of the tags.


#### valid_suffixes(: List[str] = ['\*', 'mask', 'bold', 'brain', 'T1w'])

### class core.resource_pool.ResourcePool()
Bases: `object`


#### extract(\*resources: Union[core.resource_pool.ResourceKey, str])

#### property raw()

### class core.resource_pool.Strategy(forks=None, \*\*kwargs)
Bases: `radiome.core.utils.Hashable`


#### FORK_SEP( = '+')

#### FORMAT( = '[^\\\\-\\\\+]+\\\\-[^\\\\+]+(\\\\+[^\\\\-\\\\+]+\\\\-[^\\\\+]+)\*')

#### KEYVAL_SEP( = '-')

#### property forks()

### class core.resource_pool.StrategyResourcePool(strategy: core.resource_pool.ResourceKey, resource_pool: core.resource_pool.ResourcePool)
Bases: `object`

A non-safe resource pool proxy for a specific strategy.

## core.schema module


### exception core.schema.ValidationError()
Bases: `Exception`


### core.schema.steps(config: dict)

### core.schema.validate(config: dict)

### core.schema.validate_inputs(current_file, config: dict)
## Module contents

Top-level package for radiome.
