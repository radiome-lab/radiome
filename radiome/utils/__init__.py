import hashlib


def deterministic_hash(obj):
    return hashlib.sha256(repr(obj).encode('UTF-8')).hexdigest()


class Hashable:

    def __hashcontent__(self):
        raise NotImplementedError

    def __hexhash__(self):
        return deterministic_hash(self.__hashcontent__())

    def __hash__(self):
        return int(self.__hexhash__(), 16)

    def __shorthash__(self):
        return self.__hexhash__()[-8:]

    def __eq__(self, other):
        return self.__hexhash__() == other.__hexhash__()
