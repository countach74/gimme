from dogpile.cache.api import CacheBackend, NO_VALUE


class Memory(CacheBackend):
    def __init__(self, arguments):
        self.cache = {}

    def get(self, key):
        return self.cache.get(key, NO_VALUE)

    def set(self, key, value):
        self.cache[key] = value

    def delete(self, key):
        del(self.cache[key])
