from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, status

from scryfall_matching.cards.provider import CardProvider
from scryfall_matching.cards.schemas import ApiError, CardResponse, RandomCardsResponse

router = APIRouter(prefix="/api/v1/cards", tags=["cards"])
RANDOM_BATCH_SIZE = 5


def get_card_provider(request: Request) -> CardProvider:
    return cast(CardProvider, request.app.state.card_provider)


@router.get(
    "/random",
    response_model=RandomCardsResponse,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ApiError,
            "description": "The active card repository cannot serve a full batch.",
        }
    },
)
def random_cards(
    provider: Annotated[CardProvider, Depends(get_card_provider)],
) -> RandomCardsResponse:
    cards = provider.get_random_batch(RANDOM_BATCH_SIZE)
    return RandomCardsResponse(cards=[CardResponse.model_validate(card) for card in cards])
