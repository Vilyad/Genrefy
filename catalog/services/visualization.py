import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any


class VisualizationService:
    """Сервис для создания графиков и визуализаций."""

    @staticmethod
    def create_genre_popularity_chart(genres_data: List[Dict]) -> str:
        """
        Создание графика популярности жанров.

        Args:
            genres_data: Список жанров с данными о популярности

        Returns:
            HTML код графика
        """
        if not genres_data:
            return ""
        
        df = pd.DataFrame(genres_data)
        
        df = df.sort_values('count', ascending=False).head(15)
        
        fig = px.bar(
            df,
            x='name',
            y='count',
            title='Топ-15 музыкальных жанров по популярности',
            labels={'name': 'Жанр', 'count': 'Количество треков'},
            color='count',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            plot_bgcolor='white',
            showlegend=False
        )
        
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    @staticmethod
    def create_artist_comparison_chart(artists_data: List[Dict]) -> str:
        """
        Создание графика сравнения артистов.

        Args:
            artists_data: Список артистов с данными о слушателях

        Returns:
            HTML код графика
        """
        if not artists_data:
            return ""

        df = pd.DataFrame(artists_data)
        df = df.sort_values('listeners', ascending=False).head(10)

        fig = px.bar(
            df,
            x='name',
            y='listeners',
            title='Топ-10 артистов по количеству слушателей',
            labels={'name': 'Артист', 'listeners': 'Слушатели'},
            color='listeners',
            color_continuous_scale='Plasma'
        )

        fig.update_layout(
            xaxis_tickangle=-45,
            plot_bgcolor='white',
            showlegend=False
        )

        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    @staticmethod
    def create_track_popularity_chart(tracks_data: List[Dict]) -> str:
        """
        Создание графика популярности треков.

        Args:
            tracks_data: Список треков с данными о прослушиваниях

        Returns:
            HTML код графика
        """
        if not tracks_data:
            return ""

        df = pd.DataFrame(tracks_data)
        df = df.sort_values('playcount', ascending=False).head(15)

        fig = px.scatter(
            df,
            x='playcount',
            y='listeners',
            size='playcount',
            color='playcount',
            hover_name='name',
            hover_data=['artist'],
            title='Популярность треков',
            labels={
                'playcount': 'Количество прослушиваний',
                'listeners': 'Уникальные слушатели'
            },
            size_max=50
        )

        fig.update_layout(
            plot_bgcolor='white',
            showlegend=False
        )

        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    @staticmethod
    def create_tag_distribution_chart(tags_data: List[Dict]) -> str:
        """
        Создание круговой диаграммы распределения тегов.

        Args:
            tags_data: Список тегов с количеством

        Returns:
            HTML код графика
        """
        if not tags_data:
            return ""

        df = pd.DataFrame(tags_data)
        df = df.sort_values('count', ascending=False).head(10)

        fig = px.pie(
            df,
            values='count',
            names='name',
            title='Распределение топ-10 жанров',
            hole=0.3
        )

        fig.update_traces(
            textposition='inside',
            textinfo='percent+label'
        )

        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    @staticmethod
    def create_genre_comparison_radar(genres_stats: Dict[str, Dict]) -> str:
        """
        Создание радарной диаграммы для сравнения жанров.

        Args:
            genres_stats: Статистика по жанрам

        Returns:
            HTML код графика
        """
        if not genres_stats:
            return ""

        fig = go.Figure()

        for genre_name, stats in genres_stats.items():
            categories = list(stats.keys())
            values = list(stats.values())

            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name=genre_name
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max([max(v.values()) for v in genres_stats.values()]) * 1.1]
                )),
            showlegend=True,
            title='Сравнение характеристик жанров'
        )

        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    