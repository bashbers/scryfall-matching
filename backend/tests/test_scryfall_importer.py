import gzip
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scryfall_matching.cards.domain import CompactCard
from scryfall_matching.cards.repository import InMemoryCardRepository, SwappableCardProvider
from scryfall_matching.scryfall.client import BulkDataExport
from scryfall_matching.scryfall.importer import (
    ScryfallBulkImporter,
    iter_bulk_records,
    iter_json_array,
    map_card,
)


class FakeBulkDataClient:
    def __init__(self, source: str, version: str = "2026-08-04T00:00:00Z") -> None:
        self._source = source
        self._export = BulkDataExport(
            "https://files.example.test/oracle.json",
            datetime(2026, 8, 4, tzinfo=UTC),
            version,
        )

    def oracle_cards_export(self) -> BulkDataExport:
        return self._export

    def download(self, export: BulkDataExport, destination: str) -> None:
        Path(destination).write_text(self._source, encoding="utf-8")


def test_importer_compacts_deduplicates_and_swaps_snapshot(tmp_path: Path) -> None:
    source = json.dumps(
        [
            _single_card("printing-one", "oracle-one", "First Card"),
            _single_card("printing-two", "oracle-one", "First Card"),
            _double_faced_card(),
            _single_card("not-legal", "not-legal", "Not Legal", regular_legal=False),
        ]
    )
    provider = _provider()
    importer = ScryfallBulkImporter(tmp_path, 1, client=FakeBulkDataClient(source))

    result = importer.refresh(provider)

    assert result.status == "updated"
    assert result.imported_cards == 2
    assert provider.statistics().dataset_version == "2026-08-04T00:00:00Z"
    metadata = json.loads((tmp_path / "metadata.json").read_text())
    snapshot_path = tmp_path / metadata["snapshotFile"]
    cards = [json.loads(line) for line in snapshot_path.read_text().splitlines()]
    assert [card["id"] for card in cards] == ["oracle-one", "oracle-double"]
    assert cards[1]["isDoubleSided"] is True
    assert cards[1]["backImageUrl"] == "https://images.example.test/back.jpg"
    assert metadata["importStatus"] == "complete"
    assert metadata["cardCount"] == 2


def test_failed_import_retains_existing_dataset_and_records_failure(tmp_path: Path) -> None:
    provider = _provider()
    old_snapshot = tmp_path / "cards.compact.jsonl"
    old_snapshot.write_text('{"id":"old"}\n', encoding="utf-8")
    old_metadata = tmp_path / "metadata.json"
    old_metadata.write_text('{"datasetVersion":"old","cardCount":1}', encoding="utf-8")
    importer = ScryfallBulkImporter(tmp_path, 1, client=FakeBulkDataClient("not json"))

    with pytest.raises(ValueError, match="JSON array"):
        importer.refresh(provider)

    assert provider.statistics().dataset_version == "old-provider"
    assert old_snapshot.read_text(encoding="utf-8") == '{"id":"old"}\n'
    metadata = json.loads(old_metadata.read_text(encoding="utf-8"))
    assert metadata["importStatus"] == "failed"
    assert metadata["datasetVersion"] == "old"


def test_existing_dataset_version_skips_download(tmp_path: Path) -> None:
    version = "2026-08-04T00:00:00Z"
    source = json.dumps([_single_card("id", "oracle", "Legal")])
    initial_importer = ScryfallBulkImporter(
        tmp_path, 1, client=FakeBulkDataClient(source, version)
    )
    initial_importer.refresh(_provider())
    importer = ScryfallBulkImporter(tmp_path, 1, client=FakeBulkDataClient("[]", version))

    result = importer.refresh(_provider())

    assert result.status == "unchanged"


