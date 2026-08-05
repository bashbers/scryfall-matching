import gzip
import json
import os
import re
import shutil
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, TextIO

from scryfall_matching.cards.domain import CompactCard
from scryfall_matching.cards.repository import InMemoryCardRepository, SwappableCardProvider
from scryfall_matching.scryfall.client import BulkDataExport, ScryfallClient
from scryfall_matching.scryfall.storage import (
    COMPACT_FILENAME,
    METADATA_FILENAME,
    compact_file_checksum,
    load_repository,
    read_cards,
    serialize_card,
    snapshot_file_for_checksum,
    write_metadata,
)

REGULAR_FORMATS = frozenset(
    {
        "standard",
        "pioneer",
        "modern",
        "legacy",
        "pauper",
        "alchemy",
        "explorer",
        "historic",
        "timeless",
    }
)
DOUBLE_SIDED_LAYOUTS = frozenset({"transform", "modal_dfc", "meld", "reversible_card"})
MAX_INVALID_RECORDS = 100
MAX_INVALID_RECORD_RATIO = 0.01


class BulkDataClient(Protocol):
    def oracle_cards_export(self) -> BulkDataExport:
        """Return the current oracle_cards export descriptor."""

    def download(self, export: BulkDataExport, destination: str) -> None:
        """Download the export to destination without exposing partial data."""


@dataclass(frozen=True)
class ImportResult:
    status: str
    imported_cards: int
    skipped_records: int
    dataset_version: str | None


class ScryfallBulkImporter:
    def __init__(
        self,
        data_directory: Path,
        timeout_seconds: int,
        client: BulkDataClient | None = None,
    ) -> None:
        self._data_directory = data_directory
        self._client = client or ScryfallClient(timeout_seconds)

    def refresh(self, provider: SwappableCardProvider) -> ImportResult:
        self._data_directory.mkdir(parents=True, exist_ok=True)
        export = self._client.oracle_cards_export()
        existing_metadata = _read_metadata(self._data_directory / METADATA_FILENAME)
        existing_repository = load_repository(self._data_directory)
        if (
            existing_metadata.get("datasetVersion") == export.version
            and existing_repository is not None
        ):
            provider.replace(existing_repository)
            return ImportResult("unchanged", 0, 0, export.version)

        source_path = self._data_directory / "oracle_cards.download.tmp"
        compact_path = self._data_directory / (COMPACT_FILENAME + ".tmp")
        try:
            self._client.download(export, str(source_path))
            imported_cards, skipped_records = _compact_source(source_path, compact_path)
            _validate_import(imported_cards, skipped_records)
            repository = _load_temporary_repository(compact_path, export.version)
            checksum = compact_file_checksum(compact_path)
            snapshot_file = snapshot_file_for_checksum(checksum)
            snapshot_path = self._data_directory / snapshot_file
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            os.replace(compact_path, snapshot_path)
            write_metadata(
                self._data_directory / METADATA_FILENAME,
                {
                    "cardCount": imported_cards,
                    "compactFileSha256": checksum,
                    "datasetVersion": export.version,
                    "importStatus": "complete",
                    "skippedRecords": skipped_records,
                    "snapshotFile": snapshot_file,
                    "updatedAt": _isoformat(export.updated_at),
                },
            )
            provider.replace(repository)
            _prune_snapshots(
                self._data_directory,
                active_snapshot=snapshot_file,
                rollback_snapshot=existing_metadata.get("snapshotFile"),
            )
            return ImportResult("updated", imported_cards, skipped_records, export.version)
        except Exception as error:
            self._record_failure(existing_metadata, export, error)
            raise
        finally:
            for temporary_path in (source_path, compact_path):
                if temporary_path.exists():
                    temporary_path.unlink()

    def _record_failure(
        self,
        existing_metadata: Mapping[str, Any],
        export: BulkDataExport,
        error: Exception,
    ) -> None:
        metadata = dict(existing_metadata)
        metadata.update(
            {
                "lastAttemptStatus": "failed",
                "lastAttemptedVersion": export.version,
                "lastError": str(error),
                "lastAttemptedAt": _isoformat(datetime.now(UTC)),
            }
        )
        if metadata.get("importStatus") != "complete":
            metadata["importStatus"] = "failed"
        write_metadata(self._data_directory / METADATA_FILENAME, metadata)


