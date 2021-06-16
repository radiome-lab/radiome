import copy
import hashlib
from string import Formatter


def _nested_repr(obj):
    if isinstance(obj, dict):
        return repr([
            (_nested_repr(k), _nested_repr(v))
            for k, v in sorted(obj.items(), key=lambda i: i[0])
        ])

    if isinstance(obj, (list, tuple)):
        return repr([_nested_repr(v) for v in obj])

    if isinstance(obj, set):
        return repr([_nested_repr(v) for v in sorted(list(obj))])

    if isinstance(obj, Hashable):
        return _nested_repr(obj.__longhash__())

    return repr(obj)


def deterministic_hash(obj):
    hasher = hashlib.blake2s(digest_size=8)
    hasher.update(_nested_repr(obj).encode('UTF-8'))
    return hasher.hexdigest()


class Hashable:
    _hash = None

    def __hashcontent__(self):
        raise NotImplementedError

    def __longhash__(self):
        if not self._hash:
            reference = self._reference if hasattr(self, '_reference') else ''
            self._hash = deterministic_hash(self.__hashcontent__())
        return self._hash

    def __hash__(self):
        return int(self.__longhash__(), 16)

    def __shorthash__(self):
        return self.__longhash__()[-8:]

    def __eq__(self, other):
        return self.__longhash__() == other.__longhash__()

    def __update_hash__(self):
        self._hash = None
        selfid = id(self)
        self.__longhash__()


class TemplateDictionaryBuilder:
    def __init__(self, mapping):
        self._formatter = Formatter()
        self._mapping = mapping
        self._visited = set()

    def __getitem__(self, item):
        if item in self._visited:
            raise ValueError(f'{item} has cyclic reference. Please check your template.')
        if item not in self._mapping:
            raise KeyError(f'variable "{item}" does not exist.')
        self._visited.add(item)
        if 'default' not in self._mapping[item]:
            raise ValueError(f'{item} can not be substituted because it does not have a default value.')
        template = str(self._mapping[item]['default'])
        substituted = self._formatter.vformat(template, [], self)
        self._visited.remove(item)
        return substituted

    def build(self):
        res = {}
        for k, v in self._mapping.items():
            v = copy.copy(v)
            if 'default' in v and v['type'] == 'string':
                v['default'] = self[k]
                res[k] = v
            else:
                res[k] = v
        return res
