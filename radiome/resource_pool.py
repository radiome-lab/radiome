from typing import Union, List, Dict

class ResourceKey(object):

    supported_entities: List[str] = ['space', 'desc', 'atlas', 'roi', 'label', 'hemi', 'from', 'to', 'suffix']
    valid_suffixes: List[str] = []

    def __init__(self,
                 entity_dictionary: Union[str, Dict[str, str], None] = None,
                 **kwargs) -> None:

        self.entity_dictionary: Dict[str, str] = {}

        if not entity_dictionary:
            entity_dictionary = kwargs

        # initialize dictionary from a key
        if isinstance(entity_dictionary, str):

            for entity_pair in entity_dictionary.split('_'):

                if '-' in entity_pair:
                    key, value = entity_pair.split('-')
                else:
                    key = 'suffix'
                    value = entity_pair

                if not value or not isinstance(value, str):
                    raise ValueError(f'Value must be a string, and cannot be empty ({value})')

                if key in self.supported_entities:
                    self.entity_dictionary[key] = value
                else:
                    raise KeyError(f'Entity {key} is not supported by the resource pool')

        # initialize from a dictionary
        elif isinstance(entity_dictionary, dict):
            for key, value in entity_dictionary.items():

                if key not in self.supported_entities:
                    raise KeyError(f'Entity {key} is not supported by the resource pool')

                self.entity_dictionary[key] = str(value)

        else:
            raise ValueError(f'Function argument entity_dictionary should be a str or dict,'
                             f' not a {type(entity_dictionary)}')

        if 'suffix' not in self.entity_dictionary:
            raise ValueError('Could not extract suffix from entity_dictionary')

    def __str__(self):

        return '_'.join(
            [
                '-'.join([entity, self.entity_dictionary[entity]])
                for entity in self.supported_entities
                if entity in self.entity_dictionary and entity != 'suffix'
            ]
                +
            [
                self.entity_dictionary['suffix']
            ]
        )

    def __hash__(self):

        return hash(self.__str__())

    def __getitem__(self, item):

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
