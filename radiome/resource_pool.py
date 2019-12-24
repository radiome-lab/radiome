from typing import Union, List, Set, Dict, OrderedDict as OrderedDictType, overload
from collections import OrderedDict
import itertools
import re


class Strategy:

    _forks: OrderedDictType[str, str]

    def __init__(self,
                 forks=None,
                 **kwargs):

        if isinstance(forks, str):
            if not re.match(r'[^-+]+-[^+]+(\+[^-+]+-[^+]+)*', forks):
                raise ValueError(f'Forks should be in the format "strat-value" '
                                 f'separated by +, provided: "{forks}"')
            forks = [
                (k, v)
                for k, v in [
                    strat.split('-', 1)
                    for strat in forks.split('+')
                ]
            ]
        else:
            forks = forks or {}
            forks = [
                (str(k), str(v))
                for k, v in forks.items()
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
    def forks(self):
        return OrderedDict([
            (k, v)
            for k, v in self._forks.items()
        ])

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __str__(self):
        return '+'.join([
            f'{k}-{v}'
            for k, v in self._forks.items()
        ])

    def __add__(self, other):
        s = Strategy({})
        for k, v in self._forks.items():
            s._forks[k] = v
        for k, v in other._forks.items():
            s._forks[k] = v
        return s

    def __len__(self):
        return len(self._forks)

    def __iter__(self):
        return iter(self._forks.items())

class ResourceKey:

    supported_entities: List[str] = ['sub', 'ses', 'run', 'task',
                                     'space', 'atlas', 'roi', 'label',
                                     'hemi', 'from', 'to', 'desc']
    valid_suffixes: List[str] = ['*', 'mask', 'bold', 'brain', 'T1w']

    branching_entities: List[str] = ['sub', 'ses', 'run', 'task']

    _suffix: str
    _strategy: Strategy
    _entities: Dict[str, str]
    _tags: Set[str]

    def __init__(self,
                 entity_dictionary: Union[str, Dict[str, str], None] = None,
                 tags: Union[Set[str], None] = None,
                 **kwargs) -> None:

        entities = {}
        suffix = '*'
        tags = tags or set()
        strategy = Strategy()

        # initialize dictionary from a key
        if isinstance(entity_dictionary, str):
            parsed_entities = entity_dictionary.split('_')

            if '-' not in parsed_entities:
                parsed_entities, suffix = parsed_entities[:-1], parsed_entities[-1]

            for entity_pair in parsed_entities:
                key, value = entity_pair.split('-', 1)
                entities[key] = value

        # initialize from a dictionary or custom parameters
        elif isinstance(entity_dictionary, (dict, ResourceKey)):

            if isinstance(entity_dictionary, ResourceKey):
                suffix = entity_dictionary.suffix
                tags |= entity_dictionary.tags
                entities = {
                    str(k): str(v)
                    for k, v in entity_dictionary._entities.items()
                }
                strategy = entity_dictionary._strategy

            else:
                entities = {
                    str(k): str(v)
                    for k, v in entity_dictionary.items()
                }

                if 'suffix' in entities:
                    suffix = entities['suffix']
                    del entities['suffix']

        if kwargs:
            suffix = kwargs.get('suffix', suffix)

            for key, value in kwargs.items():
                if key == 'suffix':
                    continue

                if value is None:
                    if key in entities:
                        del entities[key]
                else:
                    entities[key] = str(value)

        if suffix not in self.valid_suffixes:
            raise ValueError(f'Invalid suffix "{suffix}"')

        self._suffix = suffix
        self._entities = {}

        if 'desc' in entities:
            try:
                strategy = Strategy(entities['desc'])
                del entities['desc']
            except ValueError:
                pass

        self._strategy = strategy

        for key, value in entities.items():
            if key not in self.supported_entities:
                raise KeyError(f'Entity {key} is not supported by '
                               f'the resource pool')

            if not value:
                raise ValueError(f'Entity value cannot '
                                 f'be empty: "{value}"')

            self._entities[key] = value

        self._tags = {str(t) for t in tags}

    def __lt__(self, other):
        if self.suffix != other.suffix:
            return self.suffix < other.suffix

        if self.strategy != other.strategy:
            return self.strategy < other.strategy

        other_entities = other.entities
        for k, v in self._entities:
            if k not in other_entities:
                return -1
            elif v != other_entities[k]:
                return v < other_entities[k]

        return len(self._entities) < len(other_entities)

    def __call__(self, resouce_pool):
        return StrategyResourcePool(self, resouce_pool)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.__str__())

    def __str__(self):
        return '_'.join(filter(None,
            [
                '-'.join([entity, self._entities[entity]])
                for entity in self.supported_entities
                if entity in self._entities and entity != 'desc'
            ]
            +
            (['desc-' + str(self._strategy)] if len(self._strategy) > 0 else [])
            +
            [self._suffix]
        ))

    def keys(self):
        return list(self._entities.keys()) + ['desc', 'suffix']

    def __getitem__(self, item):

        if item == 'suffix':
            return self._suffix

        if item == 'desc':
            return self._strategy

        if item not in self.supported_entities:
            raise KeyError(f'Entity {item} is not supported '
                           f'by the resource pool')

        return self._entities[item]

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __contains__(self, key):

        if isinstance(key, ResourceKey):

            if self._suffix != '*' and self._suffix != key.suffix:
                return False

            for entity, value in self._entities.items():
                if entity == 'desc':
                    continue

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

            if 'desc' in key.entities and 'desc' in self._entities:

                if key.entities['desc'] == '^':
                    if 'desc' in key._entities:
                        return False

                elif 'desc' not in key._entities:
                    return True

                my_strat = self.strategy
                key_strat = key.strategy

                for k, v in key_strat.items():
                    if k not in my_strat:
                        continue
                    if v != my_strat[k]:
                        return False

            if self.tags:
                if not key._tags:
                    return False
                if not all(tag in key.tags for tag in self._tags):
                    return False

            return True

        elif isinstance(key, str):
            return key in self._entities

        return False

    @property
    def suffix(self):
        return self._suffix

    @property
    def tags(self):
        return {t for t in self._tags}

    @property
    def strategy(self):
        if not self._strategy:
            return Strategy({})

        return self._strategy

    @property
    def entities(self):
        return {
            k: v
            for k, v in self._entities.items()
        }

    @staticmethod
    def from_key(key):
        if isinstance(key, ResourceKey):
            return key

        return ResourceKey(key)

    def isfilter(self):
        return \
            any(
                v == '*'
                for v in self._entities.values()
            ) or \
            self._suffix == '*'

    def isbroad(self):
        return \
            len(self._entities) == 0 and \
            self._suffix == '*'


