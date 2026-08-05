# Scryfall Matching

Een mobiele en desktopvriendelijke swipe-app om Magic: The Gathering-kaarten uit de Scryfall-bulkdataset te ontdekken.

De repository is een monorepo met een FastAPI-backend en een React/TypeScript/Vite-frontend. De app importeert de Scryfall-bulkdataset, presenteert kaarten in een swipe-ervaring en bewaart likes, dislikes en historie lokaal in de browser.

## Vereisten

- Docker Desktop met Docker Compose v2 (aanbevolen)
- Of lokaal: Python 3.14+ en Node.js 20.19+

## Starten met Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open daarna http://localhost:5173. De backend draait op http://localhost:8000.
Vanaf een ander apparaat in hetzelfde netwerk open je `http://<LAN-IP-VAN-DEZE-PC>:5173`; de ontwikkelserver proxy't `/api` automatisch naar de backendcontainer.

De compose-configuratie houdt toekomstige Scryfall-data in het persistente volume `scryfall-data`; er is bewust geen databasecontainer.
De frontend voert bij elke containerstart `npm install` uit, zodat wijzigingen in `package.json` ook met het persistente `node_modules`-volume worden toegepast. Zodra de lockfile is vastgelegd, gebruikt de image `npm ci` voor reproduceerbare builds.

## Lokaal ontwikkelen

Backend:

```powershell
cd backend
uv sync --extra dev
uv run uvicorn scryfall_matching.main:app --reload
```

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
npm run lint
npm run format:check
npm run typecheck
npm run build
```

## Productiecontainers

De productieconfiguratie gebruikt een non-root backend met één Uvicorn-worker en een persistent datavolume. De frontend is een Nginx-container met SPA-fallback, cacheheaders voor gehashte assets en een interne `/api`-proxy naar de backend.

```powershell
docker compose -f compose.production.yaml up --build
```

Open de frontend op http://localhost:8081. De backend blijft beschikbaar op http://localhost:8000; de containerlimiet voor de backend is 1 GiB RAM.

## Scryfall-data verversen

De configuratie voor de datamap, timeout en het update-interval staat in `.env`. De bulkdownload filtert en dedupliceert de Scryfall-data en vervangt de compacte dataset atomisch. De data blijft onder `DATA_PATH`: in het ontwikkelvolume `scryfall-data` en in het productievolume `scryfall-production-data`.

## API-contract

De backend publiceert nu:

- `GET /api/v1/cards/random`: exact vijf unieke compacte kaartrecords.
- `GET /api/v1/health/live`: liveness zonder afhankelijkheid van dataset of repository.
- `GET /api/v1/health/ready`: readiness met datasetversie, kaartenaantal en repositorystatus.

OpenAPI is beschikbaar via FastAPI op `/openapi.json` en lokaal te exporteren met:

```powershell
cd backend
scryfall-matching-export-openapi --output openapi.json
```
