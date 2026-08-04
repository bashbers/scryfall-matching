from typing import Protocol

from scryfall_matching.cards.domain import CompactCard, RepositoryStatistics


class CardProvider(Protocol):
    def get_random_batch(self, batch_size: int) -> tuple[CompactCard, ...]:
        """Return a unique random batch of cards."""

    def reload(self) -> None:
        """Reload the active dataset, if the provider supports it."""

    def statistics(self) -> RepositoryStatistics:
        """Return readiness information for the active dataset."""
