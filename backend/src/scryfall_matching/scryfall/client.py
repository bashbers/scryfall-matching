from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

BULK_DATA_URL = "https://api.scryfall.com/bulk-data"
ACCEPT_HEADER = "application/json;q=0.9,*/*;q=0.8"
USER_AGENT = "scryfall-matching/0.1 (local card discovery app)"


@dataclass(frozen=True)
class BulkDataExport:
    download_uri: str
    updated_at: datetime
    version: str


class ScryfallClient:
    def __init__(self, timeout_seconds: int) -> None:
        self._timeout_seconds = timeout_seconds

    def oracle_cards_export(self) -> BulkDataExport:
        with httpx.Client(
            timeout=self._timeout_seconds,
            headers={"Accept": ACCEPT_HEADER, "User-Agent": USER_AGENT},
        ) as client:
            response = client.get(BULK_DATA_URL)
            response.raise_for_status()
            payload = response.json()
        data = payload.get("data")
        if not isinstance(data, list):
            raise ValueError("Scryfall bulk-data response has no data array.")
        for item in data:
            if isinstance(item, Mapping) and item.get("type") == "oracle_cards":
                return _parse_export(item)
        raise ValueError("Scryfall bulk-data response has no oracle_cards export.")

    def download(self, export: BulkDataExport, destination: str) -> None:
        with httpx.Client(
            timeout=self._timeout_seconds,
            headers={"Accept": ACCEPT_HEADER, "User-Agent": USER_AGENT},
            follow_redirects=True,
        ) as client:
            with client.stream("GET", export.download_uri) as response:
                response.raise_for_status()
                with open(destination, "wb") as output:
                    for chunk in response.iter_bytes():
                        output.write(chunk)


def _parse_export(item: Mapping[str, Any]) -> BulkDataExport:
    download_uri = item.get("download_uri") or item.get("jsonl_download_uri")
    updated_at = item.get("updated_at")
    if not isinstance(download_uri, str) or not isinstance(updated_at, str):
        raise ValueError("Scryfall oracle_cards export is incomplete.")
    parsed_updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    return BulkDataExport(download_uri, parsed_updated_at, updated_at)