class Resource:
    def __init__(self, key, content):
        self._key = key
        self._content = content

    def __copy__(self):
        return Resource(self._key, self._content)


class ComputedResource(Resource):
    pass


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

    def __iter__(self):
        return iter(self._pool.items())

    def __contains__(self, key: ResourceKey) -> bool:
        for rp_key in self._pool.keys():
            if rp_key in key:
                return True
        return False

    def __getitem__(self, key: Union[ResourceKey, str, List[str]]) -> Union[Resource, Dict]:

        if isinstance(key, list):
            return self.extract(*key)

        if isinstance(key, ResourceKey):
            try:
                return self._pool[key]
            except KeyError:
                return self._pool[next(iter(sorted([
                    k
                    for k in self._pool.keys()
                    if k in key
                ], reverse=True)))]

        if key in self._pool_by_type:
            return self._pool_by_type[key]

        if key in self._pool_by_tag:
            return self._pool_by_tag[key]

        raise KeyError(f'Key "{key}" not find in suffixes or tags')

    def __setitem__(self, resource_key: ResourceKey, resource: Resource) -> None:

        if not isinstance(resource_key, ResourceKey):
            resource_key = ResourceKey(str(resource_key))

        if resource_key.isfilter():
            raise KeyError(f'Resource key cannot be a filter: {resource_key}')

        if not isinstance(resource, Resource):
            resource = Resource(resource_key, resource)
        else:
            resource = resource.__copy__()
            resource._key = resource_key

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
            if entity in resource_key:
                self._pool_branches[entity].add(resource_key[entity])
                self._pool_branched_resources[entity].add(clean_resource_key)

        for flag in resource_key.tags:
            if flag not in self._pool:
                self._pool_by_tag[flag] = {}
            self._pool_by_tag[flag][resource_key] = resource

    def extract(self, *resources):

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
                    b not in resource or resource[b] != '*'
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

            strategy_combination = '+'.join([
                '-'.join([k, v])
                for k, v
                in zip(strategies_keys, strategies_values)
            ])

            extracted_resource_pool = ResourcePool()

            for resource, extracted in extracted_resources.items():

                expected_resource_unbranching = {
                    b: '*' for b in ResourceKey.branching_entities
                    if b in resource and resource[b] == '*'
                }

                resource_filter = ResourceKey(
                    resource,
                    desc=strategy_combination or None,
                    **expected_branching,
                    **expected_resource_unbranching
                )

                strategy_extracted_resources = [
                    e for e in extracted if e in resource_filter
                ]

                if strategy_extracted_resources:

                    for strategy_extracted_resource in strategy_extracted_resources:

                        # replace wildcard with the actual value of branching
                        branched_resource = ResourceKey(
                            resource,
                            suffix=strategy_extracted_resource.suffix,
                            **{
                                **{
                                    bk: bv if bv != "*" else strategy_extracted_resource[bk]
                                    for bk, bv in {**expected_resource_unbranching, **expected_branching}.items()
                                    if bk in strategy_extracted_resource
                                },
                                **{
                                    k: v
                                    for k, v in strategy_extracted_resource.entities.items()
                                    if k in resource
                                }
                            }
                        )

                        if branched_resource in extracted_resource_pool:
                            if self[strategy_extracted_resource] != extracted_resource_pool[branched_resource]:
                                raise ValueError(f'There was an error extracting the resource {branched_resource}: '
                                                 f'Adressing different resources: {self[strategy_extracted_resource]} '
                                                 f'and {extracted_resource_pool[branched_resource]}')
                            continue

                        extracted_resource_pool[branched_resource] = self[strategy_extracted_resource]

                else:
                    break

            # Assert strategy has all the resources required
            if all(e in extracted_resource_pool for e in extracted_resources):
                expected_strategy_combination = {}
                if strategy_combination:
                    expected_strategy_combination['desc'] = strategy_combination
                strategy_key = ResourceKey(
                    **expected_strategy_combination,
                    **expected_branching,
                    suffix='*'
                )
                yield strategy_key, StrategyResourcePool(strategy_key, extracted_resource_pool)


class StrategyResourcePool:

    def __init__(self, strategy, resource_pool):
        self._strategy = strategy
        self._reference_pool = resource_pool

    def _map(self, resource_key):
        if type(resource_key) is list:
            return [self._map(k) for k in resource_key]

        if not isinstance(resource_key, ResourceKey):
            return resource_key

        return ResourceKey(
            resource_key,
            **self._strategy.entities
            desc=self._strategy.strategy + resource_key.strategy
        )

    def __iter__(self):
        return iter(
            (k, v) for k, v in self._reference_pool.items()
            if k in self._strategy
        )

    def __contains__(self, key: ResourceKey) -> bool:
        return self._reference_pool.__contains__(self._map(key))

    def __getitem__(self, key: Union[ResourceKey, str, List[str]]) -> Union[Resource, Dict]:
        return self._reference_pool.__getitem__(self._map(key))

    def __setitem__(self, resource_key: ResourceKey, resource: Resource) -> None:
        return self._reference_pool.__setitem__(self._map(key), resource)
