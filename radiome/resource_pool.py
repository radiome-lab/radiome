

class ResourceKey(object):

    supported_entities = ['space', 'desc', 'suffix', 'atlas', 'roi', 'label', 'hemi', 'from', 'to']
    valid_suffixes = []

    def __init__(self, entity_dictionary):

        self.entity_dictionary = {}

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

        string_components = []

        for entity in self.supported_entities:
            if entity != 'suffix':
                if entity in self.entity_dictionary:
                    string_components.append('-'.join([entity, self.entity_dictionary[entity]]))

        string_components.append(self.entity_dictionary['suffix'])

        return '_'.join(string_components)

    def __hash__(self):

        return hash(self.__str__())

    def __getitem__(self, item):

        if item not in self.supported_entities:
            raise KeyError(f'Entity {item} is not supported by the resource pool')

        return self.entity_dictionary[item]


class Resource(object):

    def __init__(self, workflow_node, slot, flags):

        self.workflow_node = workflow_node
        self.slot = slot
        self.flags = flags
