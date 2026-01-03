import plotly.graph_objects as go
import plotly.offline as pyo
from django.db.models import Count

from catalog.models import Genre
from .lastfm_service import LastFMService


class AnalyticsService:

    @staticmethod
    def get_analytics_data(time_period='overall', limit=10):
        """Получение данных для аналитики."""
        local_genres = AnalyticsService._get_local_genres()
        lastfm_genres = AnalyticsService._get_lastfm_genres(limit)

        charts = AnalyticsService._create_charts(local_genres, lastfm_genres)
        comparison_table = AnalyticsService._create_comparison_table(local_genres, lastfm_genres)

        return {
            'charts': charts,
            'genres_table': comparison_table,
            'local_count': len(local_genres),
            'lastfm_count': len(lastfm_genres),
        }

    @staticmethod
    def _get_local_genres():
        """Получение жанров из локальной базы с статистикой."""
        genres = Genre.objects.annotate(
            annotated_track_count=Count('artists__tracks', distinct=True),
            annotated_artist_count=Count('artists', distinct=True)
        ).order_by('-annotated_track_count')

        return genres

    @staticmethod
    def _get_lastfm_genres(limit):
        """Получение популярных жанров из Last.fm."""
        client = LastFMService()

        try:
            tags = client.get_top_tags(limit=limit)
            return tags
        except Exception as e:
            print(f"Error getting Last.fm genres: {e}")
            return []

    @staticmethod
    def _create_charts(local_genres, lastfm_genres):
        """Создание графиков для отображения."""
        charts = []

        if local_genres and len(local_genres) > 0:
            local_chart_html = AnalyticsService._create_local_genres_chart(local_genres)
            charts.append(('local_genres', 'Локальные жанры (по трекам)', local_chart_html))

        if lastfm_genres and len(lastfm_genres) > 0:
            lastfm_chart_html = AnalyticsService._create_lastfm_genres_chart(lastfm_genres)
            charts.append(('lastfm_genres', 'Last.fm популярность жанров', lastfm_chart_html))

        if local_genres and lastfm_genres and len(local_genres) > 0 and len(lastfm_genres) > 0:
            distribution_chart = AnalyticsService._create_distribution_chart(local_genres, lastfm_genres)
            if distribution_chart:
                charts.append(('distribution', 'Распределение жанров', distribution_chart))

        return charts

    @staticmethod
    def _create_local_genres_chart(genres):
        """Создание графика локальных жанров."""
        top_genres = list(genres)[:10] if hasattr(genres, '__iter__') else []

        if not top_genres:
            return ""

        genre_names = [genre.name for genre in top_genres]
        track_counts = [genre.annotated_track_count for genre in top_genres]
        artist_counts = [genre.annotated_artist_count for genre in top_genres]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=genre_names,
            y=track_counts,
            name='Треки',
            marker_color='rgb(55, 83, 109)'
        ))

        fig.add_trace(go.Bar(
            x=genre_names,
            y=artist_counts,
            name='Артисты',
            marker_color='rgb(26, 118, 255)'
        ))

        fig.update_layout(
            title='Топ локальных жанров',
            xaxis_tickangle=-45,
            barmode='group',
            height=400,
            showlegend=True
        )

        return pyo.plot(fig, output_type='div', include_plotlyjs=False)

    @staticmethod
    def _create_lastfm_genres_chart(lastfm_genres):
        """Создание графика Last.fm жанров."""
        if not lastfm_genres:
            return ""

        top_genres = lastfm_genres[:10]

        genre_names = [tag.get('name', '') for tag in top_genres]
        reach_values = [int(tag.get('reach', 0)) for tag in top_genres]
        tag_counts = [int(tag.get('count', 0)) for tag in top_genres]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=genre_names,
            y=reach_values,
            name='Охват',
            marker_color='rgb(255, 140, 0)'
        ))

        fig.add_trace(go.Bar(
            x=genre_names,
            y=tag_counts,
            name='Теги',
            marker_color='rgb(50, 205, 50)'
        ))

        fig.update_layout(
            title='Топ жанров Last.fm',
            xaxis_tickangle=-45,
            barmode='group',
            height=400,
            showlegend=True
        )

        return pyo.plot(fig, output_type='div', include_plotlyjs=False)

    @staticmethod
    def _create_distribution_chart(local_genres, lastfm_genres):
        """Создание графика распределения."""
        try:
            local_list = list(local_genres)
            top_local = {genre.name: genre.annotated_track_count for genre in local_list[:5]}
            top_lastfm = {}

            for tag in lastfm_genres[:5]:
                name = tag.get('name', '')
                if name:
                    top_lastfm[name] = int(tag.get('count', 0))

            all_genres = set(list(top_local.keys()) + list(top_lastfm.keys()))

            local_values = [top_local.get(genre, 0) for genre in all_genres]
            lastfm_values = [top_lastfm.get(genre, 0) for genre in all_genres]

            max_local = max(local_values) if local_values else 1
            max_lastfm = max(lastfm_values) if lastfm_values else 1

            normalized_local = [v / max_local * 100 for v in local_values]
            normalized_lastfm = [v / max_lastfm * 100 for v in lastfm_values]

            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=list(all_genres),
                y=normalized_local,
                name='Локальные',
                marker_color='rgb(55, 83, 109)'
            ))

            fig.add_trace(go.Bar(
                x=list(all_genres),
                y=normalized_lastfm,
                name='Last.fm',
                marker_color='rgb(255, 140, 0)'
            ))

            fig.update_layout(
                title='Сравнение популярности жанров',
                xaxis_tickangle=-45,
                barmode='group',
                height=400,
                showlegend=True,
                yaxis_title='Нормализованная популярность (%)'
            )

            return pyo.plot(fig, output_type='div', include_plotlyjs=False)
        except Exception as e:
            print(f"Error creating distribution chart: {e}")
            return ""

    @staticmethod
    def _create_comparison_table(local_genres, lastfm_genres):
        """Создание таблицы сравнения жанров."""
        comparison_data = []

        local_list = list(local_genres)

        local_dict = {genre.name.lower(): genre for genre in local_list}
        lastfm_dict = {}

        for tag in lastfm_genres:
            name = tag.get('name', '')
            if name:
                lastfm_dict[name.lower()] = tag

        common_genres = set(local_dict.keys()) & set(lastfm_dict.keys())

        for genre_name in sorted(common_genres)[:20]:
            local_genre = local_dict.get(genre_name)
            lastfm_tag = lastfm_dict.get(genre_name)

            if local_genre and lastfm_tag:
                comparison_data.append({
                    'name': local_genre.name,
                    'local_tracks': local_genre.annotated_track_count,
                    'local_artists': local_genre.annotated_artist_count,
                    'lastfm_count': lastfm_tag.get('count', 0),
                    'lastfm_reach': lastfm_tag.get('reach', 0),
                    'match': True,
                    'match_percentage': 100
                })

        local_only = set(local_dict.keys()) - set(lastfm_dict.keys())
        for genre_name in sorted(local_only)[:10]:
            local_genre = local_dict.get(genre_name)
            if local_genre:
                comparison_data.append({
                    'name': local_genre.name,
                    'local_tracks': local_genre.annotated_track_count,
                    'local_artists': local_genre.annotated_artist_count,
                    'lastfm_count': 0,
                    'lastfm_reach': 0,
                    'match': False,
                    'match_percentage': 0
                })

        lastfm_only = set(lastfm_dict.keys()) - set(local_dict.keys())
        for genre_name in sorted(lastfm_only)[:10]:
            lastfm_tag = lastfm_dict.get(genre_name)
            if lastfm_tag:
                comparison_data.append({
                    'name': lastfm_tag.get('name', ''),
                    'local_tracks': 0,
                    'local_artists': 0,
                    'lastfm_count': lastfm_tag.get('count', 0),
                    'lastfm_reach': lastfm_tag.get('reach', 0),
                    'match': False,
                    'match_percentage': 0
                })

        return comparison_data
