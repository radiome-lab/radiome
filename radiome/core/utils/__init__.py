import hashlib

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