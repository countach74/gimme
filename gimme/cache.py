from dogpile.cache.api import CacheBackend, NO_VALUE
import pickle
import os


class Memory(CacheBackend):
    def __init__(self, arguments):
        self.cache = {}

    def get(self, key):
        return self.cache.get(key, NO_VALUE)

    def set(self, key, value):
        self.cache[key] = value

    def delete(self, key):
        del(self.cache[key])


class File(CacheBackend):
    def __init__(self, arguments):
        self.directory = arguments.get('directory', '/tmp/gimme')

    def get(self, key):
        try:
            with open(os.path.join(self.directory, key), 'r') as f:
                return pickle.load(f)
        except:
            return NO_VALUE

    def set(self, key, value):
        path = os.path.join(os.path.abspath(self.directory), key)

        if not os.path.exists(os.path.abspath(self.directory)):
            os.makedirs(os.path.abspath(self.directory))
        try:
            with open(path, 'w') as f:
                pickle.dump(value, f)
        except:
            pass

    def delete(self, key):
        try:
            os.unlink(os.path.join(self.directory, key))
        except OSError:
            pass
