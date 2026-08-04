from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from scryfall_matching.cards.domain import RepositoryStatus


class ApiError(BaseModel):
    code: str
    message: str


class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    front_image_url: str = Field(alias="frontImageUrl")
    back_image_url: str | None = Field(alias="backImageUrl")
    is_double_sided: bool = Field(alias="isDoubleSided")
    commander_legal: bool = Field(alias="commanderLegal")
    scryfall_url: str = Field(alias="scryfallUrl")


class RandomCardsResponse(BaseModel):
    cards: list[CardResponse] = Field(min_length=5, max_length=5)


class LiveHealthResponse(BaseModel):
    status: Literal["live"]


class ReadyHealthResponse(BaseModel):
    status: RepositoryStatus
    dataset_version: str = Field(alias="datasetVersion")
    card_count: int = Field(alias="cardCount")
    loaded_at: datetime | None = Field(alias="loadedAt")

    model_config = ConfigDict(populate_by_name=True)
