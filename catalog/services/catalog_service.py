"""
Сервисы для работы с основными моделями каталога.
"""
from typing import Dict, List, Optional, Tuple

from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404

from .lastfm_service import LastFMService
from ..models import Genre, Artist, Track, Favorite


class CatalogService:
    """Сервис для работы с каталогом музыки."""

    @staticmethod
    def get_genre_statistics(limit: int = 100, search_query: str = None):
        """
        Получение статистики по жанрам с возможностью поиска.
        """
        queryset = Genre.objects.annotate(
            annotated_track_count=Count('artists__tracks', distinct=True),
            annotated_artist_count=Count('artists', distinct=True),
            total_playcount=Sum('artists__tracks__lastfm_playcount')
        )

        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        return queryset.order_by('-total_playcount')[:limit]

    @staticmethod
    def get_genre_with_details(pk: int):
        """
        Получение жанра с детальной информацией.
        """
        genre = get_object_or_404(Genre, pk=pk)

        artists_count = Artist.objects.filter(genres=genre).count()
        tracks_count = Track.objects.filter(artist__genres=genre).count()

        artists = Artist.objects.filter(genres=genre)[:10]
        tracks = Track.objects.filter(artist__genres=genre).select_related('artist')[:20]

        genre.artist_count = artists_count
        genre.track_count = tracks_count

        top_tracks = []
        try:
            lastfm = LastFMService()
            top_tracks = lastfm.get_top_tracks_by_tag(
                tag=genre.lastfm_tag or genre.name.lower(),
                limit=20
            )
        except ValueError:
            pass

        return genre, artists, tracks, top_tracks

    @staticmethod
    def search_in_lastfm(query: str, search_type: str = 'track', limit: int = 20) -> List[Dict]:
        """
        Поиск в Last.fm.

        Args:
            query: Поисковый запрос
            search_type: Тип поиска ('track' или 'artist')
            limit: Максимальное количество результатов

        Returns:
            Список результатов
        """
        try:
            lastfm = LastFMService()

            if search_type == 'track':
                return lastfm.search_track(query, limit=limit)
            else:
                return lastfm.search_artist(query, limit=limit)
        except ValueError:
            return []

    @staticmethod
    def get_or_create_track_from_lastfm(track_name: str, artist_name: str) -> Tuple[Optional[Track], bool]:
        """
        Получение или создание трека из Last.fm.

        Args:
            track_name: Название трека
            artist_name: Имя исполнителя

        Returns:
            Кортеж (трек, создан_ли_новый)
        """
        try:
            lastfm = LastFMService()
            track_info = lastfm.get_track_info(artist=artist_name, track=track_name)

            if not track_info:
                return None, False

            artist, artist_created = Artist.objects.get_or_create(
                name=artist_name,
                defaults={'lastfm_listeners': track_info.get('listeners', 0)}
            )

            artist_info = lastfm.get_artist_info(artist_name)
            if artist_info:
                artist.lastfm_listeners = artist_info.get('listeners', 0)
                artist.lastfm_playcount = artist_info.get('playcount', 0)
                artist.save()

            track, track_created = Track.objects.get_or_create(
                title=track_name,
                artist=artist,
                defaults={
                    'lastfm_listeners': track_info.get('listeners', 0),
                    'lastfm_playcount': track_info.get('playcount', 0),
                    'lastfm_url': track_info.get('url', ''),
                    'duration': track_info.get('duration'),
                    'album': track_info.get('album', ''),
                    'tags': track_info.get('tags', []),
                    'lastfm_data': track_info
                }
            )

            for tag_name in track_info.get('tags', [])[:5]:
                genre, created = Genre.objects.get_or_create(
                    name=tag_name.title(),
                    defaults={'lastfm_tag': tag_name.lower()}
                )
                artist.genres.add(genre)

            track.link_genres_from_tags()

            return track, track_created

        except Exception as e:
            print(f"Error in get_or_create_track_from_lastfm: {e}")
            return None, False

    @staticmethod
    def update_track_from_lastfm(track: Track) -> bool:
        """
        Обновление данных трека из Last.fm.

        Args:
            track: Объект трека для обновления

        Returns:
            True если обновлено успешно
        """
        try:
            lastfm = LastFMService()
            track_info = lastfm.get_track_info(
                artist=track.artist.name,
                track=track.title
            )

            if track_info:
                track.lastfm_listeners = track_info.get('listeners', 0)
                track.lastfm_playcount = track_info.get('playcount', 0)
                track.tags = track_info.get('tags', [])
                track.set_lastfm_data(track_info)
                track.save()
                return True
        except Exception as e:
            print(f"Error updating track from Last.fm: {e}")

        return False

    @staticmethod
    def add_to_favorites(user, track):
        """Добавление жанров трека в избранное пользователя."""
        if not user.is_authenticated:
            return 0, 0

        genres = track.artist.genres.all()
        added = 0
        existing = 0

        for genre in genres:
            item_id_str = str(genre.id)

            exists = Favorite.objects.filter(
                user=user,
                item_type='genre',
                item_id=item_id_str
            ).exists()

            if not exists:
                Favorite.objects.create(
                    user=user,
                    item_type='genre',
                    item_id=item_id_str
                )
                added += 1
            else:
                existing += 1

        return added, existing

    @staticmethod
    def get_user_favorites_with_recommendations(user):
        """Получение избранных жанров пользователя с рекомендациями."""
        favorite_genres_ids_str = Favorite.objects.filter(
            user=user,
            item_type='genre'
        ).values_list('item_id', flat=True)

        favorite_genres_ids = []
        for id_str in favorite_genres_ids_str:
            try:
                favorite_genres_ids.append(int(id_str))
            except (ValueError, TypeError):
                continue

        favorite_genres = Genre.objects.filter(id__in=favorite_genres_ids)

        recommendations = {
            'artists': Artist.objects.filter(genres__in=favorite_genres).distinct()[:4],
            'tracks': Track.objects.filter(artist__genres__in=favorite_genres).distinct()[:5]
        }

        return {
            'favorite_genres': favorite_genres,
            'recommendations': recommendations
        }

    @staticmethod
    def get_or_create_artist_from_lastfm(artist_name: str) -> Tuple[Optional[Artist], bool]:
        """
        Получение или создание исполнителя из Last.fm.

        Args:
            artist_name: Имя исполнителя

        Returns:
            Кортеж (исполнитель, создан_ли_новый)
        """
        try:
            lastfm = LastFMService()
            artist_info = lastfm.get_artist_info(artist_name)

            if not artist_info:
                return None, False

            artist, created = Artist.objects.get_or_create(
                name=artist_name,
                defaults={
                    'lastfm_listeners': artist_info.get('listeners', 0),
                    'lastfm_playcount': artist_info.get('playcount', 0),
                    'lastfm_url': artist_info.get('url', '')
                }
            )

            for tag_name in artist_info.get('tags', [])[:5]:
                genre, _ = Genre.objects.get_or_create(
                    name=tag_name.title(),
                    defaults={'lastfm_tag': tag_name.lower()}
                )
                artist.genres.add(genre)

            return artist, created

        except Exception as e:
            print(f"Error in get_or_create_artist_from_lastfm: {e}")
            return None, False
