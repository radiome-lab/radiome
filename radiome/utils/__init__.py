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
        return _nested_repr(obj.__hashcontent__())

    return repr(obj)


def deterministic_hash(obj):
    hasher = hashlib.blake2s(digest_size=8)
    hasher.update(_nested_repr(obj).encode('UTF-8'))
    return hasher.hexdigest()


class Hashable:

    def __hashcontent__(self):
        raise NotImplementedError

    def __longhash__(self):
        return deterministic_hash(self.__hashcontent__())

    def __hash__(self):
        return int(self.__longhash__(), 16)

    def __shorthash__(self):
        return self.__longhash__()[-8:]

    def __eq__(self, other):
        return self.__longhash__() == other.__longhash__()