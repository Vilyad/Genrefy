"""
Тесты для сервиса Last.fm.
"""
import os
import sys
import tempfile
import unittest
import django
from django.conf import settings
from unittest.mock import patch, Mock

from catalog.services.lastfm_service import LastFMService

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
        LASTFM_API_KEY='test_api_key',
        LASTFM_SHARED_SECRET='test_shared_secret',
        USE_TZ=True,
    )
    django.setup()


class TestLastFMService(unittest.TestCase):
    """Тесты для LastFMService."""

    def setUp(self):
        """Настройка тестового окружения."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = LastFMService(cache_dir=self.temp_dir)

    def tearDown(self):
        """Очистка после тестов."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_with_api_keys(self):
        """Тест: инициализация с API ключами."""
        self.assertIsNotNone(self.service)
        self.assertEqual(self.service.api_key, 'test_api_key')
        self.assertEqual(self.service.shared_secret, 'test_shared_secret')

    def test_sign_request(self):
        """Тест: создание подписи запроса."""
        params = {
            'method': 'test.method',
            'api_key': 'test_key',
            'param1': 'value1',
            'param2': 'value2'
        }

        signature = self.service._sign_request(params)

        self.assertEqual(len(signature), 32)
        self.assertTrue(all(c in '0123456789abcdef' for c in signature))

    def test_sign_request_deterministic(self):
        """Тест: одинаковая подпись для одинаковых параметров."""
        params1 = {'method': 'test', 'a': '1', 'b': '2'}
        params2 = {'b': '2', 'a': '1', 'method': 'test'}

        sig1 = self.service._sign_request(params1)
        sig2 = self.service._sign_request(params2)

        self.assertEqual(sig1, sig2)

    @patch('catalog.services.lastfm_service.BaseAPIService._load_from_cache')
    def test_make_request_cache_hit(self, mock_load_cache):
        """Тест: запрос возвращает данные из кэша."""
        cached_data = {'cached': 'data'}
        mock_load_cache.return_value = cached_data

        with patch('requests.get') as mock_get:
            result = self.service._make_request('test.method', {})

            self.assertEqual(result, cached_data)
            mock_get.assert_not_called()

    @patch('catalog.services.lastfm_service.BaseAPIService._load_from_cache')
    @patch('catalog.services.lastfm_service.BaseAPIService._save_to_cache')
    @patch('catalog.services.lastfm_service.requests.get')
    def test_make_request_success(self, mock_get, mock_save_cache, mock_load_cache):
        """Тест: успешный HTTP запрос."""
        mock_load_cache.return_value = None

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_get.return_value = mock_response

        result = self.service._make_request('test.method', {'param': 'value'})

        self.assertEqual(result, {'success': True})
        mock_get.assert_called_once()
        mock_save_cache.assert_called_once()

    def test_parse_track_search_result_valid(self):
        """Тест: парсинг валидного результата поиска трека."""
        track_data = {
            'name': 'Test Track',
            'artist': 'Test Artist',
            'url': 'http://last.fm/track',
            'listeners': '1000',
            'image': [
                {'#text': 'http://img.small.jpg', 'size': 'small'},
                {'#text': 'http://img.large.jpg', 'size': 'large'}
            ],
            'mbid': 'test-mbid'
        }

        result = self.service._parse_track_search_result(track_data)

        self.assertEqual(result['name'], 'Test Track')
        self.assertEqual(result['artist'], 'Test Artist')
        self.assertEqual(result['listeners'], 1000)
        self.assertEqual(result['image'], 'http://img.large.jpg')

    def test_parse_track_search_result_invalid(self):
        """Тест: парсинг невалидного результата поиска трека."""
        track_data = {'invalid': 'data'}
        result = self.service._parse_track_search_result(track_data)
        self.assertIsNone(result)

    def test_parse_track_info(self):
        """Тест: парсинг полной информации о треке."""
        track_data = {
            'name': 'Test Track',
            'artist': {'name': 'Test Artist'},
            'url': 'http://last.fm/track',
            'duration': '240000',
            'listeners': '5000',
            'playcount': '10000',
            'album': {'title': 'Test Album'},
            'toptags': {
                'tag': [
                    {'name': 'rock'},
                    {'name': 'alternative'},
                    {'name': 'indie'}
                ]
            },
            'wiki': {'content': 'Test description'},
            'image': [
                {'#text': 'http://img.jpg', 'size': 'extralarge'}
            ]
        }

        result = self.service._parse_track_info(track_data)

        self.assertEqual(result['name'], 'Test Track')
        self.assertEqual(result['artist'], 'Test Artist')
        self.assertEqual(result['duration'], 240)
        self.assertEqual(result['listeners'], 5000)
        self.assertEqual(result['playcount'], 10000)
        self.assertEqual(result['tags'], ['rock', 'alternative', 'indie'])
        self.assertEqual(result['wiki'], 'Test description')

    def test_get_image_url_prefers_extralarge(self):
        """Тест: выбор изображения предпочитает размер extralarge."""
        images = [
            {'#text': 'http://small.jpg', 'size': 'small'},
            {'#text': 'http://medium.jpg', 'size': 'medium'},
            {'#text': 'http://large.jpg', 'size': 'large'},
            {'#text': 'http://extralarge.jpg', 'size': 'extralarge'}
        ]

        result = self.service._get_image_url(images)
        self.assertEqual(result, 'http://extralarge.jpg')

    def test_get_image_url_fallback(self):
        """Тест: fallback на первое доступное изображение."""
        images = [
            {'#text': '', 'size': 'small'},
            {'#text': 'http://valid.jpg', 'size': 'medium'},
            {'#text': '', 'size': 'large'}
        ]

        result = self.service._get_image_url(images)
        self.assertEqual(result, 'http://valid.jpg')


if __name__ == '__main__':
    unittest.main()
