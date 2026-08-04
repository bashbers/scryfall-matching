import json
from pathlib import Path

from fastapi.testclient import TestClient

from scryfall_matching.cards.domain import CompactCard
from scryfall_matching.cards.repository import InMemoryCardRepository
from scryfall_matching.core.openapi import write_openapi_contract
from scryfall_matching.core.settings import Settings
from scryfall_matching.main import app, create_app


def test_application_metadata() -> None:
    assert app.title == "Scryfall Matching API"
    assert app.version == "0.1.0"


def test_random_cards_returns_exactly_five_unique_cards() -> None:
    settings = _test_settings()
    settings = Settings(
        data_path=settings.data_path,
        batch_size=99,
        scryfall_timeout_seconds=settings.scryfall_timeout_seconds,
        scryfall_update_interval_hours=settings.scryfall_update_interval_hours,
        log_level=settings.log_level,
    )
    test_app = create_app(settings)
    test_app.state.card_provider = InMemoryCardRepository(
        _cards(6), dataset_version="test-snapshot"
    )
    client = TestClient(test_app)

    response = client.get("/api/v1/cards/random")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["cards"]) == 5
    assert len({card["id"] for card in payload["cards"]}) == 5
    assert {
        "id",
        "name",
        "frontImageUrl",
        "backImageUrl",
        "isDoubleSided",
        "commanderLegal",
        "scryfallUrl",
    }.issubset(payload["cards"][0])
    assert all(card["commanderLegal"] for card in payload["cards"])


def test_random_cards_returns_error_when_full_batch_is_unavailable() -> None:
    test_app = create_app(_test_settings())
    test_app.state.card_provider = InMemoryCardRepository(
        _cards(4),
        dataset_version="test-too-small",
    )
    client = TestClient(test_app)

    response = client.get("/api/v1/cards/random")

    assert response.status_code == 503
    assert response.json()["code"] == "cards_unavailable"


def test_live_health_does_not_depend_on_card_repository() -> None:
    test_app = create_app(_test_settings())
    test_app.state.card_provider = object()
    client = TestClient(test_app)

    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "live"}


def test_frontend_development_origin_is_allowed_by_cors() -> None:
    client = TestClient(create_app(_test_settings()))

    response = client.get("/api/v1/health/live", headers={"Origin": "http://localhost:5173"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_ready_health_reports_repository_statistics() -> None:
    test_app = create_app(_test_settings())
    test_app.state.card_provider = InMemoryCardRepository(
        _cards(6), dataset_version="test-snapshot"
    )
    client = TestClient(test_app)

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["datasetVersion"] == "test-snapshot"
    assert payload["cardCount"] == 6
    assert payload["loadedAt"] is not None


def test_ready_health_returns_503_when_repository_is_empty() -> None:
    test_app = create_app(_test_settings())
    test_app.state.card_provider = InMemoryCardRepository(
        (),
        dataset_version="empty-test",
    )
    client = TestClient(test_app)

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "empty"


def test_openapi_contract_can_be_exported(tmp_path: Path) -> None:
    output_path = tmp_path / "openapi.json"

    write_openapi_contract(create_app(_test_settings()), output_path)

    generated_contract = json.loads(output_path.read_text(encoding="utf-8"))
    checked_in_contract = json.loads(Path("openapi.json").read_text(encoding="utf-8"))
    assert generated_contract == checked_in_contract


def test_checked_in_openapi_contract_contains_phase_1_endpoints() -> None:
    contract = json.loads(Path("openapi.json").read_text(encoding="utf-8"))

    assert "/api/v1/cards/random" in contract["paths"]
    cards_schema = contract["components"]["schemas"]["RandomCardsResponse"]["properties"][
        "cards"
    ]
    assert cards_schema["minItems"] == 5
    assert cards_schema["maxItems"] == 5


def _test_settings() -> Settings:
    return Settings(
        data_path="/tmp/scryfall-matching-test",
        batch_size=5,
        scryfall_timeout_seconds=30,
        scryfall_update_interval_hours=24,
        log_level="INFO",
    )


def _cards(count: int) -> tuple[CompactCard, ...]:
    return tuple(
        CompactCard(
            id=f"test-card-{index}",
            name=f"Test Card {index}",
            front_image_url=f"https://example.test/cards/{index}.jpg",
            back_image_url=None,
            is_double_sided=False,
            commander_legal=True,
            scryfall_url=f"https://scryfall.com/card/test/{index}",
        )
        for index in range(count)
    )
