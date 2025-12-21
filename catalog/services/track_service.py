from typing import Tuple, Optional, Dict, Any
from django.contrib import messages
from ..models import Artist, Track, Genre
from .spotify_service import spotify_service
import logging

logger = logging.getLogger(__name__)


class TrackService:
    """Сервис для бизнес-логики работы с треками"""
    @staticmethod
    def add_track_from_spotify(spotify_url: str, genre: Genre) -> Tuple[Optional[Track], str]:
        """
        Добавляет трек из Spotify по URL

        Возвращает: (трек, сообщение)
        """
        if not spotify_url or not genre:
            return None, "Отсутствуют обязательные данные"

        try:
            track_info = spotify_service.get_track_full_info(spotify_url)
            if not track_info or 'track' not in track_info:
                return None, "Не удалось получить данные о треке из Spotify"

            track_data = track_info['track']
            audio_features = track_info.get('audio_features')
            artist_data = track_info.get('artist')

            track_id = spotify_service.extract_track_id_from_url(spotify_url)
            if not track_id:
                return None, "Не удалось извлечь ID трека из URL"

            existing_track = Track.objects.filter(spotify_id=track_id).first()
            if existing_track:
                return existing_track, f"Трек '{existing_track.title}' уже существует в базе"

            artist = None
            if track_data.get('artists'):
                main_artist = track_data['artists'][0]
                artist, created = Artist.objects.get_or_create(
                    spotify_id=main_artist['id'],
                    defaults={
                        'name': main_artist['name'],
                        'spotify_url': main_artist.get('external_urls', {}).get('spotify', '')
                    }
                )

                artist.genres.add(genre)

            audio_features_data = {}
            if audio_features:
                audio_features_data = {
                    "acousticness": audio_features.get('acousticness', 0),
                    "danceability": audio_features.get('danceability', 0),
                    "duration_ms": audio_features.get('duration_ms', 0),
                    "energy": audio_features.get('energy', 0),
                    "instrumentalness": audio_features.get('instrumentalness', 0),
                    "key": audio_features.get('key', 0),
                    "liveness": audio_features.get('liveness', 0),
                    "loudness": audio_features.get('loudness', 0),
                    "mode": audio_features.get('mode', 0),
                    "speechiness": audio_features.get('speechiness', 0),
                    "tempo": audio_features.get('tempo', 0),
                    "time_signature": audio_features.get('time_signature', 0),
                    "valence": audio_features.get('valence', 0),
                }

            album = track_data.get('album', {})
            album_images = album.get('images', [])
            album_image_url = ''
            if album_images and len(album_images) > 0:
                album_image_url = album_images[0].get('url', '')

            track = Track.objects.create(
                title=track_data['name'],
                artist=artist,
                spotify_id=track_id,
                spotify_url=track_data.get('external_urls', {}).get('spotify', ''),
                preview_url=track_data.get('preview_url', ''),
                duration_ms=track_data.get('duration_ms', 0),
                album_name=album.get('name', ''),
                album_image_url=album_image_url,
                popularity=track_data.get('popularity', 0),
                audio_features=audio_features_data,
            )

            return track, f"Трек '{track.title}' успешно добавлен!"

        except Exception as e:
            logger.error(f"Ошибка при добавлении трека: {str(e)}", exc_info=True)
            return None, f"Ошибка при обработке трека: {str(e)}"

    @staticmethod
    def search_tracks_in_spotify(query: str, limit: int = 10) -> Optional[Dict[str, Any]]:
        """Поиск треков в Spotify"""
        try:
            return spotify_service.search_track(query, limit=limit)
        except Exception as e:
            logger.error(f"Ошибка поиска в Spotify: {str(e)}")
            return None

    @staticmethod
    def get_track_details(track_id: str) -> Optional[Dict[str, Any]]:
        """Получение детальной информации о треке"""
        try:
            return spotify_service.get_track_full_info(track_id)
        except Exception as e:
            logger.error(f"Ошибка получения деталей трека: {str(e)}")
            return None

    @staticmethod
    def get_track_by_spotify_id(spotify_id: str) -> Optional[Track]:
        """Поиск трека в базе по Spotify ID"""
        try:
            return Track.objects.filter(spotify_id=spotify_id).first()
        except Exception as e:
            logger.error(f"Ошибка поиска трека в базе: {str(e)}")
            return None

    @staticmethod
    def get_tracks_by_genre(genre: Genre, limit: int = 20):
        """Получение треков по жанру"""
        return Track.objects.filter(artist__genres=genre).select_related('artist')[:limit]