def map_card(record: Mapping[str, Any]) -> CompactCard | None:
    legalities = record.get("legalities")
    if not isinstance(legalities, Mapping) or not _is_legal_in_regular_format(legalities):
        return None
    card_id = record.get("oracle_id") or record.get("id")
    name = record.get("name")
    scryfall_uri = record.get("scryfall_uri")
    if not all(isinstance(value, str) and value for value in (card_id, name, scryfall_uri)):
        raise ValueError("Card lacks an id, name, or Scryfall URL.")
    assert isinstance(card_id, str)
    assert isinstance(name, str)
    assert isinstance(scryfall_uri, str)
    layout = record.get("layout")
    if layout in DOUBLE_SIDED_LAYOUTS:
        faces = record.get("card_faces")
        if not isinstance(faces, list) or len(faces) < 2:
            raise ValueError("Double-sided card lacks two faces.")
        front_image = _face_image(faces[0])
        back_image = _face_image(faces[1])
        return CompactCard(
            card_id,
            name,
            front_image,
            back_image,
            True,
            legalities.get("commander") == "legal",
            scryfall_uri,
        )
    image_uris = record.get("image_uris")
    if not isinstance(image_uris, Mapping) or not isinstance(image_uris.get("normal"), str):
        raise ValueError("Single-sided card lacks a normal image.")
    front_image_url = image_uris["normal"]
    assert isinstance(front_image_url, str)
    return CompactCard(
        card_id,
        name,
        front_image_url,
        None,
        False,
        legalities.get("commander") == "legal",
        scryfall_uri,
    )


def iter_json_array(source: TextIO, chunk_size: int = 65536) -> Iterator[Mapping[str, Any]]:
    """Yield an array of objects without loading the Scryfall export into memory."""
    decoder = json.JSONDecoder()
    buffer = ""
    position = 0
    started = False
    expect_value = True
    after_comma = False
    while True:
        chunk = source.read(chunk_size)
        if chunk:
            buffer += chunk
        elif not buffer[position:].strip():
            break
        while True:
            while position < len(buffer) and buffer[position] in " \t\r\n":
                position += 1
            if not started:
                if position >= len(buffer):
                    break
                if buffer[position] != "[":
                    raise ValueError("Bulk source must be a JSON array.")
                started = True
                position += 1
                continue
            if position >= len(buffer):
                break
            if expect_value and buffer[position] == "]":
                if after_comma:
                    raise ValueError("Bulk source has a trailing comma.")
                position += 1
                _verify_trailing_content(source, buffer[position:])
                return
            if not expect_value:
                if buffer[position] == "]":
                    position += 1
                    _verify_trailing_content(source, buffer[position:])
                    return
                if buffer[position] != ",":
                    raise ValueError("Bulk source has no comma between records.")
                position += 1
                expect_value = True
                after_comma = True
                continue
            try:
                value, end = decoder.raw_decode(buffer, position)
            except json.JSONDecodeError:
                break
            if not isinstance(value, Mapping):
                raise ValueError("Bulk source contains a non-object record.")
            position = end
            expect_value = False
            after_comma = False
            yield value
        if position:
            buffer = buffer[position:]
            position = 0
        if not chunk:
            raise ValueError("Bulk source ended before its JSON array was complete.")
    if not started:
        raise ValueError("Bulk source is empty.")
    raise ValueError("Bulk source ended before its JSON array was complete.")


