import itertools
import os
import re
from collections import OrderedDict
from typing import Any, Union, List, Tuple, Set, Dict, Iterator

from radiome.utils import Hashable, s3


class Strategy(Hashable):
    KEYVAL_SEP = '-'
    FORK_SEP = '+'

    _KVS = re.escape(KEYVAL_SEP)
    _FS = re.escape(FORK_SEP)
    FORMAT = rf'[^{_KVS}{_FS}]+{_KVS}[^{_FS}]+({_FS}[^{_KVS}{_FS}]+{_KVS}[^{_FS}]+)*'
    del _KVS, _FS

    _forks: Dict[str, str]

    def __init__(self,
                 forks=None,
                 **kwargs):

        if isinstance(forks, str):
            if not re.match(Strategy.FORMAT, forks):
                raise ValueError(f'Forks should be in the format '
                                 f'"strat{Strategy.KEYVAL_SEP}value" '
                                 f'separated by {Strategy.FORK_SEP}, '
                                 f'provided: "{forks}"')
            forks = [
                tuple(strat.split(Strategy.KEYVAL_SEP, 1))
                for strat in forks.split(Strategy.FORK_SEP)
            ]
        else:
            forks = forks or {}
            items = forks.items() if isinstance(forks, dict) else forks
            forks = [
                (str(k), str(v))
                for k, v in items
            ]

        forks += [
            (str(k), str(v))
            for k, v in kwargs.items()
        ]

        self._forks = OrderedDict([
            (str(k), str(v))
            for k, v in forks
        ])

    @property
    def forks(self) -> Dict[str, str]:
        return OrderedDict(self._forks.items())

    def __hashcontent__(self) -> Any:
        return tuple(
            (k, v)
            for k, v in self._forks.items()
        )

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return Strategy.FORK_SEP.join([
            f'{k}{Strategy.KEYVAL_SEP}{v}'
            for k, v in self._forks.items()
        ])

    def __len__(self) -> int:
        return len(self._forks)

    def __bool__(self) -> bool:
        return len(self) > 0

    __nonzero__ = __bool__

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        return iter(self._forks.items())

    def __getitem__(self, key: str) -> str:
        return self._forks[key]

    def __add__(self, other: 'Strategy') -> 'Strategy':
        s = Strategy({})
        for k, v in self._forks.items():
            s._forks[k] = v
        for k, v in other._forks.items():
            s._forks[k] = v
        return s

    def __contains__(self, other: 'Strategy') -> bool:
        my_strat = self.forks
        other_strat = other.forks

        for k, v in other_strat.items():
            if k not in my_strat:
                continue
            if v != my_strat[k]:
                return False

        return True


