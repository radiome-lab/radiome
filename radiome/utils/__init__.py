import hashlib


def _nestedrepr(obj):
    if isinstance(obj, dict):
        return repr([
            (_nestedrepr(k), _nestedrepr(v))
            for k, v in sorted(obj.items(), key=lambda i: i[0])
        ])
    elif isinstance(obj, (list, tuple)):
        return repr([_nestedrepr(v) for v in obj])
    elif isinstance(obj, set):
        return repr([_nestedrepr(v) for v in sorted(list(obj))])
    else:
        return repr(obj)


def deterministic_hash(obj):
    return hashlib.sha256(_nestedrepr(obj).encode('UTF-8')).hexdigest()


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
