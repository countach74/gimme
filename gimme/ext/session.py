import abc
from dogpile.cache import make_region


class ChangeTracker(object):
    def __init__(self):
        self._dirty = False

    def is_dirty(self):
        return self._dirty

    def dirty(self):
        self._dirty = True

    def clean(self):
        self._dirty = False


class NotifiedMixin(object):
    def __init__(self):
        if isinstance(self, list):
            i = 0
            for item in self:
                self[i] = self._check(item)
                i += 1
        elif isinstance(self, dict):
            for k, v in self.items():
                self[k] = self._check(v)

    def _check(self, item):
        if isinstance(item, dict) and not isinstance(item, NotifiedDict):
            item = NotifiedDict(self._state, item)
        if isinstance(item, list) and not isinstance(item, NotifiedList):
            item = NotifiedList(self._state, item)
        return item


class NotifiedDict(dict, NotifiedMixin):
    def __init__(self, state, *args, **kwargs):
        self._state = state
        dict.__init__(self, *args, **kwargs)
        NotifiedMixin.__init__(self)

    def __setitem__(self, key, value):
        self._state.dirty()
        value = self._check(value)
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        self._state.dirty()
        dict.__delitem__(self, key)


class NotifiedList(list, NotifiedMixin):
    def __init__(self, state, *args, **kwargs):
        self._state = state
        list.__init__(self, *args, **kwargs)
        NotifiedMixin.__init__(self)

    def __delitem__(self, key):
        self._state.dirty()
        list.__delitem__(self, key)

    def append(self, item):
        self._state.dirty()
        item = self._check(item)
        list.append(self, item)

    def remove(self, item):
        self._state.dirty()
        list.remove(self, item)

    def insert(self, index, item):
        self._state.dirty()
        item = self._check(item)
        list.insert(self, index, item)

    def pop(self, *args, **kwargs):
        self._state.dirty()
        return list.pop(self, *args, **kwargs)


class Session(object):
    '''
    The base session interface for Gimme. Designed to behave very much like a
    normal :func:`dict`.

    :param cache: The dogpile cache region to store to.
    :param key: A unique identifier for the session.
    :param data: A dictionary of data to start with.
    :param new: Whether or not the session is new or not (affects whether or
        not the session data will be stored, regardless of anything being in
        the data dictionary).
    '''

    def __init__(self, cache, key, data={}, new=False):
        self._cache = cache
        self._key = key
        self._state = ChangeTracker()
        self._data = NotifiedDict(self._state, data)

        if new:
            self._state.dirty()

    def __contains__(self, key):
        '''
        Checks if ``key`` is in the session.

        :param key: The key to check for.
        :return: ``True/False`` depending if the key is found.
        '''
        return key in self._data

    def __getitem__(self, key):
        '''
        Fetches ``key`` from session.

        :param key: The key to fetch.
        :return: The item from the session.
        '''
        return self._data[key]

    def __setitem__(self, key, value):
        '''
        Sets ``key`` in session to ``value``.

        :param key: The key to set.
        :param value: The value to set it to.
        '''
        self._data[key] = value

    def __repr__(self):
        return "Session(%s)" % (self._key)

    def get(self, *args, **kwargs):
        '''
        Fetches a key from the session. Works just like
        :meth:`dict.get`. In fact, this method simply calls
        :meth:`dict.get`.
        '''
        return self._data.get(*args, **kwargs)

    def save(self):
        '''
        Save the session to whichever backend has been selected.
        '''
        self._cache.set(self._key, dict(self._data))

    def touch(self):
        '''
        Actually, this just calls :meth:`save
        <gimme.ext.session.Session.save>`.
        '''
        self._cache.save()

    def destroy(self):
        '''
        Removes the session from the cache backend.
        '''
        self._cache.delete(self._key)

    def keys(self):
        return self._data.keys()