class ResourceKey(Hashable):
    """Representation of a resource, matching BIDS specification.

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
    """

    KEYVAL_SEP = '-'
    ENTITY_SEP = '_'
    STRAT_SEP = '#'

    _KVS = re.escape(KEYVAL_SEP)
    _ES = re.escape(ENTITY_SEP)
    _SS = re.escape(STRAT_SEP)
    FORMAT = rf'([^{_KVS}{_ES}]+{_KVS}[^{_ES}{_SS}]+(_ES[^{_KVS}{_ES}]+{_KVS}[^{_ES}{_SS}]+)*)?([^{_KVS}{_ES}]+)?'

    supported_entities: List[str] = ['sub', 'ses', 'run', 'task', 'acq',
                                     'space', 'atlas', 'roi', 'label',
                                     'hemi', 'from', 'to', 'desc']

    valid_suffixes: List[str] = ['*', 'mask', 'bold', 'brain', 'T1w']

    branching_entities: List[str] = ['sub', 'ses', 'run', 'task']

    _suffix: str
    _strategy: Strategy
    _entities: Dict[str, str]
    _tags: Set[str]

    def __init__(self,
                 key: Union[str, Dict[str, str], 'ResourceKey', None] = None,
                 tags: Union[Set[str], None] = None,
                 **kwargs) -> None:

        """Initialize a ResourceKey instance, based on a previous key, a mapping
        of entities or a BIDS-valid string.

        Args:
            key: The content of the key. A ResourceKey might be provided and
                specific entities can be overwritten with kwargs.
                `*` can be used to use it as a filter
                `^` can be used to use it as a non-matching filter
            tags: Tags to mark resources
            **kwargs: Custom entities to overwrite entities from `key`.

        Examples:
            Examples should be written in doctest format, and should illustrate how
            to use the function.

            >>> acq_filter = ResourceKey('acq-*_T1w')
            >>> ResourceKey('acq-mprage_T1w') in acq_filter
            True

            >>> not_acq_filter = ResourceKey('acq-^_T1w')
            >>> ResourceKey('acq-mprage_T1w') in not_acq_filter
            False
        """

        entities = {}
        suffix = '*'
        tags = tags or set()
        strategy = Strategy()

        # initialize dictionary from a key
        if isinstance(key, str):
            if not re.match(ResourceKey.FORMAT, key):
                raise ValueError(f'Resource keys should be in the format "key{ResourceKey.KEYVAL_SEP}value" '
                                 f'separated by {ResourceKey.ENTITY_SEP}, provided: "{key}"')

            parsed_entities = key.split(ResourceKey.ENTITY_SEP)

            if ResourceKey.KEYVAL_SEP not in parsed_entities[-1]:
                parsed_entities, suffix = parsed_entities[:-1], parsed_entities[-1]

            for entity_pair in parsed_entities:
                key, value = entity_pair.split(ResourceKey.KEYVAL_SEP, 1)
                entities[key] = value

        # initialize from a dictionary or custom parameters
        elif isinstance(key, (dict, ResourceKey)):

            if isinstance(key, ResourceKey):
                suffix = key.suffix
                tags |= key.tags
                entities = key._entities.copy()
                strategy = key._strategy

            else:
                entities = {
                    str(k): v
                    for k, v in key.items()
                }

                if 'suffix' in entities:
                    suffix = entities['suffix']
                    del entities['suffix']

        if kwargs:
            suffix = kwargs.get('suffix', suffix)

            for kwargs_key, value in kwargs.items():
                if kwargs_key == 'suffix':
                    continue

                if value is None:
                    if kwargs_key in entities:
                        del entities[kwargs_key]
                else:
                    entities[kwargs_key] = value

        if suffix not in self.valid_suffixes:
            raise ValueError(f'Invalid suffix "{suffix}"')

        self._suffix = suffix
        self._entities = {}

        if 'desc' in entities:
            entities['desc'] = str(entities['desc'])
            if ResourceKey.STRAT_SEP in entities['desc']:
                entities['desc'], strategy = entities['desc'].split(ResourceKey.STRAT_SEP)
                strategy = Strategy(strategy)
            else:
                try:
                    strategy = Strategy(entities['desc'])
                    del entities['desc']
                except ValueError:
                    pass

        if 'strategy' in entities:
            strategy = Strategy(entities['strategy'])
            del entities['strategy']

        self._strategy = strategy

        for entity_key, value in entities.items():
            if entity_key not in self.supported_entities:
                raise KeyError(f'Entity "{entity_key}" is not supported '
                               f'by the resource pool')

            if not value:
                raise ValueError(f'Entity "{entity_key}" value '
                                 f'cannot be empty')

            self._entities[entity_key] = str(value)

        self._tags = {str(t) for t in tags}

    def __lt__(self, other: 'ResourceKey') -> bool:
        """Compare ResourceKeys based on quantity of entities and strategy.
        Earlier strategies (with less forks) are considered lesser than new
        strategies.

        Args:
            other: ResourceKey to be compared to.

        Returns:
            True if object is considered lesser than other.
            False otherwise.
        """
        if self.suffix != other.suffix:
            return self.suffix < other.suffix

        if self.strategy != other.strategy:

            other_strategy = other.strategy
            self_strategy_keys = set(self.strategy.keys())
            other_strategy_keys = set(other_strategy.keys())

            if not self_strategy_keys.issubset(other_strategy_keys) and \
                not other_strategy_keys.issubset(self_strategy_keys):
                raise ValueError(f'Strategy are not subsets: {self_strategy_keys} '
                                 f'and {other_strategy_keys}')

            return self.strategy < other.strategy

        other_entities = other.entities

        self_entities_keys = set(self._entities.keys())
        other_entities_keys = set(other_entities.keys())

        if not self_entities_keys.issubset(other_entities_keys) and \
            not other_entities_keys.issubset(self_entities_keys):
            raise ValueError(f'Entities are not subsets: {self_entities_keys} '
                             f'and {other_entities_keys}')

        for k, v in self._entities.items():
            if k not in other_entities:
                return False
            if v != other_entities[k]:
                return v < other_entities[k]

        return len(self._entities) < len(other_entities)

    def __hashcontent__(self) -> Any:
        """Create a reliable set of tuples and strings used
        to hash the key.
        """
        return (
            self._suffix,
            self._strategy.__hashcontent__(),
            tuple(
                (entity, self._entities[entity])
                for entity in self.supported_entities
                if entity in self._entities
            ),
            tuple(self._tags),
        )

    def __repr__(self) -> str:
        """Use __str__ representation as official repr"""
        return str(self)

    def __str__(self) -> str:
        """Create a string representation of the key.

        The representation is compatible with BIDS. It prepares
        the `desc` field in case that there is an strategy in place.
        """
        desc = ResourceKey.STRAT_SEP.join(filter(None, [
            self._entities.get('desc', ''),
            str(self._strategy)
        ]))
        if desc:
            desc = f'desc{ResourceKey.KEYVAL_SEP}{desc}'

        return ResourceKey.ENTITY_SEP.join(filter(None,
                                                  [
                                                      ResourceKey.KEYVAL_SEP.join([entity, self._entities[entity]])
                                                      for entity in self.supported_entities
                                                      if entity in self._entities and entity != 'desc'
                                                  ]
                                                  +
                                                  ([desc] if desc else [])
                                                  +
                                                  [self._suffix]
                                                  ))

    def keys(self) -> List[str]:
        """Get a list of keys of defined entities and strategy."""
        return \
            list(self._entities.keys()) + \
            ['suffix'] + \
            (['strategy'] if self._strategy else [])

    def __getitem__(self, item: str) -> str:
        """Retrieve an entity, the suffix, or an strategy.

        Args:
            item: Entity or specific property to retrieve

        Returns:
            String, in case of entities and suffix.
            Strategy, in case of `strategy` item.
        """

        if item == 'suffix':
            return self._suffix

        if item == 'strategy':
            return self._strategy

        if item not in self.supported_entities:
            raise KeyError(f'Entity {item} is not supported '
                           f'by the resource pool')

        return self._entities[item]

    def __contains__(self, key: Union[str, 'ResourceKey']) -> bool:
        """Assess if a key is a subset of it.

        It is the main method that allows a ResourceKey to be a filter.

        Returns:
            True, if `key` is a subset of `self`.
            False, otherwise.

        Examples:
            >>> ResourceKey('sub-001_T1w') in ResourceKey('sub-*_T1w')
            True

            >>> ResourceKey('sub-001_ses-001_T1w') in ResourceKey('sub-*_ses-^_T1w')
            False
        """

        key = ResourceKey(key)

        if self._suffix != '*' and self._suffix != key.suffix:
            return False

        for entity, value in self._entities.items():
            if value == '^':
                if entity in key._entities:
                    return False
            else:

                if entity not in key._entities:
                    continue

                if value == '*':
                    continue

                if value != key._entities[entity]:
                    return False

        my_strat = self.strategy
        key_strat = key.strategy

        if my_strat not in key_strat:
            return False

        if self.tags:
            if not key._tags:
                return False
            if not all(tag in key.tags for tag in self._tags):
                return False

        return True

    @property
    def suffix(self) -> str:
        """Retrieve the suffix."""
        return self._suffix

    @property
    def tags(self) -> Set[str]:
        """Retrieve a copy of the tags."""
        return self._tags.copy()

    @property
    def strategy(self) -> Strategy:
        """Retrieve the strategy. An empty strategy will be
        created if not set."""
        if not self._strategy:
            return Strategy({})

        return self._strategy

    @property
    def entities(self) -> Dict[str, str]:
        """Retrieve a copy of entities."""
        return self._entities.copy()

    def isfilter(self) -> bool:
        """Check if key is a filter.

        It will be considered a filter if it contains a quantifier.

        Returns:
            True, if an entity or suffix is a quantifier.
            False, otherwise.
        """
        return \
            any(
                v in ['*', '^']
                for v in self._entities.values()
            ) or \
            self._suffix == '*'

    def isbroad(self) -> bool:
        """Check if key is a broad key (*).

        Returns:
            True, if there is no entity and suffix matches all.
            False, otherwise.
        """
        return \
            len(self._entities) == 0 and \
            self._suffix == '*'


