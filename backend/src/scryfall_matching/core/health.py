from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, Response, status

from scryfall_matching.cards.provider import CardProvider
from scryfall_matching.cards.schemas import LiveHealthResponse, ReadyHealthResponse

router = APIRouter(prefix="/api/v1/health", tags=["health"])


def get_card_provider(request: Request) -> CardProvider:
    return cast(CardProvider, request.app.state.card_provider)


@router.get("/live", response_model=LiveHealthResponse)
def live() -> LiveHealthResponse:
    return LiveHealthResponse(status="live")


@router.get(
    "/ready",
    response_model=ReadyHealthResponse,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ReadyHealthResponse,
            "description": "Dataset is empty or unavailable.",
        }
    },
)
def ready(
    response: Response,
    provider: Annotated[CardProvider, Depends(get_card_provider)],
) -> ReadyHealthResponse:
    stats = provider.statistics()
    if stats.status != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadyHealthResponse(
        status=stats.status,
        datasetVersion=stats.dataset_version,
        cardCount=stats.card_count,
        loadedAt=stats.loaded_at,
    )