def iter_bulk_records(source: TextIO) -> Iterator[Mapping[str, Any]]:
    first_character = source.read(1)
    source.seek(0)
    if first_character == "[":
        yield from iter_json_array(source)
        return
    if first_character == "{":
        for line in source:
            value = json.loads(line)
            if not isinstance(value, Mapping):
                raise ValueError("Bulk source contains a non-object record.")
            yield value
        return
    raise ValueError("Bulk source must be a JSON array or JSONL object stream.")


def _compact_source(source_path: Path, compact_path: Path) -> tuple[int, int]:
    seen_keys = set()
    imported_cards = 0
    skipped_records = 0
    with (
        _open_bulk_source(source_path) as source,
        compact_path.open("w", encoding="utf-8") as output,
    ):
        for record in iter_bulk_records(source):
            try:
                card = map_card(record)
            except KeyError, TypeError, ValueError:
                skipped_records += 1
                continue
            if card is None:
                continue
            dedupe_key = _dedupe_key(record, card)
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            output.write(serialize_card(card) + "\n")
            imported_cards += 1
    return imported_cards, skipped_records


def _load_temporary_repository(path: Path, dataset_version: str) -> InMemoryCardRepository:
    cards = tuple(read_cards(path))
    if not cards:
        raise ValueError("Compact snapshot contains no cards.")
    return InMemoryCardRepository(cards, dataset_version=dataset_version)


def _dedupe_key(record: Mapping[str, Any], card: CompactCard) -> str:
    oracle_id = record.get("oracle_id")
    if isinstance(oracle_id, str) and oracle_id:
        return "oracle:" + oracle_id
    return "name:" + card.name.casefold()


def _face_image(face: Any) -> str:
    if not isinstance(face, Mapping):
        raise ValueError("Card face is invalid.")
    image_uris = face.get("image_uris")
    if not isinstance(image_uris, Mapping) or not isinstance(image_uris.get("normal"), str):
        raise ValueError("Card face lacks a normal image.")
    normal_image = image_uris["normal"]
    assert isinstance(normal_image, str)
    return normal_image


def _is_legal_in_regular_format(legalities: Mapping[str, Any]) -> bool:
    return any(legalities.get(format_name) == "legal" for format_name in REGULAR_FORMATS)


def _validate_import(imported_cards: int, skipped_records: int) -> None:
    total_records = imported_cards + skipped_records
    if not imported_cards:
        raise ValueError("Import produced no eligible cards.")
    if (
        skipped_records > MAX_INVALID_RECORDS
        and skipped_records / total_records > MAX_INVALID_RECORD_RATIO
    ):
        raise ValueError("Import exceeded its invalid-record threshold.")


def _read_metadata(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _isoformat(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _verify_trailing_content(source: TextIO, remainder: str) -> None:
    if remainder.strip() or source.read().strip():
        raise ValueError("Bulk source contains trailing content.")


def _open_bulk_source(path: Path) -> TextIO:
    with path.open("rb") as source:
        is_gzip = source.read(2) == b"\x1f\x8b"
    if is_gzip:
        return gzip.open(path, mode="rt", encoding="utf-8")
    return path.open(encoding="utf-8")


def _prune_snapshots(
    data_directory: Path,
    active_snapshot: str,
    rollback_snapshot: Any,
) -> None:
    """Best-effort retention of the active snapshot and one rollback snapshot."""
    keep_names = {Path(active_snapshot).parent.name}
    if isinstance(rollback_snapshot, str):
        keep_names.add(Path(rollback_snapshot).parent.name)
    snapshots_directory = data_directory / "snapshots"
    try:
        for candidate in snapshots_directory.iterdir():
            if candidate.name in keep_names or not re.fullmatch(r"[0-9a-f]{64}", candidate.name):
                continue
            if candidate.is_dir() and not candidate.is_symlink():
                shutil.rmtree(candidate)
    except OSError:
        return None