class Resource(Hashable):

    def __init__(self, content: Any):
        self._content = content

    def __copy__(self) -> 'Resource':
        return Resource(self._content)

    def __hashcontent__(self) -> Tuple:
        return self._content,

    def __str__(self) -> str:
        return f'Resource({self._content})'

    def __repr__(self) -> str:
        return f'Resource({self._content})'

    def __call__(self, **state: Any) -> Any:
        return self._content

    @property
    def content(self) -> Any:
        return self._content

    def dependencies(self) -> Dict[str, Any]:
        return {}


class FileResource(Resource):
    def __init__(self, content: str, working_dir: str = None, aws_cred_path: str = None):
        if content.lower().startswith("s3://"):
            if working_dir is None or not os.path.exists(working_dir):
                raise IOError(f'Cannot find the working directory {working_dir}')
            if aws_cred_path is not None and not os.path.isfile(aws_cred_path):
                raise IOError(f'Cannot find the cred {aws_cred_path}')
            super().__init__(content)
        elif os.path.isfile(content):
            super().__init__(content)
        else:
            raise IOError(f'Cannot find the file {content}')
        self._cwd = working_dir
        self._aws_cred_path = aws_cred_path
        self._cached = None

    def __call__(self, *args):
        if self.content.lower().startswith("s3://"):
            if self._cached is not None and os.path.exists(self._cached):
                return self._cached
            else:
                self._cached = s3.download_file(self.content, self._cwd, self._aws_cred_path)
                return self._cached
        else:
            return self.content


