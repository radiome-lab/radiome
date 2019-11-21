from typing import Union, List, Dict


class ResourceKey(object):

    supported_entities: List[str] = ['space', 'desc', 'atlas', 'roi', 'label', 'hemi', 'from', 'to']
    valid_suffixes: List[str] = ['mask']

    suffix: str = ''
    entity_dictionary: Dict[str, str] = {}
    strategy: List[str] = []

    def __init__(self,
                 entity_dictionary: Union[str, Dict[str, str], None] = None,
                 **kwargs) -> None:

        self.entity_dictionary = {}
        self.strategy = []

        # initialize dictionary from a key
        if isinstance(entity_dictionary, str):

            *entities, suffix = entity_dictionary.split('_')

            if '-' in suffix:
                raise ValueError(f'Suffix not provided in "{entity_dictionary}"')

            if suffix not in self.valid_suffixes:
                raise ValueError(f'Invalid suffix "{suffix}" in "{entity_dictionary}"')

            self.suffix = suffix

            for entity_pair in entities:

                if '-' not in entity_pair:
                    raise ValueError(f'Invalid entity pair "{entity_pair}" in "{entity_dictionary}"')

                key, value = entity_pair.split('-', 1)

                if not value:
                    raise ValueError(f'Entity value cannot be empty: "{value}"')

                if key not in self.supported_entities:
                    raise KeyError(f'Entity "{key}" is not supported by the resource pool')

                self.entity_dictionary[key] = value

        # initialize from a dictionary or custom parameters
        elif isinstance(entity_dictionary, dict) or kwargs:

            # add custom entities
            if not entity_dictionary:
                entity_dictionary = {}
            entity_dictionary.update(kwargs)

            # ensure immutability
            entity_dictionary = { str(k): str(v) for k, v in entity_dictionary.items() }

            suffix = entity_dictionary.get('suffix', '')
            if suffix not in self.valid_suffixes:
                raise ValueError(f'Invalid suffix "{suffix}" in "{entity_dictionary}"')

            for key, value in entity_dictionary.items():

                if key == 'suffix':
                    self.suffix = value
                    continue

                if key not in self.supported_entities:
                    raise KeyError(f'Entity {key} is not supported by the resource pool')

                self.entity_dictionary[key] = value

        else:
            raise ValueError(f'Provided entity_dictionary must be a string or dictionary,'
                             f' not a {type(entity_dictionary)}')

    def __str__(self):

        return '_'.join(
            [
                '-'.join([entity, self.entity_dictionary[entity]])
                for entity in self.supported_entities
                if entity in self.entity_dictionary
            ]
                +
            [
                self.suffix
            ]
        )

    def __hash__(self):

        return hash(self.__str__())

    def __getitem__(self, item):

        if item == 'suffix':
            return self.suffix

        if item not in self.supported_entities:
            raise KeyError(f'Entity {item} is not supported by the resource pool')

        return self.entity_dictionary[item]


class Resource(object):

    def __init__(self, workflow_node, slot, flags: List[str]):
        self.workflow_node = workflow_node
        self.slot = slot
        self.flags = flags


class ResourcePool(object):

    def __init__(self):
        self.pool_dictionary = {}

    def __getitem__(self, resource_key: Union[ResourceKey, str]) -> Resource:

        if isinstance(resource_key, ResourceKey):
            return self.pool_dictionary[resource_key['suffix']][resource_key]
        else:
            return self.pool_dictionary[resource_key]

    def __setitem__(self, resource_key: ResourceKey, resource: Resource) -> None:

        if resource_key['suffix'] not in self.pool_dictionary:
            self.pool_dictionary[resource_key['suffix']] = {}

        if resource_key in self.pool_dictionary[resource_key['suffix']]:
            raise KeyError(f'Resource key {resource_key} already exists in the pool.')

        self.pool_dictionary[resource_key['suffix']][resource_key] = resource

        for flag in resource.flags:
            if flag not in self.pool_dictionary:
                self.pool_dictionary[flag] = {}
            self.pool_dictionary[flag][resource_key] = resource
