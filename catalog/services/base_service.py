import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional


class BaseAPIService:
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_key(self, method: str, params: dict) -> str:
        key_str = f"{method}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _load_from_cache(self, key: str, ttl_days: int = 7) -> Optional[Dict]:
        cache_file = Path(self.cache_dir) / f"{key}.json"

        if cache_file.exists():
            file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if file_age < timedelta(days=ttl_days):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass
        return None

    def _save_to_cache(self, key: str, data: Dict):
        cache_file = Path(self.cache_dir) / f"{key}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _rate_limit(self, last_request_time: float, min_interval: float = 0.2) -> float:
        current_time = time.time()
        time_since_last = current_time - last_request_time

        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            time.sleep(wait_time)
            return time.time()
        else:
            return current_time
