from types import MappingProxyType
from typing import Union, List, Set, Dict, OrderedDict as OrderedDictType
from collections import OrderedDict
import itertools
import re


class Strategy:
    __forks: OrderedDictType[str, str]

    def __init__(self,
                 forks,
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
            forks += [
                (str(k), str(v))
                for k, v in forks.items()
            ]

        forks += [
            (str(k), str(v))
            for k, v in kwargs.items()
        ]

        self.__forks = OrderedDict([
            (str(k), str(v))
            for k, v in forks
        ])

    @property
    def forks(self):
        return OrderedDict([
            (k, v)
            for k, v in self.__forks.items()
        ])

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __str__(self):
        return '-'.join([
            f'{k}-{v}'
            for k, v in self.__forks.items()
        ])


class ResourceKey:

    supported_entities: List[str] = ['sub', 'ses', 'run',
                                     'space', 'atlas', 'roi', 'label',
                                     'hemi', 'from', 'to', 'desc']
    valid_suffixes: List[str] = ['*', 'mask', 'bold', 'T1w']

    branching_entities: List[str] = ['sub', 'ses', 'run']

    __suffix: str
    __strategy: Strategy
    __entities: Dict[str, str]
    __tags: Set[str]

    def __init__(self,
                 entity_dictionary: Union[str, Dict[str, str], None] = None,
                 tags: Union[Set[str], None] = None,
                 **kwargs) -> None:

        entities = {}
        suffix = '*'
        tags = tags or set()

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
                    for k, v in entity_dictionary.__entities.items()
                }

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

        self.__suffix = suffix
        self.__entities = {}

        self.__strategy = None
        if 'desc' in entities:
            try:
                self.__strategy = Strategy(entities['desc'])
            except ValueError:
                pass

        for key, value in entities.items():
            if key not in self.supported_entities:
                raise KeyError(f'Entity {key} is not supported by '
                               f'the resource pool')

            if not value:
                    raise ValueError(f'Entity value cannot '
                                     f'be empty: "{value}"')

            self.__entities[key] = value

        self.__tags = {str(t) for t in tags}

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.__str__())

    def __str__(self):
        return '_'.join(filter(None,
            [
                '-'.join([entity, self.__entities[entity]])
                for entity in self.supported_entities
                if entity in self.__entities and entity != 'desc'
            ]
            +
            ([str(self.__strategy)] if self.__strategy else [])
            +
            [self.__suffix]
        ))

    def __getitem__(self, item):

        if item == 'suffix':
            return self.__suffix

        if item == 'desc':
            return self.__strategy

        if item not in self.supported_entities:
            raise KeyError(f'Entity {item} is not supported '
                           f'by the resource pool')

        return self.__entities[item]

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __contains__(self, key):

        if isinstance(key, ResourceKey):

            if self.__suffix != '*' and self.__suffix != key.suffix:
                return False

            for entity, value in self.__entities.items():
                if entity == 'desc':
                    continue

                if value == '^':
                    if entity in key.__entities:
                        return False
                else:

                    if entity not in key.__entities:
                        continue

                    if value == '*':
                        continue

                    if value != key.__entities[entity]:
                        return False

            if 'desc' in key.entities and 'desc' in self.__entities:

                if key.entities['desc'] == '^':
                    if 'desc' in key.__entities:
                        return False

                elif 'desc' not in key.__entities:
                    return True

                my_strat = self.strategy
                key_strat = key.strategy

                for k, v in key_strat.items():
                    if k not in my_strat:
                        continue
                    if v != my_strat[k]:
                        return False

            if self.tags:
                if not key.__tags:
                    return False
                if not all(tag in key.tags for tag in self.__tags):
                    return False

            return True

        elif isinstance(key, str):
            return key in self.__entities

        return False

    @property
    def suffix(self):
        return self.__suffix

    @property
    def tags(self):
        return {t for t in self.__tags}

    @property
    def strategy(self):
        if not self.__strategy:
            return {}

        return self.__strategy.forks

    @property
    def entities(self):
        return {
            k: v
            for k, v in self.__entities.items()
        }

    @staticmethod
    def from_key(key):
        if isinstance(key, ResourceKey):
            return key

        return ResourceKey(key)

    def isfilter(self):
        return \
            len(self.__entities) == 0 or \
            any(
                v == '*'
                for v in self.__entities.values()
            ) or \
            self.__suffix == '*'


class Resource:

    def __init__(self, workflow_node, slot):
        self.workflow_node = workflow_node
        self.slot = slot


