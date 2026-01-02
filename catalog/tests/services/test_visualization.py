"""
Тесты для сервиса визуализации.
"""
import os
import sys
import unittest
import django
from django.conf import settings

from catalog.services.visualization import VisualizationService

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if not settings.configured:
    settings.configure(
        SECRET_KEY='test-secret-key',
        INSTALLED_APPS=['catalog'],
        USE_TZ=True,
    )
    django.setup()


class TestVisualizationService(unittest.TestCase):
    """Тесты для VisualizationService."""

    def setUp(self):
        self.service = VisualizationService()

    def test_create_genre_popularity_chart_empty_data(self):
        """Тест: создание графика с пустыми данными."""
        result = self.service.create_genre_popularity_chart([])
        self.assertEqual(result, "")

    def test_create_genre_popularity_chart_valid_data(self):
        """Тест: создание графика с валидными данными."""
        test_data = [
            {'name': 'Rock', 'count': 1500},
            {'name': 'Pop', 'count': 1200},
            {'name': 'Jazz', 'count': 800},
        ]

        result = self.service.create_genre_popularity_chart(test_data)

        self.assertIsInstance(result, str)
        self.assertIn('plotly', result.lower())

    def test_create_genre_popularity_chart_limits_to_15(self):
        """Тест: ограничение до 15 жанров в графике."""
        test_data = [
            {'name': f'Genre {i}', 'count': 1000 - i * 10}
            for i in range(20)
        ]

        result = self.service.create_genre_popularity_chart(test_data)

        self.assertIsInstance(result, str)
        self.assertIn('plotly', result.lower())
        self.assertIn('Genre 14', result)
        self.assertNotIn('Genre 15', result)

    def test_create_artist_comparison_chart(self):
        """Тест: создание графика сравнения артистов."""
        test_data = [
            {'name': 'The Beatles', 'listeners': 5000000},
            {'name': 'Queen', 'listeners': 4500000},
        ]

        result = self.service.create_artist_comparison_chart(test_data)
        self.assertIsInstance(result, str)
        self.assertIn('plotly', result.lower())

    def test_create_track_popularity_chart(self):
        """Тест: создание графика популярности треков."""
        test_data = [
            {'name': 'Bohemian Rhapsody', 'artist': 'Queen', 'playcount': 1000000, 'listeners': 500000},
        ]

        result = self.service.create_track_popularity_chart(test_data)
        self.assertIsInstance(result, str)
        self.assertIn('plotly', result.lower())

    def test_create_tag_distribution_chart(self):
        """Тест: создание круговой диаграммы."""
        test_data = [
            {'name': 'Rock', 'count': 40},
            {'name': 'Pop', 'count': 30},
        ]

        result = self.service.create_tag_distribution_chart(test_data)
        self.assertIsInstance(result, str)
        self.assertIn('plotly', result.lower())

    def test_create_genre_comparison_radar(self):
        """Тест: создание радарной диаграммы."""
        test_data = {
            'Rock': {'energy': 8, 'danceability': 6},
            'Jazz': {'energy': 5, 'danceability': 4},
        }

        result = self.service.create_genre_comparison_radar(test_data)
        self.assertIsInstance(result, str)
        self.assertIn('plotly', result.lower())

    def test_create_genre_popularity_chart_with_error(self):
        """Тест: обработка ошибки при создании графика."""
        invalid_data = [{'name': 'Rock'}]

        result = self.service.create_genre_popularity_chart(invalid_data)
        self.assertIsInstance(result, str)


class TestVisualizationServiceEdgeCases(unittest.TestCase):
    """Тесты для крайних случаев."""

    def setUp(self):
        self.service = VisualizationService()

    def test_empty_dict_in_data(self):
        """Тест: обработка пустых словарей в данных."""
        test_data = [
            {},
            {'name': 'Rock', 'count': 100},
        ]

        result = self.service.create_genre_popularity_chart(test_data)
        self.assertIsInstance(result, str)

    def test_negative_values(self):
        """Тест: отрицательные значения в данных."""
        test_data = [
            {'name': 'Rock', 'count': -100},
            {'name': 'Pop', 'count': 0},
        ]

        result = self.service.create_genre_popularity_chart(test_data)
        self.assertIsInstance(result, str)

    def test_unicode_characters(self):
        """Тест: Unicode символы в названиях."""
        test_data = [
            {'name': 'Рок', 'count': 100},
            {'name': 'Pop🎵', 'count': 90},
        ]

        result = self.service.create_genre_popularity_chart(test_data)
        self.assertIsInstance(result, str)


if __name__ == '__main__':
    unittest.main()