class InvalidResource(Resource):

    def __init__(self, resource: Resource, exception: Exception = None):
        self._resource = resource
        self._exception = exception
        self._content = None

    def __hashcontent__(self) -> Tuple:
        return self._resource, self._exception

    def __call__(self, **state: Any) -> Any:
        return self.content

    @property
    def content(self) -> Any:
        if self._exception:
            raise self._exception


class ResourcePool:
    _pool: Dict[ResourceKey, Resource]
    _pool_by_type: Dict[str, Dict[ResourceKey, Resource]]
    _pool_by_tag: Dict[str, Dict[ResourceKey, Resource]]
    _pool_branches: Dict[str, Set[str]]
    _pool_branched_resources: Dict[str, Set[ResourceKey]]

    def __init__(self):
        self._pool = {}
        self._pool_by_type = {}
        self._pool_by_tag = {}
        self._pool_branches = {
            entity: set()
            for entity in ResourceKey.branching_entities
        }
        self._pool_branched_resources = {
            entity: set()
            for entity in ResourceKey.branching_entities
        }

    def __iter__(self) -> Iterator[Tuple[ResourceKey, Resource]]:
        return iter(self._pool.items())

    def __contains__(self, key: ResourceKey) -> bool:
        for rp_key in self._pool:
            if rp_key in key:
                return True
        return False

    @property
    def raw(self):
        return self._pool

    def __getitem__(self, key: Union[ResourceKey, str, List[str]]) -> Union[Resource, Dict]:

        if isinstance(key, list):
            return self.extract(*key)

        if isinstance(key, ResourceKey):

            if key.isfilter():
                rp = ResourcePool()

                for rkey in self._pool:
                    if rkey not in key:
                        continue
                    rp[rkey] = self[rkey]

                return rp
                
            try:
                return self._pool[key]
            except KeyError:
                return self._pool[next(iter(sorted([
                    k
                    for k in self._pool
                    if k in key
                ], reverse=True)))]

        if key in self._pool_by_type:
            return self._pool_by_type[key]

        if key in self._pool_by_tag:
            return self._pool_by_tag[key]

        raise KeyError(f'Key "{key}" not find in suffixes or tags')

    def __setitem__(self, resource_key: Union[ResourceKey, str], resource: Resource) -> None:

        if not isinstance(resource_key, ResourceKey):
            resource_key = ResourceKey(str(resource_key))

        if resource_key.isfilter():
            raise KeyError(f'Resource key cannot be a filter: {resource_key}')

        if not isinstance(resource, Resource):
            resource = Resource(resource)

        self._pool[resource_key] = resource

        if resource_key['suffix'] not in self._pool_by_type:
            self._pool_by_type[resource_key['suffix']] = {}

        if resource_key in self._pool_by_type[resource_key['suffix']]:
            raise KeyError(f'Resource key {resource_key} already '
                           f'exists in the pool.')

        self._pool_by_type[resource_key['suffix']][resource_key] = resource

        cleaner = {en: None for en in ResourceKey.branching_entities}
        clean_resource_key = ResourceKey(
            resource_key,
            **cleaner
        )
        for entity in ResourceKey.branching_entities:
            if entity in resource_key.entities:
                self._pool_branches[entity].add(resource_key[entity])
                self._pool_branched_resources[entity].add(clean_resource_key)

        for flag in resource_key.tags:
            if flag not in self._pool:
                self._pool_by_tag[flag] = {}
            self._pool_by_tag[flag][resource_key] = resource

    def extract(self, *resources: Union[ResourceKey, str]):

        extracted_resources = {}
        strategies = {}

        resources = [ResourceKey(r) for r in resources]

        too_broad_resources = [r for r in resources if r.isbroad()]
        if too_broad_resources:
            raise KeyError(f'Extracted resource keys too broad: {too_broad_resources}')

        for resource in resources:
            extracted_resources[resource] = [
                r for r in self._pool if r in resource
            ]

            for matching in extracted_resources[resource]:
                for strategy, name in matching.strategy:
                    if strategy not in strategies:
                        strategies[strategy] = set()
                    strategies[strategy].add(name)

        # Branching
        expected_branching_keys = [
            b for b in self._pool_branches
            if

            # there is branching in this entity
            self._pool_branches[b] and

            # all resource selectors for this entity are not wildcards
            all(
                b not in resource.entities or resource[b] != '*'
                for resource in resources
            ) and

            # there is at least one selected resource that uses this branch
            any(
                any(resource in b for b in self._pool_branched_resources[b])
                for resource in resources
            )
        ]
        expected_branching_values_set = [
            self._pool_branches[b] for b in expected_branching_keys
        ]

        strategies_keys, strategies_values_set = list(strategies.keys()), list(strategies.values())

        for grouping_values in itertools.product(*expected_branching_values_set, *strategies_values_set):

            branching_values = grouping_values[:len(expected_branching_keys)]
            strategies_values = grouping_values[len(expected_branching_keys):]

            expected_branching = dict(zip(expected_branching_keys, branching_values))

            strategy_combination = Strategy(zip(strategies_keys, strategies_values))

            expected_strategy_combination = {}
            if strategy_combination:
                expected_strategy_combination['strategy'] = strategy_combination

            strategy_key = ResourceKey(
                **expected_strategy_combination,
                **expected_branching,
                suffix='*'
            )

            extracted_resource_pool = ResourcePool()

            for resource, extracted in extracted_resources.items():

                expected_resource_unbranching = {
                    b: '*' for b in ResourceKey.branching_entities
                    if b in resource.entities and resource[b] == '*'
                }

                resource_filter = ResourceKey(
                    resource,
                    strategy=strategy_combination or None,
                    **expected_branching,
                    **expected_resource_unbranching
                )

                strategy_extracted_resources = [
                    e for e in extracted if e in resource_filter
                ]

                if strategy_extracted_resources:

                    for strategy_extracted_resource in strategy_extracted_resources:

                        # replace wildcard with the actual value of branching
                        branched_resource = strategy_extracted_resource
                        if branched_resource in extracted_resource_pool.raw:
                            if self[strategy_extracted_resource] != extracted_resource_pool[branched_resource]:
                                raise ValueError(f'There was an error extracting the resource {branched_resource}: '
                                                 f'Adressing different resources: {self[strategy_extracted_resource]} '
                                                 f'and {extracted_resource_pool[branched_resource]}')
                            continue

                        extracted_resource_pool[branched_resource] = self[strategy_extracted_resource]

                else:
                    break

            if all(e in extracted_resource_pool for e in extracted_resources):
                expected_strategy_combination = {}
                if strategy_combination:
                    expected_strategy_combination['strategy'] = strategy_combination
                strategy_key = ResourceKey(
                    **expected_strategy_combination,
                    **expected_branching,
                    suffix='*'
                )
                yield strategy_key, StrategyResourcePool(strategy_key, self)

            # """


