import urllib.request
import json
import time
import logging
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

_CACHE: Dict[str, Tuple[str, float]] = {}
_CACHE_TTL = 3600  # 1 hour

DATASET_IDS = {
    "unemployment_rate":      "d_ca32584c91ee07d091a4ce75fa868414",
    "retrenchment":           "d_000d49cda016c13522d7d5be6a050f59",
    "recruitment_rate":       "d_785903005a276ca9efdeab97707cdbbf",
    "long_term_unemployment": "d_edc7e225d4e7c8f3532e6c329ba2bf79",
    "hdb_resale":             "d_8b84c4ee58e3cfc0ece0d773c8ca6abc",
    "private_property":       "d_43f2a1fee1a0e8aa1ebe875a24a0dfae",
}


class DataGovSGClient:
    OPEN = "https://api-open.data.gov.sg/v1/public/api"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _get(self, url: str) -> dict:
        req = urllib.request.Request(url, headers={
            "x-api-key": self.api_key,
            "User-Agent": "GovDataAnalytics/1.0",
            "Accept": "*/*",
        })
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())

    def fetch_csv(self, dataset_key: str) -> Optional[str]:
        """Download dataset CSV by key. Returns cached result if fresh."""
        dataset_id = DATASET_IDS.get(dataset_key)
        if not dataset_id:
            logger.error(f"Unknown dataset key: {dataset_key}")
            return None

        if dataset_id in _CACHE:
            data, ts = _CACHE[dataset_id]
            if time.time() - ts < _CACHE_TTL:
                logger.info(f"Cache hit: {dataset_key}")
                return data

        try:
            self._get(f"{self.OPEN}/datasets/{dataset_id}/initiate-download")

            download_url = None
            for _ in range(5):
                resp = self._get(f"{self.OPEN}/datasets/{dataset_id}/poll-download")
                download_url = resp.get("data", {}).get("url")
                if download_url:
                    break
                time.sleep(1)

            if not download_url:
                raise ValueError("poll-download returned no URL")

            with urllib.request.urlopen(download_url, timeout=30) as r:
                csv_data = r.read().decode("utf-8")

            _CACHE[dataset_id] = (csv_data, time.time())
            logger.info(f"Downloaded {dataset_key}: {len(csv_data.splitlines())} rows")
            return csv_data

        except Exception as e:
            logger.error(f"DataGovSG fetch failed [{dataset_key}]: {e}")
            return None
