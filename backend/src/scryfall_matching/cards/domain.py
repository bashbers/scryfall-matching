from dataclasses import dataclass
from datetime import datetime
from typing import Literal

RepositoryStatus = Literal["ready", "empty", "unavailable"]


@dataclass(frozen=True)
class CompactCard:
    id: str
    name: str
    front_image_url: str
    back_image_url: str | None
    is_double_sided: bool
    commander_legal: bool
    scryfall_url: str


@dataclass(frozen=True)
class RepositoryStatistics:
    dataset_version: str
    card_count: int
    status: RepositoryStatus
    loaded_at: datetime | None