class ResourcePool:

    __pool: Dict[ResourceKey, Resource]
    __pool_by_type: Dict[str, Dict[ResourceKey, Resource]]
    __pool_by_tag: Dict[str, Dict[ResourceKey, Resource]]
    __pool_branches: Dict[str, Set[str]]
    __pool_branched_resources: Dict[str, Set[ResourceKey]]

    def __init__(self):
        self.__pool = {}
        self.__pool_by_type = {}
        self.__pool_by_tag = {}
        self.__pool_branches = {
            entity: set()
            for entity in ResourceKey.branching_entities
        }
        self.__pool_branched_resources = {
            entity: set()
            for entity in ResourceKey.branching_entities
        }

    def __contains__(self, key: ResourceKey) -> bool:
        for rp_key in self.__pool.keys():
            if rp_key in key:
                return True
        return False

    def __getitem__(self, key: Union[ResourceKey, str, List[str]]) -> Union[Resource, Dict]:

        if isinstance(key, list):
            return self.extract(*key)

        if isinstance(key, ResourceKey):
            return self.__pool[key]

        if key in self.__pool_by_type:
            return self.__pool_by_type[key]

        if key in self.__pool_by_tag:
            return self.__pool_by_tag[key]

        raise KeyError(f'Key "{key}" not find in suffixes or tags')


    def __setitem__(self, resource_key: ResourceKey, resource: Resource) -> None:

        if not isinstance(resource_key, ResourceKey):
            resource_key = ResourceKey(str(resource_key))

        if resource_key.isfilter():
            raise KeyError(f'Resource key cannot be a filter: {resource_key}')

        self.__pool[resource_key] = resource

        if resource_key['suffix'] not in self.__pool_by_type:
            self.__pool_by_type[resource_key['suffix']] = {}

        if resource_key in self.__pool_by_type[resource_key['suffix']]:
            raise KeyError(f'Resource key {resource_key} already '
                           f'exists in the pool.')

        self.__pool_by_type[resource_key['suffix']][resource_key] = resource

        cleaner = {en: None for en in ResourceKey.branching_entities}
        clean_resource_key = ResourceKey(
            resource_key,
            **cleaner
        )
        for entity in ResourceKey.branching_entities:
            if entity in resource_key:
                self.__pool_branches[entity].add(resource_key[entity])
                self.__pool_branched_resources[entity].add(clean_resource_key)

        for flag in resource_key.tags:
            if flag not in self.__pool:
                self.__pool_by_tag[flag] = {}
            self.__pool_by_tag[flag][resource_key] = resource

    def group_by(self, name: str, key: str) -> MappingProxyType:
        if name not in ['suffix', 'tag']:
            raise ValueError(f'Name {name} does not exist! try "suffix" or "tag"')
        resource = self._pool_by_type if name == 'suffix' else self._pool_by_tag
        if key not in resource:
            return MappingProxyType({})
        return MappingProxyType(resource[key])

    def extract(self, *resources):

        extracted_resources = {}
        strategies = {}

        resources = [ResourceKey(r) for r in resources]

        for resource in resources:
            extracted_resources[resource] = [
                r for r in self.__pool if r in resource
            ]

            for matching in extracted_resources[resource]:
                for strategy, name in matching.strategy.items():
                    if strategy not in strategies:
                        strategies[strategy] = set()
                    strategies[strategy].add(name)

        # Branching
        expected_branching_keys = [
            b for b in self.__pool_branches
            if
                # there is branching in this entity
                self.__pool_branches[b] and

                # all resource selectors for this entity are not wildcards
                all(
                    b not in resource or resource[b] != '*'
                    for resource in resources
                ) and

                # there is at least one selected resource that uses this branch
                any(
                    any(resource in b for b in self.__pool_branched_resources[b])
                    for resource in resources
                )
        ]
        expected_branching_values_set = [
            self.__pool_branches[b] for b in expected_branching_keys
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
                                bk: bv if bv != "*" else strategy_extracted_resource[bk]
                                for bk, bv in {**expected_resource_unbranching, **expected_branching}.items()
                                if bk in strategy_extracted_resource
                            },
                            **{
                                k: v
                                for k, v in strategy_extracted_resource.entities.items()
                                if k in resource
                            }
                        )

                        if branched_resource in extracted_resource_pool:
                            if self[strategy_extracted_resource] != extracted_resource_pool[branched_resource]:
                                raise ValueError()
                            continue

                        extracted_resource_pool[branched_resource] = self[strategy_extracted_resource]

                else:
                    break

            # Assert strategy has all the resources required
            if all(e in extracted_resource_pool for e in extracted_resources):
                yield ResourceKey(
                    desc=strategy_combination,
                    **expected_branching,
                    suffix='*'
                ), extracted_resource_pool