def test_failed_refresh_keeps_a_previous_snapshot_loadable(tmp_path: Path) -> None:
    source = json.dumps([_single_card("id", "oracle", "Legal")])
    ScryfallBulkImporter(tmp_path, 1, client=FakeBulkDataClient(source)).refresh(_provider())
    importer = ScryfallBulkImporter(
        tmp_path, 1, client=FakeBulkDataClient("not json", "new-version")
    )

    with pytest.raises(ValueError):
        importer.refresh(_provider())

    metadata = json.loads((tmp_path / "metadata.json").read_text())
    assert metadata["importStatus"] == "complete"
    assert metadata["lastAttemptStatus"] == "failed"
    assert (tmp_path / metadata["snapshotFile"]).is_file()


def test_importer_retains_only_active_and_one_rollback_snapshot(tmp_path: Path) -> None:
    provider = _provider()
    for version, name in (("one", "One"), ("two", "Two"), ("three", "Three")):
        source = json.dumps([_single_card(version, version, name)])
        ScryfallBulkImporter(
            tmp_path, 1, client=FakeBulkDataClient(source, version)
        ).refresh(provider)

    snapshots = [path for path in (tmp_path / "snapshots").iterdir() if path.is_dir()]
    assert len(snapshots) == 2


def test_mapper_requires_regular_format_and_handles_layouts() -> None:
    assert map_card(_single_card("id", "oracle", "Legal")) is not None
    assert map_card(_single_card("id", "oracle", "Illegal", regular_legal=False)) is None
    double_faced = map_card(_double_faced_card())
    assert double_faced is not None
    assert double_faced.is_double_sided is True


def test_streaming_parser_handles_small_chunks(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    source.write_text('[{"id":"one"},{"id":"two"}]', encoding="utf-8")

    with source.open(encoding="utf-8") as handle:
        records = list(iter_json_array(handle, chunk_size=3))

    assert records == [{"id": "one"}, {"id": "two"}]


def test_jsonl_gzip_source_is_compacted(tmp_path: Path) -> None:
    source = tmp_path / "oracle.jsonl.gz"
    source.write_bytes(gzip.compress(b'{"id":"one"}\n{"id":"two"}\n'))

    from scryfall_matching.scryfall.importer import _open_bulk_source

    with _open_bulk_source(source) as handle:
        records = list(iter_bulk_records(handle))

    assert records == [{"id": "one"}, {"id": "two"}]


@pytest.mark.parametrize("source", ['[{"id":"one"} {"id":"two"}]', '[{"id":"one"},]'])
def test_streaming_parser_rejects_invalid_separators(tmp_path: Path, source: str) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(source, encoding="utf-8")

    with path.open(encoding="utf-8") as handle, pytest.raises(ValueError):
        list(iter_json_array(handle, chunk_size=2))


def test_mapper_handles_reversible_cards() -> None:
    reversible = _double_faced_card()
    reversible["layout"] = "reversible_card"

    card = map_card(reversible)

    assert card is not None
    assert card.is_double_sided is True


def _provider() -> SwappableCardProvider:
    seed = CompactCard(
        "seed", "Seed", "https://example.test/seed.jpg", None, False, True, "https://scryfall.com"
    )
    return SwappableCardProvider(InMemoryCardRepository((seed,), dataset_version="old-provider"))


def _single_card(
    card_id: str, oracle_id: str, name: str, regular_legal: bool = True
) -> dict[str, object]:
    return {
        "id": card_id,
        "oracle_id": oracle_id,
        "name": name,
        "layout": "normal",
        "scryfall_uri": "https://scryfall.com/card/test/1",
        "image_uris": {"normal": "https://images.example.test/front.jpg"},
        "legalities": {"modern": "legal" if regular_legal else "not_legal", "commander": "legal"},
    }


def _double_faced_card() -> dict[str, object]:
    return {
        "id": "printing-double",
        "oracle_id": "oracle-double",
        "name": "Front // Back",
        "layout": "transform",
        "scryfall_uri": "https://scryfall.com/card/test/2",
        "card_faces": [
            {"image_uris": {"normal": "https://images.example.test/front.jpg"}},
            {"image_uris": {"normal": "https://images.example.test/back.jpg"}},
        ],
        "legalities": {"modern": "legal", "commander": "not_legal"},
    }
