"""
Сервисы для аналитики и визуализации данных.
"""
from typing import Dict, List, Optional, Tuple
from django.db.models import QuerySet
from ..models import Genre
from .lastfm_service import LastFMService
from .visualization import VisualizationService
from .catalog_service import CatalogService


class AnalyticsService:
    """Сервис для аналитики музыкальных данных."""

    @staticmethod
    def get_analytics_data(time_period: str = 'overall', limit: int = 10) -> Dict:
        """
        Получение данных для аналитики жанров.

        Args:
            time_period: Период анализа (не используется в текущей реализации, оставлен для совместимости)
            limit: Максимальное количество жанров

        Returns:
            Словарь с данными для аналитики
        """
        # Локальная статистика из базы
        local_genres = CatalogService.get_genre_statistics(limit)

        # Топ жанров из Last.fm
        lastfm_genres = AnalyticsService._get_lastfm_top_genres(limit)

        # Создаем графики
        charts = AnalyticsService._create_charts(local_genres, lastfm_genres)

        # Таблица сравнения
        comparison_table = AnalyticsService._create_comparison_table(local_genres, lastfm_genres)

        return {
            'local_genres': local_genres,
            'lastfm_genres': lastfm_genres,
            'charts': charts,
            'genres_table': comparison_table,
            'local_count': len(local_genres),
            'lastfm_count': len(lastfm_genres)
        }

    @staticmethod
    def _get_lastfm_top_genres(limit: int) -> List[Dict]:
        """
        Получение топ жанров из Last.fm.

        Args:
            limit: Максимальное количество жанров

        Returns:
            Список жанров из Last.fm
        """
        try:
            lastfm = LastFMService()
            return lastfm.get_top_tags(limit=limit)
        except ValueError:
            return []

    @staticmethod
    def _create_charts(local_genres: QuerySet, lastfm_genres: List[Dict]) -> List[Tuple]:
        """
        Создание графиков на основе данных.

        Args:
            local_genres: Локальные жанры из базы
            lastfm_genres: Жанры из Last.fm

        Returns:
            Список кортежей (id, title, html_chart)
        """
        charts = []
        viz = VisualizationService()

        # 1. График локальных жанров
        if local_genres:
            local_data = [{
                'name': genre.name,
                'count': genre.track_count or 0,
                'playcount': genre.total_playcount or 0
            } for genre in local_genres]

            chart_html = viz.create_genre_popularity_chart(local_data)
            if chart_html:
                charts.append(('local_genres', 'Популярность жанров в базе', chart_html))

        # 2. График жанров Last.fm
        if lastfm_genres:
            chart_html = viz.create_genre_popularity_chart(lastfm_genres)
            if chart_html:
                charts.append(('lastfm_genres', 'Топ жанров Last.fm', chart_html))

            # 3. Круговая диаграмма распределения
            pie_chart = viz.create_tag_distribution_chart(lastfm_genres)
            if pie_chart:
                charts.append(('distribution', 'Распределение жанров', pie_chart))

        return charts

    @staticmethod
    def _create_comparison_table(local_genres: QuerySet, lastfm_genres: List[Dict]) -> List[Dict]:
        """
        Создание таблицы сравнения локальных и Last.fm жанров.

        Args:
            local_genres: Локальные жанры
            lastfm_genres: Жанры из Last.fm

        Returns:
            Список словарей с данными для таблицы
        """
        table = []

        for local_genre in local_genres:
            # Ищем совпадение в Last.fm
            lastfm_match = next(
                (g for g in lastfm_genres if g['name'].lower() == local_genre.name.lower()),
                None
            )

            table.append({
                'name': local_genre.name,
                'local_tracks': local_genre.track_count,
                'local_artists': local_genre.artist_count,
                'local_playcount': local_genre.total_playcount or 0,
                'lastfm_count': lastfm_match.get('count', 0) if lastfm_match else 0,
                'lastfm_reach': lastfm_match.get('reach', 0) if lastfm_match else 0,
                'match': lastfm_match is not None,
                'match_percentage': AnalyticsService._calculate_match_percentage(
                    local_genre.track_count or 0,
                    lastfm_match.get('count', 0) if lastfm_match else 0
                ) if lastfm_match else 0
            })

        return table

    @staticmethod
    def _calculate_match_percentage(local_count: int, lastfm_count: int) -> float:
        """
        Расчет процента соответствия между локальными и Last.fm данными.

        Args:
            local_count: Количество в локальной базе
            lastfm_count: Количество в Last.fm

        Returns:
            Процент соответствия (0-100)
        """
        if lastfm_count == 0:
            return 0.0

        # Используем минимальное значение как базовое для расчета процента
        min_count = min(local_count, lastfm_count)
        max_count = max(local_count, lastfm_count)

        if max_count == 0:
            return 0.0

        return round((min_count / max_count) * 100, 1)

    @staticmethod
    def get_genre_trend_data(genre_name: str, days_back: int = 30) -> Dict:
        """
        Получение данных о тренде жанра.

        Args:
            genre_name: Название жанра
            days_back: Количество дней для анализа

        Returns:
            Данные о тренде
        """
        # Здесь можно реализовать сбор исторических данных
        # Для примера возвращаем заглушку
        return {
            'genre': genre_name,
            'trend': 'stable',  # rising, falling, stable
            'change_percentage': 0.0,
            'data_points': []
        }

    @staticmethod
    def get_correlation_analysis() -> Dict:
        """
        Анализ корреляции между жанрами.

        Returns:
            Данные о корреляциях
        """
        # Заглушка для будущей реализации
        return {
            'correlations': [],
            'strongest_pair': None,
            'weakest_pair': None
        }