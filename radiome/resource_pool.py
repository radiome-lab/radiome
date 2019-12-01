import itertools
from types import MappingProxyType
from typing import Union, List, Dict


class ResourceKey:
    supported_entities: List[str] = ['space', 'atlas', 'roi', 'label',
                                     'hemi', 'from', 'to', 'desc']
    valid_suffixes: List[str] = ['mask', 'bold', 'T1w']

    _suffix: str
    _entities: Dict[str, str]
    _tags: List[str]

    def __init__(self,
                 entity_dictionary: Union[str, Dict[str, str], None] = None,
                 tags: Union[List[str], None] = None,
                 **kwargs) -> None:

        self._entities = {}
        self._suffix = ''
        self._tags = tags or []

        # initialize dictionary from a key
        if isinstance(entity_dictionary, str):

            *entities, suffix = entity_dictionary.split('_')

            if '-' in suffix:
                raise ValueError(f'Suffix not provided'
                                 f'in "{entity_dictionary}"')

            if suffix not in self.valid_suffixes:
                raise ValueError(f'Invalid suffix "{suffix}"'
                                 f' in "{entity_dictionary}"')

            self._suffix = suffix

            for entity_pair in entities:

                if '-' not in entity_pair:
                    raise ValueError(f'Invalid entity pair "{entity_pair}" '
                                     f'in "{entity_dictionary}"')

                key, value = entity_pair.split('-', 1)

                if not value:
                    raise ValueError(f'Entity value cannot '
                                     f'be empty: "{value}"')

                if key not in self.supported_entities:
                    raise KeyError(f'Entity "{key}" is not supported '
                                   f'by the resource pool')

                self._entities[key] = value

        # initialize from a dictionary or custom parameters
        elif isinstance(entity_dictionary, dict):

            # ensure immutability
            entity_dictionary = {
                str(k): str(v)
                for k, v in entity_dictionary.items()
            }

            suffix = entity_dictionary.get('suffix', '')
            if suffix not in self.valid_suffixes:
                raise ValueError(f'Invalid suffix "{suffix}"'
                                 f' in "{entity_dictionary}"')
            self._suffix = suffix

            for key, value in entity_dictionary.items():
                if key == 'suffix':
                    continue

                if key not in self.supported_entities:
                    raise KeyError(f'Entity {key} is not supported '
                                   f'by the resource pool')

                self._entities[key] = value

        elif not kwargs:
            raise ValueError(f'Provided entity_dictionary must be '
                             f'a string or dictionary, not a '
                             f'{type(entity_dictionary)}')

        if kwargs:
            suffix = kwargs.get('suffix', self._suffix)
            if suffix not in self.valid_suffixes:
                raise ValueError(f'Invalid suffix "{suffix}" in '
                                 f'"{entity_dictionary}"')
            self._suffix = suffix

            for key, value in kwargs.items():
                if key == 'suffix':
                    continue

                if key not in self.supported_entities:
                    raise KeyError(f'Entity {key} is not supported '
                                   f'by the resource pool')

                self._entities[key] = value

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.__str__())

    def __str__(self):
        return '_'.join(
            [
                '-'.join([entity, self._entities[entity]])
                for entity in self.supported_entities
                if entity in self._entities
            ]
            +
            [
                self._suffix
            ]
        )

    def __getitem__(self, item):

        if item == 'suffix':
            return self._suffix

        if item not in self.supported_entities:
            raise KeyError(f'Entity {item} is not supported '
                           f'by the resource pool')

        return self._entities[item]

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __contains__(self, key):

        if isinstance(key, ResourceKey):

            if self._suffix != key.suffix:
                return False

            for entity, value in key.entities.items():
                if entity == 'desc':
                    continue

                if value == '^':
                    if entity in self._entities:
                        return False
                else:

                    if entity not in self._entities:
                        return False

                    if value != self._entities[entity]:
                        return False

            if 'desc' in key.entities:

                if key.entities['desc'] == '^':
                    if 'desc' in self._entities:
                        return False

                elif 'desc' not in self._entities:
                    return False

                my_strat = self.strategy
                key_strat = key.strategy

                for k, v in key_strat.items():
                    if k not in my_strat:
                        return False
                    if v != my_strat[k]:
                        return False

            if key.tags:
                if not self._tags:
                    return False
                if not all(tag in self._tags for tag in key.tags):
                    return False

            return True

        return False

    @property
    def suffix(self):
        return self._suffix

    @property
    def tags(self):
        return [t for t in self._tags]

    @property
    def strategy(self):
        if not self._entities.get('desc'):
            return {}

        return {
            k: v
            for k, v in [
                strat.split('-', 1)
                for strat in self._entities.get('desc', '').split('+')
            ]
        }

    @property
    def entities(self):
        return {k: v for k, v in self._entities.items()}

    @staticmethod
    def from_key(key):
        if isinstance(key, ResourceKey):
            return key

        return ResourceKey(key)


class Resource:

    def __init__(self, workflow_node, slot):
        self.workflow_node = workflow_node
        self.slot = slot


class ResourcePool:
    _pool: Dict[ResourceKey, Resource]
    _pool_by_type: Dict[str, Dict[ResourceKey, Resource]]
    _pool_by_tag: Dict[str, Dict[ResourceKey, Resource]]

    def __init__(self):
        self._pool = {}
        self._pool_by_type = {}
        self._pool_by_tag = {}

    def __contains__(self, key: ResourceKey) -> bool:
        return key in self._pool

    def __getitem__(self, key: Union[ResourceKey, str]) -> Resource:

        if isinstance(key, ResourceKey):
            return self._pool[key]

        raise KeyError(f'Key "{key}" not found in suffixes or tags')

    def __setitem__(self, resource_key: ResourceKey, resource: Resource) -> None:

        if not isinstance(resource_key, ResourceKey):
            resource_key = ResourceKey(str(resource_key))

        self._pool[resource_key] = resource

        if resource_key['suffix'] not in self._pool_by_type:
            self._pool_by_type[resource_key['suffix']] = {}

        if resource_key in self._pool_by_type[resource_key['suffix']]:
            raise KeyError(f'Resource key {resource_key} already '
                           f'exists in the pool.')

        self._pool_by_type[resource_key['suffix']][resource_key] = resource

        for flag in resource_key.tags:
            if flag not in self._pool:
                self._pool_by_tag[flag] = {}
            self._pool_by_tag[flag][resource_key] = resource

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

        for resource in resources:
            resource = ResourceKey.from_key(resource)

            extracted_resources[resource] = [
                r for r in self._pool if resource in r
            ]

            for matching in extracted_resources[resource]:
                for strategy, name in matching.strategy.items():
                    if strategy not in strategies:
                        strategies[strategy] = set()
                    strategies[strategy].add(name)

        strategies_keys, strategies_values_set = strategies.keys(), strategies.values()

        for strategies_values in itertools.product(*strategies_values_set):

            strategy_combination = '+'.join([
                '-'.join([k, v])
                for k, v
                in zip(strategies_keys, strategies_values)
            ])

            extracted_resource_pool = ResourcePool()

            for resource, extracted in extracted_resources.items():

                resource_filter = ResourceKey(
                    str(resource),
                    desc=strategy_combination,
                )

                strategy_extracted = [
                    e for e in extracted if e in resource_filter
                ]

                if strategy_extracted:
                    if len(strategy_extracted) > 1:
                        raise ValueError

                    extracted_resource_pool[resource] = self[strategy_extracted[0]]

                else:
                    break

            # Assert strategy has all the resources required
            if all(e in extracted_resource_pool for e in extracted_resources):
                yield strategy_combination, extracted_resource_pool
