import hashlib
import json
from typing import Dict, List, Optional

import requests
from django.conf import settings

from .base_service import BaseAPIService


class LastFMService(BaseAPIService):
    """Сервис для работы с Last.fm API."""

    def __init__(self, cache_dir: str = ".cache/lastfm"):
        super().__init__(cache_dir)

        self.api_key = getattr(settings, 'LASTFM_API_KEY', '')
        self.shared_secret = getattr(settings, 'LASTFM_SHARED_SECRET', '')

        if not self.api_key or not self.shared_secret:
            raise ValueError("Last.fm API ключи не настроены. Проверьте настройки в .env")

        self.base_url = "https://ws.audioscrobbler.com/2.0/"
        self.last_request_time = 0
        self.min_request_interval = 0.2

    def _sign_request(self, params: Dict) -> str:
        """Создание подписи для запросов, требующих аутентификации."""
        sorted_params = sorted(params.items())

        sig_string = ''.join(f"{k}{v}" for k, v in sorted_params)
        sig_string += self.shared_secret

        return hashlib.md5(sig_string.encode()).hexdigest()

    def _make_request(self, method: str, params: Dict, requires_auth: bool = False) -> Optional[Dict]:
        """
        Выполнение запроса к Last.fm API.

        Args:
            method: Метод API (например, 'track.search')
            params: Параметры запроса
            requires_auth: Требуется ли аутентификация

        Returns:
            Ответ API в виде словаря или None в случае ошибки
        """
        cache_key = self._get_cache_key(method, params)

        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            return cached_data

        self.last_request_time = self._rate_limit(self.last_request_time, self.min_request_interval)

        request_params = {
            'method': method,
            'api_key': self.api_key,
            'format': 'json',
            **params
        }

        if requires_auth:
            request_params['api_sig'] = self._sign_request(request_params)

        try:
            response = requests.get(
                self.base_url,
                params=request_params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                if 'error' in data:
                    print(f"Last.fm API error {data['error']}: {data.get('message', 'Unknown error')}")
                    return None

                self._save_to_cache(cache_key, data)
                return data

            else:
                print(f"HTTP error {response.status_code}: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return None

    def search_track(self, query: str, artist: str = None, limit: int = 30) -> List[Dict]:
        """
        Поиск треков по названию и артисту.

        Args:
            query: Название трека
            artist: Имя артиста (опционально)
            limit: Максимальное количество результатов

        Returns:
            Список найденных треков
        """
        params = {
            'track': query,
            'limit': limit
        }

        if artist:
            params['artist'] = artist

        result = self._make_request('track.search', params)

        if not result or 'results' not in result:
            return []

        tracks = []
        track_matches = result['results'].get('trackmatches', {}).get('track', [])

        for track_data in track_matches:
            track = self._parse_track_search_result(track_data)
            if track:
                tracks.append(track)

        return tracks

    def search_artist(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Поиск артистов по имени.

        Args:
            query: Имя артиста
            limit: Максимальное количество результатов

        Returns:
            Список найденных артистов
        """
        params = {
            'artist': query,
            'limit': limit
        }

        result = self._make_request('artist.search', params)

        if not result or 'results' not in result:
            return []

        artists = []
        artist_matches = result['results'].get('artistmatches', {}).get('artist', [])

        for artist_data in artist_matches:
            artist = self._parse_artist_search_result(artist_data)
            if artist:
                artists.append(artist)

        return artists

    def get_track_info(self, artist: str, track: str) -> Optional[Dict]:
        """
        Получение полной информации о треке.

        Args:
            artist: Имя артиста
            track: Название трека

        Returns:
            Информация о треке или None
        """
        params = {
            'artist': artist,
            'track': track,
            'autocorrect': 1
        }

        result = self._make_request('track.getInfo', params)

        if not result or 'track' not in result:
            return None

        return self._parse_track_info(result['track'])

    def get_artist_info(self, artist: str) -> Optional[Dict]:
        """
        Получение полной информации об артисте.

        Args:
            artist: Имя артиста

        Returns:
            Информация об артисте или None
        """
        params = {
            'artist': artist,
            'autocorrect': 1
        }

        result = self._make_request('artist.getInfo', params)

        if not result or 'artist' not in result:
            return None

        return self._parse_artist_info(result['artist'])

    def get_top_tracks_by_tag(self, tag: str, limit: int = 50) -> List[Dict]:
        """
        Получение топовых треков по тегу (жанру).

        Args:
            tag: Тег/жанр
            limit: Количество треков

        Returns:
            Список треков
        """
        params = {
            'tag': tag,
            'limit': limit
        }

        result = self._make_request('tag.getTopTracks', params)

        if not result or 'tracks' not in result:
            return []

        tracks = []
        for track_data in result['tracks'].get('track', []):
            track = self._parse_track_from_tag(track_data)
            if track:
                tracks.append(track)

        return tracks

    def get_top_tags(self, limit: int = 100) -> List[Dict]:
        """
        Получение топовых тегов (жанров).

        Args:
            limit: Количество тегов

        Returns:
            Список тегов
        """

        params = {
            'limit': limit
        }

        result = self._make_request('chart.getTopTags', params)

        if not result or 'tags' not in result:
            return []

        tags = []
        for tag_data in result['tags'].get('tag', []):
            tag = {
                'name': tag_data.get('name', ''),
                'count': int(tag_data.get('count', 0)),
                'reach': int(tag_data.get('reach', 0)),
                'url': tag_data.get('url', '')
            }
            tags.append(tag)

        return tags

    def _parse_track_search_result(self, track_data: Dict) -> Optional[Dict]:
        """Парсинг результата поиска трека."""
        try:
            return {
                'name': track_data.get('name', ''),
                'artist': track_data.get('artist', ''),
                'url': track_data.get('url', ''),
                'listeners': int(track_data.get('listeners', 0)),
                'image': self._get_image_url(track_data.get('image', [])),
            }
        except (KeyError, ValueError):
            return None

    def _parse_artist_search_result(self, artist_data: Dict) -> Optional[Dict]:
        """Парсинг результата поиска артиста."""
        try:
            return {
                'name': artist_data.get('name', ''),
                'artist': artist_data.get('artist', ''),
                'url': artist_data.get('url', ''),
                'listeners': int(artist_data.get('listeners', 0)),
                'image': self._get_image_url(artist_data.get('image', [])),
            }
        except (KeyError, ValueError):
            return None

    def _parse_track_info(self, track_data: Dict) -> Dict:
        """Парсинг полной информации о треке."""
        track = {
            'name': track_data.get('name', ''),
            'artist': track_data.get('artist', {}).get('name', ''),
            'url': track_data.get('url', ''),
            'duration': int(track_data.get('duration', 0)) // 1000 if track_data.get('duration') else None,
            'listeners': int(track_data.get('listeners', 0)),
            'playcount': int(track_data.get('playcount', 0)),
            'album': track_data.get('album', {}).get('title', '') if track_data.get('album') else '',
            'tags': [],
            'wiki': track_data.get('wiki', {}).get('content', '') if track_data.get('wiki') else '',
            'image': self._get_image_url(track_data.get('image', []))
        }

        if 'toptags' in track_data and 'tag' in track_data['toptags']:
            tags = track_data['toptags']['tag']
            if isinstance(tags, list):
                track['tags'] = [tag.get('name', '') for tag in tags[:10]]
            elif isinstance(tags, dict):
                track['tags'] = [tags.get('name', '')]

        return track

    def _parse_artist_info(self, artist_data: Dict) -> Dict:
        """Парсинг полной информации об артисте."""
        artist = {
            'name': artist_data.get('name', ''),
            'url': artist_data.get('url', ''),
            'listeners': int(artist_data.get('stats', {}).get('listeners', 0)),
            'playcount': int(artist_data.get('stats', {}).get('playcount', 0)),
            'tags': [],
            'bio': artist_data.get('bio', {}).get('content', '') if artist_data.get('bio') else '',
            'image': self._get_image_url(artist_data.get('image', []))
        }

        if 'tags' in artist_data and 'tag' in artist_data['tags']:
            tags = artist_data['tags']['tag']
            if isinstance(tags, list):
                artist['tags'] = [tag.get('name', '') for tag in tags[:10]]
            elif isinstance(tags, dict):
                artist['tags'] = [tags.get('name', '')]

        return artist

    def _parse_track_from_tag(self, track_data: Dict) -> Optional[Dict]:
        """Парсинг трека из списка по тегу."""
        try:
            return {
                'name': track_data.get('name', ''),
                'artist': track_data.get('artist', {}).get('name', ''),
                'url': track_data.get('url', ''),
                'listeners': int(track_data.get('listeners', 0)),
                'playcount': int(track_data.get('playcount', 0)),
                'image': self._get_image_url(track_data.get('image', [])),
            }
        except (KeyError, ValueError):
            return None

    def _get_image_url(self, images: List[Dict]) -> str:
        """Извлечение URL изображения нужного размера."""
        if not images:
            return ''

        for size in ['extralarge', 'large', 'medium', 'small']:
            for img in images:
                if img.get('#text') and img.get('size') == size:
                    return img['#text']

        for img in images:
            if img.get('#text'):
                return img['#text']

        return ''
