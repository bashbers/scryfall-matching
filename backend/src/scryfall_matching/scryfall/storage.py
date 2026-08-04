import json
import os
from collections.abc import Iterable
from datetime import datetime
from hashlib import sha256
from pathlib import Path

from scryfall_matching.cards.domain import CompactCard
from scryfall_matching.cards.repository import InMemoryCardRepository

COMPACT_FILENAME = "cards.compact.jsonl"
METADATA_FILENAME = "metadata.json"


def load_repository(data_directory: Path) -> InMemoryCardRepository | None:
    metadata_path = data_directory / METADATA_FILENAME
    if not metadata_path.is_file():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        version = metadata["datasetVersion"]
        expected_checksum = metadata["compactFileSha256"]
        snapshot_file = metadata["snapshotFile"]
        loaded_at = datetime.fromisoformat(metadata["updatedAt"].replace("Z", "+00:00"))
        if metadata["importStatus"] != "complete" or not isinstance(expected_checksum, str):
            return None
        if not isinstance(snapshot_file, str):
            return None
        cards_path = _snapshot_path(data_directory, snapshot_file)
        if not cards_path.is_file():
            return None
        if compact_file_checksum(cards_path) != expected_checksum:
            return None
        cards = tuple(read_cards(cards_path))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, OSError):
        return None
    if not isinstance(version, str) or not cards:
        return None
    return InMemoryCardRepository(cards, dataset_version=version, loaded_at=loaded_at)


def write_metadata(path: Path, metadata: dict[str, object]) -> None:
    temporary_path = path.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary_path, path)


def compact_file_checksum(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_file_for_checksum(checksum: str) -> str:
    return "snapshots/" + checksum + "/" + COMPACT_FILENAME


def _snapshot_path(data_directory: Path, snapshot_file: str) -> Path:
    candidate = (data_directory / snapshot_file).resolve()
    data_root = data_directory.resolve()
    if data_root not in candidate.parents:
        raise ValueError("Snapshot file must stay inside DATA_PATH.")
    return candidate


def serialize_card(card: CompactCard) -> str:
    return json.dumps(
        {
            "backImageUrl": card.back_image_url,
            "commanderLegal": card.commander_legal,
            "frontImageUrl": card.front_image_url,
            "id": card.id,
            "isDoubleSided": card.is_double_sided,
            "name": card.name,
            "scryfallUrl": card.scryfall_url,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def read_cards(path: Path) -> Iterable[CompactCard]:
    with path.open(encoding="utf-8") as source:
        for line in source:
            payload = json.loads(line)
            yield CompactCard(
                id=payload["id"],
                name=payload["name"],
                front_image_url=payload["frontImageUrl"],
                back_image_url=payload["backImageUrl"],
                is_double_sided=payload["isDoubleSided"],
                commander_legal=payload["commanderLegal"],
                scryfall_url=payload["scryfallUrl"],
            )
