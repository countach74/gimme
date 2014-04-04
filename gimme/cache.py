from dogpile.cache.api import CacheBackend, NO_VALUE
import pickle
import os


class Memory(CacheBackend):
    cache = {}

    def __init__(self, arguments):
        pass

    def get(self, key):
        return self.cache.get(key, NO_VALUE)

    def set(self, key, value):
        self.cache[key] = value

    def delete(self, key):
        del(self.cache[key])


class Redis(CacheBackend):
    def __init__(self, arguments):
        if 'redis' not in arguments:
            raise KeyError("Redis cache backend expects 'redis' argument.")
        self.redis = arguments['redis']
        self.prefix = arguments.get('prefix', 'gimme_session::')
        self.expiration_time = arguments.get('redis_expiration_time', 60*60*24*7)

    def get(self, key):
        value = self.redis.get(self.prefix + key)
        return NO_VALUE if value is None else pickle.loads(value)

    def set(self, key, value):
        self.redis.set(self.prefix + key, pickle.dumps(value),
            ex=self.expiration_time)

    def delete(self, key):
        self.redis.delete(key)


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
