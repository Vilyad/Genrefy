"""
Тесты для базового сервиса API.
"""
import json
import os
import sys
import tempfile
import unittest
import django
from django.conf import settings
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if not settings.configured:
    settings.configure(
        SECRET_KEY='test-secret-key',
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'catalog',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        LASTFM_API_KEY='test_key',
        LASTFM_SHARED_SECRET='test_secret',
        USE_TZ=True,
    )
    django.setup()

from catalog.services.base_service import BaseAPIService


class TestBaseAPIService(unittest.TestCase):
    """Тесты для BaseAPIService."""

    def setUp(self):
        """Настройка тестового окружения."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = BaseAPIService(cache_dir=self.temp_dir)

    def tearDown(self):
        """Очистка после тестов."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_creates_cache_dir(self):
        """Тест: создание директории кэша при инициализации."""
        cache_dir = os.path.join(self.temp_dir, 'test_cache')
        service = BaseAPIService(cache_dir=cache_dir)

        self.assertTrue(os.path.exists(cache_dir))

    def test_get_cache_key_consistent(self):
        """Тест: генерация одинакового ключа для одинаковых параметров."""
        params1 = {'method': 'test', 'param': 'value'}
        params2 = {'param': 'value', 'method': 'test'}

        key1 = self.service._get_cache_key('test_method', params1)
        key2 = self.service._get_cache_key('test_method', params2)

        self.assertEqual(key1, key2)

    def test_get_cache_key_different_for_different_params(self):
        """Тест: разные ключи для разных параметров."""
        params1 = {'method': 'test', 'param': 'value1'}
        params2 = {'method': 'test', 'param': 'value2'}

        key1 = self.service._get_cache_key('test_method', params1)
        key2 = self.service._get_cache_key('test_method', params2)

        self.assertNotEqual(key1, key2)

    def test_save_to_cache(self):
        """Тест: сохранение данных в кэш."""
        cache_key = 'test_key'
        test_data = {'test': 'data'}

        self.service._save_to_cache(cache_key, test_data)

        cache_file = Path(self.temp_dir) / f"{cache_key}.json"
        self.assertTrue(cache_file.exists())

        with open(cache_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, test_data)

    def test_load_from_cache_fresh(self):
        """Тест: загрузка свежих данных из кэша."""
        cache_key = 'test_key'
        test_data = {'test': 'data'}

        self.service._save_to_cache(cache_key, test_data)

        loaded_data = self.service._load_from_cache(cache_key, ttl_days=30)

        self.assertEqual(loaded_data, test_data)

    def test_load_from_cache_expired(self):
        """Тест: кэш устарел, возвращается None."""
        cache_key = 'test_key'
        test_data = {'test': 'data'}

        self.service._save_to_cache(cache_key, test_data)

        cache_file = Path(self.temp_dir) / f"{cache_key}.json"

        thirty_days_ago = datetime.now() - timedelta(days=30)
        os.utime(cache_file, (thirty_days_ago.timestamp(), thirty_days_ago.timestamp()))

        loaded_data = self.service._load_from_cache(cache_key, ttl_days=7)

        self.assertIsNone(loaded_data)

    @patch('time.sleep')
    @patch('time.time')
    def test_rate_limit(self, mock_time, mock_sleep):
        """Тест: соблюдение интервала между запросами."""
        mock_time.side_effect = [0.1, 0.3]

        result = self.service._rate_limit(0.0, 0.2)

        mock_sleep.assert_called_once_with(0.1)
        self.assertEqual(result, 0.3)

        mock_sleep.reset_mock()

        mock_time.side_effect = [0.3]

        result = self.service._rate_limit(0.0, 0.2)

        mock_sleep.assert_not_called()
        self.assertEqual(result, 0.3)


if __name__ == '__main__':
    unittest.main()
