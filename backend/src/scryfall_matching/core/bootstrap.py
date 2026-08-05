from scryfall_matching.cards.domain import CompactCard
from scryfall_matching.cards.provider import CardProvider
from scryfall_matching.cards.repository import InMemoryCardRepository, SwappableCardProvider
from scryfall_matching.core.settings import Settings
from scryfall_matching.scryfall.importer import ScryfallBulkImporter
from scryfall_matching.scryfall.storage import load_repository


def build_card_provider(settings: Settings) -> CardProvider:
    repository = load_repository(settings.data_directory)
    if repository is None:
        repository = InMemoryCardRepository((), dataset_version="no-dataset")
    return SwappableCardProvider(repository)


def build_importer(settings: Settings) -> ScryfallBulkImporter:
    return ScryfallBulkImporter(
        data_directory=settings.data_directory,
        timeout_seconds=settings.scryfall_timeout_seconds,
    )


def _seed_cards() -> tuple[CompactCard, ...]:
    return (
        CompactCard(
            id="seed-sol-ring",
            name="Sol Ring",
            front_image_url=(
                "https://api.scryfall.com/cards/named?exact=Sol%20Ring&format=image&version=normal"
            ),
            back_image_url=None,
            is_double_sided=False,
            commander_legal=True,
            scryfall_url="https://scryfall.com/search?q=%21%22Sol+Ring%22",
        ),
        CompactCard(
            id="seed-command-tower",
            name="Command Tower",
            front_image_url=(
                "https://api.scryfall.com/cards/named"
                "?exact=Command%20Tower&format=image&version=normal"
            ),
            back_image_url=None,
            is_double_sided=False,
            commander_legal=True,
            scryfall_url="https://scryfall.com/search?q=%21%22Command+Tower%22",
        ),
        CompactCard(
            id="seed-arcane-signet",
            name="Arcane Signet",
            front_image_url=(
                "https://api.scryfall.com/cards/named"
                "?exact=Arcane%20Signet&format=image&version=normal"
            ),
            back_image_url=None,
            is_double_sided=False,
            commander_legal=True,
            scryfall_url="https://scryfall.com/search?q=%21%22Arcane+Signet%22",
        ),
        CompactCard(
            id="seed-lightning-bolt",
            name="Lightning Bolt",
            front_image_url=(
                "https://api.scryfall.com/cards/named"
                "?exact=Lightning%20Bolt&format=image&version=normal"
            ),
            back_image_url=None,
            is_double_sided=False,
            commander_legal=True,
            scryfall_url="https://scryfall.com/search?q=%21%22Lightning+Bolt%22",
        ),
        CompactCard(
            id="seed-delver-of-secrets",
            name="Delver of Secrets",
            front_image_url=(
                "https://api.scryfall.com/cards/named"
                "?exact=Delver%20of%20Secrets&format=image&version=normal"
            ),
            back_image_url=(
                "https://api.scryfall.com/cards/named"
                "?exact=Delver%20of%20Secrets&format=image&version=normal&face=back"
            ),
            is_double_sided=True,
            commander_legal=True,
            scryfall_url="https://scryfall.com/search?q=%21%22Delver+of+Secrets%22",
        ),
        CompactCard(
            id="seed-cultivate",
            name="Cultivate",
            front_image_url=(
                "https://api.scryfall.com/cards/named?exact=Cultivate&format=image&version=normal"
            ),
            back_image_url=None,
            is_double_sided=False,
            commander_legal=True,
            scryfall_url="https://scryfall.com/search?q=%21%22Cultivate%22",
        ),
    )
