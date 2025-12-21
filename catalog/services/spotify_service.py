import json
import os
import requests
import base64
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs

import requests.exceptions
from django.conf import settings

logger = logging.getLogger(__name__)


class SpotifyService:
    _instance = None
    _access_token = None
    _token_expires = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
            self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

            if not self.client_id or not self.client_secret:
                logger.warning("Spotify credentials not found in environment variables")

            self.token_url = "https://accounts.spotify.com/api/token"
            self.api_base_url = "https://api.spotify.com/v1/"
            self.default_market = "RU"
            self._initialized = True

    def _get_auth_headers(self) -> Dict[str, str]:
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

        return {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def check_api_health(self) -> bool:
        token = self.get_access_token()
        if not token:
            logger.error("Cannot get access token")
            return False

        try:
            response = requests.get(
                f"{self.api_base_url}me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            return response.status_code in [200, 401, 403]
        except:
            return False

    def _make_api_request(self, endpoint: str, method: str = "GET",
                          params: Optional[Dict] = None,
                          data: Optional[Dict] = None,
                          retries: int = 2) -> Optional[Dict[str, Any]]:
        token = self.get_access_token()
        if not token:
            return None

        url = f"{self.api_base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}

        for attempt in range(retries + 1):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    timeout=10
                )
                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout:
                if attempt < retries:
                    logger.warning(f"Timeout, retry {attempt + 1}/{retries}")
                    continue
                else:
                    logger.error(f"Request timeout after {retries} retries: {url}")
                    return None

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    logger.info("Token expired, refreshing...")
                    self._access_token = None
                    token = self.get_access_token()
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
                        continue
                    logger.error(f"HTTP error {e.response.status_code}: {e}")
                    return None

            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed: {e}, URL: {url}")
                return None
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return None

    def get_access_token(self) -> Optional[str]:
        if (self._access_token and self._token_expires and
                datetime.now() < self._token_expires):
            return self._access_token

        data = {"grant_type": "client_credentials"}
        headers = self._get_auth_headers()

        try:
            response = requests.post(
                self.token_url,
                headers=headers,
                data=data,
                timeout=10
            )
            response.raise_for_status()

            token_data = response.json()
            self._access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)

            self._token_expires = datetime.now() + timedelta(seconds=expires_in - 300)

            logger.info("Successfully obtained Spotify access token")
            return self._access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Spotify token: {e}")
            return None
        except KeyError as e:
            logger.error(f"Invalid token response format: {e}")
            return None

    def search_track(self, query: str, limit: int = 10, market: Optional[str] = None) -> Optional[Dict]:
        params = {
            "q": query,
            "type": "track",
            "limit": limit,
            "market": market or self.default_market
        }

        return self._make_api_request("search", params=params)

    def search(self, query: str, types: List[str] = None, limit: int = 10, market: Optional[str] = None) -> Optional[Dict]:
        if types is None:
            types = ["track"]

        valid_types = {"track", "artist", "album", "playlist"}
        types = [t for t in types if t in valid_types]

        if not types:
            logger.warning(f"No valid types provided, using default 'track'")
            types = ["track"]

        params = {
            "q": query,
            "type": ",".join(types),
            "limit": limit,
            "market": market or self.default_market
        }

        return self._make_api_request("search", params=params)

    def get_track(self, track_id: str) -> Optional[Dict]:
        return self._make_api_request(f"tracks/{track_id}")

    def get_audio_features(self, track_id: str) -> Optional[Dict]:
        return self._make_api_request(f"audio-features/{track_id}")

    def get_artist(self, artist_id: str) -> Optional[Dict]:
        return self._make_api_request(f"artists/{artist_id}")

    def get_album(self, album_id: str) -> Optional[Dict]:
        return self._make_api_request(f"albums/{album_id}")

    def extract_track_id_from_url(self, url: str) -> Optional[str]:
        if len(url) == 22 and url.isalnum():
            return url

        parsed_url = urlparse(url)

        if url.startswith("spotify:track:"):
            return url.split("spotify:track:")[-1].split("?")[0]

        if "open.spotify.com/track/" in url:
            path_parts = parsed_url.path.split("/")
            if len(path_parts) >= 3:
                track_id = path_parts[2]
                return track_id.split("?")[0]

        query_params = parse_qs(parsed_url.query)
        if 'track' in query_params:
            return query_params['track'][0]

        logger.warning(f"Could not extract track ID from URL: {url}")
        return None

    def get_track_full_info(self, track_id_or_url: str) -> Optional[Dict]:
        track_id = self.extract_track_id_from_url(track_id_or_url)
        if not track_id:
            return None

        track_info = self.get_track(track_id)
        if not track_info:
            return None

        audio_features = self.get_audio_features(track_id)

        artist_info = None
        if track_info.get('artists'):
            main_artist_id = track_info['artists'][0]['id']
            artist_info = self.get_artist(main_artist_id)

        combined_info = {
            'track': track_info,
            'audio_features': audio_features,
            'artist': artist_info
        }

        return combined_info


spotify_service = SpotifyService()
