
'''Fake redis database with a dictionary when testing.'''


def patch():

    import redis
    import utils

    redis.__fake_db = {}

    @utils.monkeypatch_method(redis.StrictRedis)
    def __init__(self, *args, **kwargs):
        pass

    @utils.monkeypatch_method(redis.StrictRedis)
    def get(self, key):
        return redis.__fake_db.get(key, None)

    @utils.monkeypatch_method(redis.StrictRedis)
    def set(self, key, value, **kwargs):
        '''Fake set method doesn't implement keyword argument when testing.'''
        redis.__fake_db[key] = value

    @utils.monkeypatch_method(redis.StrictRedis)
    def delete(self, keys):
        '''Simple fake delete method.'''
        if keys.__class__.__name__ != 'list':
            keys = [keys]
        for key in keys:
            if key in redis.__fake_db:
                del redis.__fake_db[key]
