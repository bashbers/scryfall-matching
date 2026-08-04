from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from scryfall_matching.cards.errors import CardsUnavailableError


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(CardsUnavailableError)
    async def cards_unavailable_handler(
        _request: Request,
        exc: CardsUnavailableError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "code": "cards_unavailable",
                "message": str(exc),
            },
        )
