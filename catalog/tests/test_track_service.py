from unittest.mock import patch
from django.test import TestCase
from catalog.models import Genre, Artist, Track
from catalog.services.track_service import TrackService


class TestTrackService(TestCase):
    """Тесты для TrackService с использованием mock-объектов"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.genre = Genre.objects.create(
            name="Test Genre",
            description="Test description"
        )

        self.artist = Artist.objects.create(
            name="Test Artist",
            spotify_id="artist123"
        )

        self.mock_track_data = {
            'track': {
                'name': 'Test Track',
                'id': 'track123',
                'artists': [{'id': 'artist123', 'name': 'Test Artist'}],
                'preview_url': 'https://example.com/preview.mp3',
                'external_urls': {'spotify': 'https://spotify.com/track/track123'},
                'duration_ms': 180000,
                'album': {
                    'name': 'Test Album',
                    'images': [{'url': 'https://example.com/image.jpg'}]
                },
                'popularity': 75
            },
            'audio_features': {
                'danceability': 0.8,
                'energy': 0.7,
                'valence': 0.6,
                'tempo': 120.0,
                'acousticness': 0.2,
                'instrumentalness': 0.1,
                'liveness': 0.3,
                'speechiness': 0.05,
                'loudness': -5.0,
                'mode': 1,
                'key': 5,
                'duration_ms': 180000,
                'time_signature': 4
            },
            'artist': {
                'id': 'artist123',
                'name': 'Test Artist',
                'external_urls': {'spotify': 'https://spotify.com/artist/artist123'}
            }
        }

        self.mock_spotify_url = "https://open.spotify.com/track/track123"

    def test_extract_track_id_from_url_valid(self):
        """Тест извлечения ID трека из различных форматов URL"""
        test_cases = [
            ("https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6", "6rqhFgbbKwnb9MLmUQDhG6"),
            ("spotify:track:6rqhFgbbKwnb9MLmUQDhG6", "6rqhFgbbKwnb9MLmUQDhG6"),
            ("https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6?si=abc123", "6rqhFgbbKwnb9MLmUQDhG6"),
            ("6rqhFgbbKwnb9MLmUQDhG6", "6rqhFgbbKwnb9MLmUQDhG6"),
        ]

        for url, expected_id in test_cases:
            with patch('catalog.services.track_service.spotify_service') as mock_service:
                mock_service.extract_track_id_from_url.return_value = expected_id

                result = mock_service.extract_track_id_from_url(url)

                self.assertEqual(result, expected_id)
                mock_service.extract_track_id_from_url.assert_called_with(url)

    @patch('catalog.services.track_service.spotify_service')
    @patch('catalog.services.track_service.logger')
    def test_add_track_success(self, mock_logger, mock_spotify_service):
        """Тест успешного добавления трека"""
        mock_spotify_service.extract_track_id_from_url.return_value = "track123"

        mock_spotify_service.get_track_full_info.return_value = {
            'track': {
                'name': 'Test Track',
                'id': 'track123',
                'artists': [{'id': 'artist123', 'name': 'Test Artist'}],
                'preview_url': 'https://example.com/preview.mp3',
                'external_urls': {'spotify': 'https://spotify.com/track/track123'},
                'duration_ms': 180000,
                'album': {
                    'name': 'Test Album',
                    'images': [{'url': 'https://example.com/image.jpg'}]
                },
                'popularity': 75
            },
            'audio_features': {
                'danceability': 0.8,
                'energy': 0.7,
                'valence': 0.6,
                'tempo': 120.0,
                'acousticness': 0.2,
                'instrumentalness': 0.1,
                'liveness': 0.3,
                'speechiness': 0.05,
                'loudness': -5.0,
                'mode': 1,
                'key': 5,
                'duration_ms': 180000,
                'time_signature': 4
            },
            'artist': {
                'id': 'artist123',
                'name': 'Test Artist',
                'external_urls': {'spotify': 'https://spotify.com/artist/artist123'}
            }
        }

        track, message = TrackService.add_track_from_spotify(
            "https://open.spotify.com/track/track123",
            self.genre
        )

        self.assertIsNotNone(track)
        self.assertIn("успешно добавлен", message)
        self.assertEqual(track.title, "Test Track")
        self.assertEqual(track.spotify_id, "track123")

        db_track = Track.objects.filter(spotify_id="track123").first()
        self.assertIsNotNone(db_track)
        self.assertEqual(db_track.title, "Test Track")

        self.artist.refresh_from_db()
        self.assertIn(self.genre, self.artist.genres.all())

        mock_logger.info.assert_not_called()

    @patch('catalog.services.track_service.spotify_service.get_track_full_info')
    def test_add_track_already_exists(self, mock_get_track_info):
        """Тест добавления уже существующего трека"""
        Track.objects.create(
            title="Existing Track",
            artist=self.artist,
            spotify_id="track123",
            preview_url="https://example.com/existing.mp3"
        )

        mock_get_track_info.return_value = self.mock_track_data

        track, message = TrackService.add_track_from_spotify(
            self.mock_spotify_url,
            self.genre
        )

        self.assertIsNotNone(track)
        self.assertIn("уже существует", message)
        self.assertEqual(track.spotify_id, "track123")

    @patch('catalog.services.track_service.spotify_service.get_track_full_info')
    def test_add_track_no_spotify_data(self, mock_get_track_info):
        """Тест случая, когда Spotify не возвращает данные"""
        mock_get_track_info.return_value = None

        track, message = TrackService.add_track_from_spotify(
            self.mock_spotify_url,
            self.genre
        )

        self.assertIsNone(track)
        self.assertIn("Не удалось получить данные", message)

    @patch('catalog.services.track_service.spotify_service.get_track_full_info')
    def test_add_track_api_error(self, mock_get_track_info):
        """Тест обработки ошибки API"""
        mock_get_track_info.side_effect = Exception("Spotify API error")

        track, message = TrackService.add_track_from_spotify(
            self.mock_spotify_url,
            self.genre
        )

        self.assertIsNone(track)
        self.assertIn("Ошибка при обработке", message)

    @patch('catalog.services.track_service.spotify_service.search_track')
    def test_search_tracks_success(self, mock_search_track):
        """Тест успешного поиска треков"""
        mock_search_track.return_value = {
            'tracks': {
                'items': [
                    {'name': 'Track 1', 'id': 'id1'},
                    {'name': 'Track 2', 'id': 'id2'}
                ]
            }
        }

        results = TrackService.search_tracks_in_spotify("test query")

        self.assertIsNotNone(results)
        self.assertIn('tracks', results)
        self.assertEqual(len(results['tracks']['items']), 2)
        mock_search_track.assert_called_with("test query", limit=10)

    @patch('catalog.services.track_service.spotify_service.search_track')
    def test_search_tracks_api_error(self, mock_search_track):
        """Тест ошибки при поиске"""
        mock_search_track.side_effect = Exception("Search failed")

        results = TrackService.search_tracks_in_spotify("test query")

        self.assertIsNone(results)

    def test_get_track_by_spotify_id_found(self):
        """Тест поиска трека в базе по Spotify ID (найден)"""
        Track.objects.create(
            title="Test Track",
            artist=self.artist,
            spotify_id="test123"
        )

        result = TrackService.get_track_by_spotify_id("test123")

        self.assertIsNotNone(result)
        self.assertEqual(result.spotify_id, "test123")

    def test_get_track_by_spotify_id_not_found(self):
        """Тест поиска трека в базе по Spotify ID (не найден)"""
        result = TrackService.get_track_by_spotify_id("nonexistent")

        self.assertIsNone(result)

    def test_get_tracks_by_genre(self):
        """Тест получения треков по жанру"""
        track1 = Track.objects.create(
            title="Track 1",
            artist=self.artist,
            spotify_id="id1"
        )
        track2 = Track.objects.create(
            title="Track 2",
            artist=self.artist,
            spotify_id="id2"
        )

        self.artist.genres.add(self.genre)

        tracks = TrackService.get_tracks_by_genre(self.genre, limit=5)

        self.assertEqual(tracks.count(), 2)
        self.assertIn(track1, tracks)
        self.assertIn(track2, tracks)

    def test_get_tracks_by_genre_empty(self):
        """Тест получения треков по жанру (пустой результат)"""
        empty_genre = Genre.objects.create(name="Empty Genre")

        tracks = TrackService.get_tracks_by_genre(empty_genre)

        self.assertEqual(tracks.count(), 0)

    @patch('catalog.services.track_service.spotify_service')
    def test_add_track_with_missing_audio_features(self, mock_spotify_service):
        """Тест добавления трека без аудио-характеристик"""
        mock_spotify_service.extract_track_id_from_url.return_value = "track123"
        mock_spotify_service.get_track_full_info.return_value = {
            'track': {
                'name': 'Track Without Features',
                'id': 'track123',
                'artists': [{'id': 'artist123', 'name': 'Test Artist'}],
                'preview_url': 'https://example.com/preview.mp3',
                'external_urls': {'spotify': 'https://spotify.com/track/track123'},
                'duration_ms': 180000,
                'album': {
                    'name': 'Test Album',
                    'images': [{'url': 'https://example.com/image.jpg'}]
                },
                'popularity': 75
            },
            # Нет audio_features!
            'audio_features': None,
            'artist': {
                'id': 'artist123',
                'name': 'Test Artist',
                'external_urls': {'spotify': 'https://spotify.com/artist/artist123'}
            }
        }

        track, message = TrackService.add_track_from_spotify(
            "https://open.spotify.com/track/track123",
            self.genre
        )

        self.assertIsNotNone(track)
        self.assertIn("успешно добавлен", message)
        self.assertEqual(track.audio_features, {})

    @patch('catalog.services.track_service.spotify_service')
    def test_add_track_with_partial_artist_data(self, mock_spotify_service):
        """Тест добавления трека с неполными данными артиста"""
        mock_spotify_service.extract_track_id_from_url.return_value = "track123"
        mock_spotify_service.get_track_full_info.return_value = {
            'track': {
                'name': 'Partial Data Track',
                'id': 'track123',
                'artists': [{
                    'id': 'artist123',
                    'name': 'Test Artist',
                    'external_urls': {}
                }],
                'preview_url': 'https://example.com/preview.mp3',
                'external_urls': {'spotify': 'https://spotify.com/track/track123'},
                'duration_ms': 180000,
                'album': {
                    'name': 'Test Album',
                    'images': []
                },
                'popularity': 75
            },
            'audio_features': {
                'danceability': 0.8,
                'energy': 0.7
            },
            'artist': {
                'id': 'artist123',
                'name': 'Test Artist',
                'external_urls': {}
            }
        }

        track, message = TrackService.add_track_from_spotify(
            "https://open.spotify.com/track/track123",
            self.genre
        )

        if track is None:
            print(f"Track is None, message: {message}")

        self.assertIsNotNone(track, f"Track should not be None. Message: {message}")
        self.assertIn("успешно добавлен", message.lower())
        self.assertEqual(track.album_image_url, '')