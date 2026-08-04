# Scryfall Matching — implementatiebacklog

Bronnen: `requirements.md` en `technisch-ontwerp-scryfall-matching.md` uit het ChatGPT-project **Scryfall Matching**.

## Fase 0 — Projectfundering

- [x] Initialiseer een monorepo met `backend/` (FastAPI) en `frontend/` (React + TypeScript + Vite).
- [x] Voeg een gedeelde ontwikkelconfiguratie toe: `.editorconfig`, formatters, linters en typechecks.
- [x] Leg omgevingsvariabelen vast voor datamap, batchgrootte, Scryfall-timeout, update-interval en logniveau.
- [x] Maak een Docker Compose-ontwikkelomgeving met backend, frontend en een persistent datavolume; geen database.
- [x] Voeg basisdocumentatie toe voor lokaal starten, testen en het verversen van de dataset.

## Fase 1 — Backenddomein en API-contract

- [x] Definieer het compacte interne kaartmodel: id, naam, front/back-image-URL, dubbelzijdig-vlag, Commander-legaliteit en Scryfall-URL.
- [x] Definieer Pydantic request/response-modellen en foutresponses.
- [x] Bouw een feature-gebaseerde FastAPI-structuur voor `cards`, `scryfall` en `core`.
- [x] Introduceer een `CardProvider`-interface met `get_random_batch()`, `reload()` en `statistics()`.
- [x] Implementeer een immutable `InMemoryCardRepository` onder de provider.
- [x] Implementeer `GET /api/v1/cards/random` met exact vijf unieke kaarten per antwoord.
- [x] Implementeer `GET /api/v1/health/live`; dit endpoint mag nooit afhankelijk zijn van dataset, repository of Scryfall.
- [x] Implementeer `GET /api/v1/health/ready` met datasetversie, aantal kaarten en repositorystatus.
- [x] Exporteer OpenAPI als het leidende API-contract.

## Fase 2 — Scryfall-datasetpipeline

- [x] Lees Scryfall Bulk Data-metadata en selecteer de `oracle_cards`-export.
- [x] Download de bron veilig naar een tijdelijk bestand en behoud de bestaande dataset bij fouten.
- [x] Verwerk de bron streaming; Scryfall levert JSON, waarna de app zelf compact JSONL genereert.
- [x] Leg de kaartfilters vast, inclusief het beleid "legaal in minimaal één regulier format".
- [x] Dedupliceer op Oracle-kaart/kaartnaam, niet op print of artwork.
- [x] Map enkel- en dubbelzijdige kaarten correct; definieer expliciet welke Scryfall-layouts fysiek dubbelzijdig zijn.
- [x] Schrijf `cards.compact.jsonl.tmp`, valideer het bestand en vervang `cards.compact.jsonl` atomisch.
- [x] Beheer `metadata.json` met versie, importstatus, aantallen en update-tijd.
- [x] Laad een nieuwe snapshot in een aparte repository en wissel de actieve repository atomisch om.
- [x] Gebruik FastAPI-lifespan voor initialisatie, updatecontrole bij startup, 24-uurs scheduler en shutdown.
- [x] Definieer het validatiebeleid voor corrupte losse records en een foutdrempel waarbij de gehele import faalt.

## Fase 3 — Frontendbasis en kaartqueue

- [x] Initialiseer React, TypeScript, Vite, React Router en TanStack Query.
- [x] Genereer TypeScript-types en API-client vanuit de backend-OpenAPI-specificatie.
- [x] Maak routes voor swipe, likes, dislikes en historie.
- [x] Bouw `useCardQueue`: initiële batch van vijf kaarten, één actieve prefetch en bijvullen wanneer twee kaarten resteren.
- [x] Filter duplicaten binnen de actieve queue; een kaart mag in een latere sessie opnieuw verschijnen.
- [x] Implementeer API-retries na 500 ms, 1.000 ms en 2.000 ms.
- [x] Toon pas retry-UI wanneer de retries op zijn én de queue leeg is; houd swipen beschikbaar zolang er kaarten zijn.

## Fase 4 — Swipe-ervaring en lokale gegevens

- [x] Bouw de kaartweergave met normale Scryfall-afbeelding, Commander-badge en veilige externe Scryfall-link.
- [x] Implementeer swipe rechts = like en swipe links = dislike, voor touch, muis en toetsenbord.
- [x] Voeg reduced-motion-ondersteuning toe.
- [x] Markeer iedere actief getoonde kaart als gezien; prefetched kaarten tellen nog niet als gezien.
- [x] Bewaar `likedCards`, `dislikedCards` en `seenCards` gededupliceerd in `localStorage`.
- [x] Bouw eenvoudige lijstweergaven voor likes, dislikes en historie, inclusief verwijderen uit lijsten.
- [x] Implementeer flipgedrag: echte dubbelzijdige kaarten tonen de tweede face; enkelzijdige kaarten tonen een lokale, eigen kaartachterkant. De keuze voor een officiële Magic-card-back blijft een open licentiebeslissing.
- [x] Voeg een placeholder toe voor falende kaartafbeeldingen, zonder swipe of Scryfall-link te blokkeren.
- [x] Handel `localStorage`-quota af met een waarschuwing terwijl de sessie bruikbaar blijft.

## Fase 5 — Tests en kwaliteitsgrenzen

- [ ] Schrijf backend-unit-tests voor filtering, mapping, deduplicatie, random batches, repository-swap en health-status.
- [ ] Schrijf import-integratietests voor succes, corrupte input, onderbroken download, atomische vervanging en herstel met bestaande dataset.
- [ ] Schrijf API-contracttests voor random batches, validatiefouten en liveness/readiness.
- [ ] Schrijf frontend-unit-tests voor swipes, flip, localStorage, Commander-badge, keyboard en reduced motion.
- [ ] Schrijf frontend-integratietests voor queue, prefetch, retries, retry-UI en duplicate filtering.
- [ ] Schrijf Playwright end-to-endtests voor de volledige like/dislike/history-flow, refresh en netwerkstoring.
- [ ] Verifieer prestatie-eisen: `GET /cards/random` p95 < 100 ms, kaartwissels zonder netwerk wanneer de queue gevuld is en passend geheugenverbruik binnen 1 GB RAM.

## Fase 6 — CI, containers en oplevering

- [ ] Configureer CI voor backend-lint, typecheck, tests en OpenAPI-export.
- [ ] Configureer CI voor frontend-lint, typecheck, OpenAPI-clientgeneratie, tests en productiebuild.
- [ ] Laat CI falen wanneer OpenAPI wijzigt zonder bijgewerkte gegenereerde client.
- [ ] Voeg containerbuilds en dependency/security-scans toe.
- [ ] Bouw een backendcontainer met non-root-user, persistent `/app/data`-volume en healthcheck op `/api/v1/health/live`.
- [ ] Bouw een frontendcontainer met statische server, SPA-fallback en correcte caching voor hashed assets versus `index.html`.
- [ ] Test productie-instellingen met één Uvicorn-worker en minimaal 1 GB RAM.

## Beslissingen die vóór of tijdens implementatie moeten worden vastgezet

- [ ] Kies de OpenAPI TypeScript-clientgenerator.
- [ ] Kies pointer-events versus een swipebibliotheek.
- [ ] Leg de exacte dubbelzijdige Scryfall-layouts in code en unit-tests vast.
- [ ] Leg het legalitybeleid voor `restricted` en Vintage buiten de reguliere formats vast.
- [ ] Kies en controleer de licentie/attributie van de Magic card back.
- [ ] Kies definitieve dependencyversies, hostingplatform en healthcheckconfiguratie.
