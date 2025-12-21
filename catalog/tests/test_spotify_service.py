import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import requests
from django.test import TestCase

from catalog.services.spotify_service import SpotifyService


class TestSpotifyService(TestCase):
    """Тесты для SpotifyService"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.service = SpotifyService()

        self.sample_track_data = {
            'name': 'Test Track',
            'id': 'track123',
            'artists': [{'id': 'artist123', 'name': 'Test Artist'}],
            'album': {'id': 'album123', 'name': 'Test Album'}
        }

        self.sample_audio_features = {
            'danceability': 0.8,
            'energy': 0.7,
            'valence': 0.6,
            'tempo': 120.0
        }

        self.sample_artist_data = {
            'id': 'artist123',
            'name': 'Test Artist',
            'genres': ['pop', 'rock']
        }

    @patch('os.getenv')
    def test_init_with_credentials(self, mock_getenv):
        """Тест инициализации с учетными данными"""
        mock_getenv.side_effect = lambda key, default=None: {
            'SPOTIFY_CLIENT_ID': 'test_client_id',
            'SPOTIFY_CLIENT_SECRET': 'test_client_secret'
        }.get(key)

        SpotifyService._instance = None
        SpotifyService._initialized = False

        service = SpotifyService()
        self.assertEqual(service.client_id, 'test_client_id')
        self.assertEqual(service.client_secret, 'test_client_secret')

    @patch('os.getenv')
    def test_init_without_credentials(self, mock_getenv):
        """Тест инициализации без учетных данных"""
        mock_getenv.return_value = None

        SpotifyService._instance = None
        SpotifyService._initialized = False

        service = SpotifyService()
        self.assertIsNone(service.client_id)
        self.assertIsNone(service.client_secret)

    def test_singleton_pattern(self):
        """Тест паттерна Singleton"""
        original_instance = SpotifyService._instance

        try:
            SpotifyService._instance = None
            SpotifyService._initialized = False

            instance1 = SpotifyService()
            instance2 = SpotifyService()

            self.assertIs(instance1, instance2)
            self.assertIs(instance1, SpotifyService._instance)
            self.assertIs(instance2, SpotifyService._instance)

        finally:
            SpotifyService._instance = original_instance
            SpotifyService._initialized = bool(original_instance)

    @patch('requests.post')
    def test_get_access_token_success(self, mock_post):
        """Тест успешного получения access token"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_token_123',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response

        SpotifyService._instance = None
        SpotifyService._initialized = False

        service = SpotifyService()
        service.client_id = 'test_id'
        service.client_secret = 'test_secret'

        token = service.get_access_token()

        self.assertEqual(token, 'test_token_123')
        self.assertEqual(service._access_token, 'test_token_123')
        self.assertIsNotNone(service._token_expires)

    @patch('requests.post')
    def test_get_access_token_failure(self, mock_post):
        """Тест неудачного получения access token"""
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        SpotifyService._instance = None
        SpotifyService._initialized = False

        service = SpotifyService()
        service.client_id = 'test_id'
        service.client_secret = 'test_secret'

        token = service.get_access_token()

        self.assertIsNone(token)

    def test_get_access_token_cached(self):
        """Тест использования кэшированного токена"""
        self.service._access_token = 'cached_token'
        self.service._token_expires = datetime.now() + timedelta(hours=1)

        token = self.service.get_access_token()
        self.assertEqual(token, 'cached_token')

    @patch('requests.post')
    def test_get_access_token_expired(self, mock_post):
        """Тест обновления истекшего токена"""
        self.service._access_token = 'old_token'
        self.service._token_expires = datetime.now() - timedelta(minutes=10)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new_token',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response

        self.service.client_id = 'test_id'
        self.service.client_secret = 'test_secret'

        token = self.service.get_access_token()

        self.assertEqual(token, 'new_token')
        self.assertNotEqual(token, 'old_token')

    def test_extract_track_id_from_url_spotify_url(self):
        """Тест извлечения ID из URL Spotify"""
        test_cases = [
            ('https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6', '6rqhFgbbKwnb9MLmUQDhG6'),
            ('https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6?si=abc123', '6rqhFgbbKwnb9MLmUQDhG6'),
            ('https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6&other=param', '6rqhFgbbKwnb9MLmUQDhG6'),
        ]

        for url, expected in test_cases:
            result = self.service.extract_track_id_from_url(url)
            self.assertEqual(result, expected)

    def test_extract_track_id_from_url_spotify_uri(self):
        """Тест извлечения ID из Spotify URI"""
        uri = 'spotify:track:6rqhFgbbKwnb9MLmUQDhG6'
        result = self.service.extract_track_id_from_url(uri)
        self.assertEqual(result, '6rqhFgbbKwnb9MLmUQDhG6')

    def test_extract_track_id_from_url_direct_id(self):
        """Тест извлечения ID (уже ID)"""
        track_id = '6rqhFgbbKwnb9MLmUQDhG6'
        result = self.service.extract_track_id_from_url(track_id)
        self.assertEqual(result, track_id)

    def test_extract_track_id_from_url_invalid(self):
        """Тест извлечения ID из невалидного URL"""
        invalid_urls = [
            'https://open.spotify.com/artist/123',
            'https://youtube.com/watch?v=123',
            'not_a_url',
            ''
        ]

        for url in invalid_urls:
            result = self.service.extract_track_id_from_url(url)
            self.assertIsNone(result)

    @patch.object(SpotifyService, '_make_api_request')
    def test_search_track_success(self, mock_make_request):
        """Тест успешного поиска треков"""
        mock_make_request.return_value = {
            'tracks': {
                'items': [
                    {'name': 'Track 1', 'id': 'id1'},
                    {'name': 'Track 2', 'id': 'id2'}
                ]
            }
        }

        result = self.service.search_track('test query', limit=5)

        self.assertIsNotNone(result)
        self.assertIn('tracks', result)
        self.assertEqual(len(result['tracks']['items']), 2)
        mock_make_request.assert_called_once()

    @patch.object(SpotifyService, '_make_api_request')
    def test_search_track_no_results(self, mock_make_request):
        """Тест поиска без результатов"""
        mock_make_request.return_value = {
            'tracks': {
                'items': []
            }
        }

        result = self.service.search_track('nonexistent query')

        self.assertIsNotNone(result)
        self.assertEqual(len(result['tracks']['items']), 0)

    @patch.object(SpotifyService, '_make_api_request')
    def test_search_track_api_error(self, mock_make_request):
        """Тест ошибки API при поиске"""
        mock_make_request.return_value = None

        result = self.service.search_track('test query')

        self.assertIsNone(result)

    @patch.object(SpotifyService, '_make_api_request')
    def test_get_track_success(self, mock_make_request):
        """Тест успешного получения информации о треке"""
        mock_make_request.return_value = self.sample_track_data

        result = self.service.get_track('track123')

        self.assertEqual(result, self.sample_track_data)
        mock_make_request.assert_called_with('tracks/track123')

    @patch.object(SpotifyService, '_make_api_request')
    def test_get_audio_features_success(self, mock_make_request):
        """Тест успешного получения аудио-характеристик"""
        mock_make_request.return_value = self.sample_audio_features

        result = self.service.get_audio_features('track123')

        self.assertEqual(result, self.sample_audio_features)
        mock_make_request.assert_called_with('audio-features/track123')

    @patch.object(SpotifyService, '_make_api_request')
    def test_get_artist_success(self, mock_make_request):
        """Тест успешного получения информации об артисте"""
        mock_make_request.return_value = self.sample_artist_data

        result = self.service.get_artist('artist123')

        self.assertEqual(result, self.sample_artist_data)
        mock_make_request.assert_called_with('artists/artist123')

    @patch.object(SpotifyService, 'get_track')
    @patch.object(SpotifyService, 'get_audio_features')
    @patch.object(SpotifyService, 'get_artist')
    def test_get_track_full_info_success(self, mock_get_artist, mock_get_audio_features, mock_get_track):
        """Тест успешного получения полной информации о треке"""
        mock_get_track.return_value = self.sample_track_data
        mock_get_audio_features.return_value = self.sample_audio_features
        mock_get_artist.return_value = self.sample_artist_data

        with patch.object(self.service, 'extract_track_id_from_url', return_value='track123'):

            result = self.service.get_track_full_info('track123')

            self.assertIsNotNone(result)
            self.assertIn('track', result)
            self.assertIn('audio_features', result)
            self.assertIn('artist', result)
            self.assertEqual(result['track'], self.sample_track_data)
            self.assertEqual(result['audio_features'], self.sample_audio_features)
            self.assertEqual(result['artist'], self.sample_artist_data)

            mock_get_track.assert_called_with('track123')
            mock_get_audio_features.assert_called_with('track123')
            mock_get_artist.assert_called_with('artist123')

    @patch.object(SpotifyService, 'get_track')
    @patch.object(SpotifyService, 'get_audio_features')
    @patch.object(SpotifyService, 'get_artist')
    def test_get_track_full_info_missing_audio_features(self, mock_get_artist, mock_get_audio_features, mock_get_track):
        """Тест получения информации без аудио-характеристик"""
        mock_get_track.return_value = self.sample_track_data
        mock_get_audio_features.return_value = None
        mock_get_artist.return_value = self.sample_artist_data

        with patch.object(self.service, 'extract_track_id_from_url', return_value='track123'):
            result = self.service.get_track_full_info('track123')

            self.assertIsNotNone(result)
            self.assertIsNone(result['audio_features'])
            self.assertEqual(result['track'], self.sample_track_data)
            self.assertEqual(result['artist'], self.sample_artist_data)

    @patch.object(SpotifyService, '_make_api_request')
    def test_get_track_full_info_invalid_url(self, mock_make_request):
        """Тест получения информации по невалидному URL"""
        with patch.object(self.service, 'extract_track_id_from_url', return_value=None):
            result = self.service.get_track_full_info('invalid_url')

            self.assertIsNone(result)
            mock_make_request.assert_not_called()

    @patch('requests.get')
    def test_check_api_health_success(self, mock_get):
        """Тест проверки здоровья API (успех)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        with patch.object(self.service, 'get_access_token', return_value='test_token'):
            result = self.service.check_api_health()

            self.assertTrue(result)

    @patch('requests.get')
    def test_check_api_health_failure(self, mock_get):
        """Тест проверки здоровья API (неудача)"""
        mock_get.side_effect = requests.exceptions.Timeout()

        with patch.object(self.service, 'get_access_token', return_value='test_token'):
            result = self.service.check_api_health()

            self.assertFalse(result)

    @patch('requests.get')
    def test_check_api_health_no_token(self):
        """Тест проверки здоровья API без токена"""
        with patch.object(self.service, 'get_access_token', return_value=None):
            result = self.service.check_api_health()

            self.assertFalse(result)

    def test_search_with_multiple_types(self):
        """Тест поиска с несколькими типами"""
        with patch.object(self.service, '_make_api_request') as mock_request:
            self.service.search('test', types=['track', 'artist'])

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            params = call_args[1]['params']
            self.assertIn('track', params['type'])
            self.assertIn('artist', params['type'])

    def test_search_with_invalid_types(self):
        """Тест поиска с невалидными типами"""
        with patch.object(self.service, '_make_api_request') as mock_request:
            self.service.search('test', types=['invalid', 'also_invalid'])

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            self.assertEqual(call_args[1]['params']['type'], 'track')

    @patch('requests.request')
    def test_make_api_request_success(self, mock_request):
        """Тест успешного API запроса"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'test'}
        mock_request.return_value = mock_response

        with patch.object(self.service, 'get_access_token', return_value='test_token'):
            result = self.service._make_api_request('test/endpoint')

            self.assertEqual(result, {'data': 'test'})

    @patch('requests.request')
    def test_make_api_request_token_refresh(self, mock_request):
        """Тест обновления токена при 401 ошибке"""
        response_mock = Mock()
        response_mock.status_code = 401

        mock_response_401 = Mock()
        mock_response_401.status_code = 401
        mock_response_401.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "401 Client Error",
            response=response_mock
        )

        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {'data': 'test'}

        mock_request.side_effect = [mock_response_401, mock_response_200]

        token_generator = iter(['old_token', 'new_token'])

        def token_side_effect():
            return next(token_generator)

        with patch.object(self.service, 'get_access_token', side_effect=token_side_effect):
            result = self.service._make_api_request('test/endpoint')

            self.assertEqual(result, {'data': 'test'})
            self.assertEqual(mock_request.call_count, 2)

    @patch('requests.request')
    def test_make_api_request_timeout_retry(self, mock_request):
        """Тест повторных попыток при таймауте"""
        mock_request.side_effect = requests.exceptions.Timeout()

        with patch.object(self.service, 'get_access_token', return_value='test_token'):
            result = self.service._make_api_request('test/endpoint', retries=1)

            self.assertIsNone(result)
            self.assertEqual(mock_request.call_count, 2)

    @patch('requests.request')
    def test_make_api_request_json_error(self, mock_request):
        """Тест ошибки парсинга JSON"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Error", "doc", 0)
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        with patch.object(self.service, 'get_access_token', return_value='test_token'):
            result = self.service._make_api_request('test/endpoint')

            self.assertIsNone(result)

    @patch('os.getenv')
    def test_service_integration(self, mock_getenv):
        """Интеграционный тест сервиса"""
        mock_getenv.side_effect = lambda key, default=None: {
            'SPOTIFY_CLIENT_ID': 'test_id',
            'SPOTIFY_CLIENT_SECRET': 'test_secret'
        }.get(key)

        SpotifyService._instance = None
        SpotifyService._initialized = False

        service = SpotifyService()

        self.assertEqual(service.client_id, 'test_id')
        self.assertEqual(service.client_secret, 'test_secret')

        service2 = SpotifyService()
        self.assertIs(service, service2)


class TestSpotifyServiceURLParsing(TestCase):
    """Дополнительные тесты для парсинга URL"""

    def setUp(self):
        SpotifyService._instance = None
        SpotifyService._initialized = False
        self.service = SpotifyService()

    def test_url_with_query_params(self):
        """Тест URL с различными query параметрами"""
        test_urls = [
            ('https://open.spotify.com/track/abc123?si=xyz&utm_source=test', 'abc123'),
            ('https://open.spotify.com/track/def456?foo=bar', 'def456'),
            ('https://open.spotify.com/track/ghi789#section', 'ghi789'),
            ('https://open.spotify.com/track/jkl012?si=abc&context=xyz&ref=test', 'jkl012'),
        ]

        for url, expected in test_urls:
            result = self.service.extract_track_id_from_url(url)
            self.assertEqual(
                result,
                expected,
                f"URL: '{url}' -> expected: {expected}, got: {result}"
            )

    def test_url_with_subdomain(self):
        """Тест URL с поддоменами"""
        urls = [
            ('https://open.spotify.com/track/123', '123'),
            ('http://open.spotify.com/track/123', '123'),
            ('https://www.open.spotify.com/track/123', '123'),
            ('http://www.open.spotify.com/track/123', '123'),
        ]

        for url, expected in urls:
            result = self.service.extract_track_id_from_url(url)
            self.assertEqual(
                result,
                expected,
                f"URL: '{url}' -> expected: {expected}, got: {result}"
            )

    def test_url_without_scheme(self):
        """Тест URL без схемы (автоматическое добавление https://)"""
        urls = [
            ('open.spotify.com/track/123', '123'),  # Должен работать
            ('www.open.spotify.com/track/456', '456'),  # Должен работать
            ('open.spotify.com/track/789?si=abc', '789'),  # С параметрами
        ]

        for url, expected in urls:
            result = self.service.extract_track_id_from_url(url)
            self.assertEqual(
                result,
                expected,
                f"URL without scheme: '{url}' -> expected: {expected}, got: {result}"
            )

    def test_malformed_urls(self):
        """Тест некорректных URL"""
        urls = [
            ('spotify.com/track/123', '123'),
            ('https://spotify.com/track/123', '123'),
            ('https://open.spotify.com/artist/123', None),  # не трек
            ('https://open.spotify.com/album/123', None),  # не трек
            ('https://open.spotify.com/playlist/123', None),  # не трек
            ('', None),  # пустая строка
            ('   ', None),  # пробелы
            ('invalid_url', None),  # невалидный URL
            (None, None),  # None
        ]

        for url, expected in urls:
            result = self.service.extract_track_id_from_url(url)
            self.assertEqual(
                result,
                expected,
                f"Malformed URL: '{url}' -> expected: {expected}, got: {result}"
            )

    def test_spotify_uri(self):
        """Тест Spotify URI"""
        test_cases = [
            ('spotify:track:6rqhFgbbKwnb9MLmUQDhG6', '6rqhFgbbKwnb9MLmUQDhG6'),
            ('spotify:track:0VjIjW4GlUZAMYd2vXMi3b', '0VjIjW4GlUZAMYd2vXMi3b'),
            ('spotify:track:abc123?si=xyz', 'abc123'),  # с параметрами
        ]

        for uri, expected in test_cases:
            result = self.service.extract_track_id_from_url(uri)
            self.assertEqual(
                result,
                expected,
                f"Spotify URI: '{uri}' -> expected: {expected}, got: {result}"
            )

    def test_direct_track_id(self):
        """Тест прямого ввода track ID"""
        track_ids = [
            ('6rqhFgbbKwnb9MLmUQDhG6', '6rqhFgbbKwnb9MLmUQDhG6'),
            ('0VjIjW4GlUZAMYd2vXMi3b', '0VjIjW4GlUZAMYd2vXMi3b'),
            ('abc123def456ghi789jkl012', 'abc123def456ghi789jkl012'),
            ('short123', 'short123'),
        ]

        for track_id, expected in track_ids:
            result = self.service.extract_track_id_from_url(track_id)
            self.assertEqual(
                result,
                expected,
                f"Direct track ID: '{track_id}' -> expected: {expected}, got: {result}"
            )

    def test_extract_id_from_complex_url(self):
        """Тест извлечения ID из сложного URL"""
        urls = [
            ('https://open.spotify.com/track/0VjIjW4GlUZAMYd2vXMi3b?si=abc&utm_source=copy-link',
             '0VjIjW4GlUZAMYd2vXMi3b'),
            ('spotify:track:0VjIjW4GlUZAMYd2vXMi3b', '0VjIjW4GlUZAMYd2vXMi3b'),
            ('0VjIjW4GlUZAMYd2vXMi3b', '0VjIjW4GlUZAMYd2vXMi3b'),  # уже ID
            ('open.spotify.com/track/0VjIjW4GlUZAMYd2vXMi3b?si=abc', '0VjIjW4GlUZAMYd2vXMi3b'),  # без схемы
        ]

        for url, expected in urls:
            result = self.service.extract_track_id_from_url(url)
            self.assertEqual(
                result,
                expected,
                f"Complex URL: '{url}' -> expected: {expected}, got: {result}"
            )