class StrategyResourcePool:
    """
    A non-safe resource pool proxy for a specific strategy.
    """

    def __init__(self, strategy: ResourceKey, resource_pool: ResourcePool):
        self._strategy = strategy
        self._reference_pool = resource_pool

    def _map(self, resource_key: ResourceKey) -> ResourceKey:
        if isinstance(resource_key, list):
            return [self._map(k) for k in resource_key]

        if not isinstance(resource_key, ResourceKey):
            return resource_key

        new_key = {
            **self._strategy,
            **resource_key,
        }

        new_key_strat = self._strategy.strategy + resource_key.strategy
        if new_key_strat:
            new_key['strategy'] = new_key_strat

        return ResourceKey(
            **new_key
        )

    def __iter__(self) -> Iterator[Tuple[ResourceKey, Resource]]:
        return iter(
            (k, v) for k, v in self._reference_pool.items()
            if k in self._strategy
        )

    def __contains__(self, key: ResourceKey) -> bool:
        return self._reference_pool.__contains__(self._map(key))

    def __getitem__(self, key: Union[ResourceKey, str, List[str]]) -> Union[Resource, Dict]:
        return self._reference_pool.__getitem__(self._map(key))

    def __setitem__(self, resource_key: ResourceKey, resource: Resource) -> None:
        return self._reference_pool.__setitem__(self._map(resource_key), resource)


R = ResourceKey
