import logging
import unittest

from sqlalchemy.engine import make_url

from gtdblib import log
from gtdblib.config import CONFIG
from gtdblib.db import GenericEngine


class TestLogging(unittest.TestCase):

    def test_root_logger_not_configured(self):
        self.assertEqual(log.name, 'rich')
        self.assertTrue(log.handlers)
        self.assertFalse(log.propagate)
        self.assertNotIn(log.handlers[0], logging.getLogger().handlers)


class TestDbUrl(unittest.TestCase):

    def setUp(self):
        self._yaml = CONFIG._yaml

    def tearDown(self):
        CONFIG._yaml = self._yaml

    def test_url_escapes_credentials(self):
        CONFIG._yaml = {'db': {'host': 'db.example.org:5432', 'user': 'us@r', 'pass': 'p@ss:/w+rd %'}}
        url = make_url(GenericEngine('common').url)
        self.assertEqual(url.username, 'us@r')
        self.assertEqual(url.password, 'p@ss:/w+rd %')
        self.assertEqual(url.host, 'db.example.org')
        self.assertEqual(url.port, 5432)
        self.assertEqual(url.database, 'common')


if __name__ == '__main__':
    unittest.main()
