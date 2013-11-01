
# Monkeypatch redis
import utils.mock_redis
utils.mock_redis.patch()

import base
import cache
import config
import cStringIO as StringIO
import json
import re
import storage


class TestLocalStorage(base.TestCase):

    def set_config(self, kind):
        self._storage = storage.load(kind)
        # Generate configs with and without cache
        # used by activate_cache.
        self._config_cache = None
        if self._storage._config.cache:
            self._config_cache = self._storage._config
        # Generate self._config (no cache)
        config_string = repr(self._storage._config).replace(
            "'", '"').replace('True', 'true').replace('False', 'false')
        c = json.loads(re.sub('u(".*?")', '\\1', config_string))
        if 'cache' in c:
            del c['cache']
        self._config = config.Config(c)
        # Add default cache values if not passed
        if not self._config_cache:
            c_cache = dict(c)
            c_cache['cache'] = cache.redis_opts
            self._config_cache = config.Config(c_cache)
        # Cache disabled by default
        self.activate_cache(False)

    def setUp(self):
        self.set_config('local')

    def activate_cache(self, boolean):
        config._config = (self._config_cache if boolean
                          else self._config)
        reload(cache)

    def test_simple(self):
        filename = self.gen_random_string()
        content = self.gen_random_string()
        # Do tests with and without cache
        for with_cache in [True, False]:
            self.activate_cache(with_cache)
            # test exists
            self.assertFalse(self._storage.exists(filename))
            self._storage.put_content(filename, content)
            self.assertTrue(self._storage.exists(filename))
            # test read / write
            ret = self._storage.get_content(filename)
            self.assertEqual(ret, content)
            # test size
            ret = self._storage.get_size(filename)
            self.assertEqual(ret, len(content))
            # test remove
            self._storage.remove(filename)
            self.assertFalse(self._storage.exists(filename))
        # Ensure the cache is deactivated as default
        self.activate_cache(False)

    def test_get_refresh_cache(self):
        filename = self.gen_random_string()
        content = self.gen_random_string()
        self.activate_cache(False)
        self._storage.put_content(filename, content)
        self.activate_cache(True)
        # The following get should refresh the cache
        ret = self._storage.get_content(filename)
        self.activate_cache(False)
        self._storage.remove(filename)
        self.activate_cache(True)

    def test_load_default_cache(self):
        config_string = repr(self._storage._config).replace(
            "'", '"').replace('True', 'true').replace('False', 'false')
        c = json.loads(re.sub('u(".*?")', '\\1', config_string))
        c['cache'] = True
        config._config = config.Config(c)
        reload(cache)
        self._storage = storage.load('local')
        self.assertEqual(cache.redis_conn.connection_pool
            .connection_kwargs['port'], 6379)

    def test_stream(self):
        filename = self.gen_random_string()
        # test 7MB
        content = self.gen_random_string(7 * 1024 * 1024)
        # test exists
        io = StringIO.StringIO(content)
        self.assertFalse(self._storage.exists(filename))
        self._storage.stream_write(filename, io)
        io.close()
        self.assertTrue(self._storage.exists(filename))
        # test read / write
        data = ''
        for buf in self._storage.stream_read(filename):
            data += buf
        self.assertEqual(content, data)
        # test remove
        self._storage.remove(filename)
        self.assertFalse(self._storage.exists(filename))

    def test_errors(self):
        notexist = self.gen_random_string()
        self.assertRaises(IOError, self._storage.get_content, notexist)
        iterator = self._storage.list_directory(notexist)
        self.assertRaises(OSError, next, iterator)
        self.assertRaises(OSError, self._storage.get_size, notexist)
