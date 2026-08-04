import random
from collections.abc import Iterable
from datetime import UTC, datetime
from threading import RLock

from scryfall_matching.cards.domain import CompactCard, RepositoryStatistics, RepositoryStatus
from scryfall_matching.cards.errors import CardsUnavailableError
from scryfall_matching.cards.provider import CardProvider


class InMemoryCardRepository(CardProvider):
    def __init__(
        self,
        cards: Iterable[CompactCard],
        *,
        dataset_version: str,
        loaded_at: datetime | None = None,
    ) -> None:
        unique_cards = tuple({card.id: card for card in cards}.values())
        self._cards = unique_cards
        self._dataset_version = dataset_version
        self._loaded_at = loaded_at or datetime.now(UTC)

    def get_random_batch(self, batch_size: int) -> tuple[CompactCard, ...]:
        if batch_size < 1:
            raise ValueError("batch_size must be positive")

        if len(self._cards) < batch_size:
            raise CardsUnavailableError(
                f"Repository contains {len(self._cards)} cards, but {batch_size} are required."
            )

        return tuple(random.sample(self._cards, k=batch_size))

    def reload(self) -> None:
        return None

    def statistics(self) -> RepositoryStatistics:
        status: RepositoryStatus = "ready" if self._cards else "empty"
        return RepositoryStatistics(
            dataset_version=self._dataset_version,
            card_count=len(self._cards),
            status=status,
            loaded_at=self._loaded_at,
        )


class SwappableCardProvider(CardProvider):
    """Keeps requests on one immutable snapshot while a new one is prepared."""

    def __init__(self, repository: CardProvider) -> None:
        self._repository = repository
        self._lock = RLock()

    def get_random_batch(self, batch_size: int) -> tuple[CompactCard, ...]:
        return self._active_repository().get_random_batch(batch_size)

    def reload(self) -> None:
        self._active_repository().reload()

    def statistics(self) -> RepositoryStatistics:
        return self._active_repository().statistics()

    def replace(self, repository: CardProvider) -> None:
        with self._lock:
            self._repository = repository

    def _active_repository(self) -> CardProvider:
        with self._lock:
            return self._repository
