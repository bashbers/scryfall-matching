import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from scryfall_matching.cards.repository import SwappableCardProvider
from scryfall_matching.cards.router import router as cards_router
from scryfall_matching.core.bootstrap import build_card_provider, build_importer
from scryfall_matching.core.errors import install_error_handlers
from scryfall_matching.core.health import router as health_router
from scryfall_matching.core.openapi import export_openapi_contract
from scryfall_matching.core.settings import Settings

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings.from_environment()
    app = FastAPI(title="Scryfall Matching API", version="0.1.0", lifespan=_lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=[],
    )
    app.state.settings = app_settings
    app.state.card_provider = build_card_provider(app_settings)
    app.state.scryfall_importer = build_importer(app_settings)
    install_error_handlers(app)
    app.include_router(health_router)
    app.include_router(cards_router)
    export_openapi_contract(app)
    return app


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    stop_event = asyncio.Event()
    update_task = asyncio.create_task(_run_updates(app, stop_event))
    try:
        yield
    finally:
        stop_event.set()
        await update_task


async def _run_updates(app: FastAPI, stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            provider = app.state.card_provider
            if isinstance(provider, SwappableCardProvider):
                await asyncio.to_thread(app.state.scryfall_importer.refresh, provider)
        except Exception:
            logger.exception("Scryfall dataset refresh failed; retaining the active snapshot.")

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=app.state.settings.scryfall_update_interval_hours * 3600,
            )
        except TimeoutError:
            continue


app = create_app()
