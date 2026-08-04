# Backend

FastAPI-backend voor Scryfall Matching.

## API

- `GET /api/v1/cards/random` geeft exact vijf unieke compacte kaartrecords terug.
- `GET /api/v1/health/live` is een pure liveness-check en raakt geen dataset of repository.
- `GET /api/v1/health/ready` rapporteert datasetversie, kaartenaantal, status en laadtijd.

Bij opstarten en vervolgens elke 24 uur controleert de backend de `oracle_cards`-bulkexport van
Scryfall. De download wordt eerst lokaal gevalideerd en compact als JSONL weggeschreven. Pas
daarna wisselt de server atomisch naar de nieuwe immutable snapshot. Een mislukte update behoudt
de laatst werkende dataset.

`metadata.json` in `DATA_PATH` bevat de importstatus, datasetversie, aantallen en tijdstempels.
Records zijn alleen bruikbaar wanneer zij legaal zijn in ten minste een regulier format:
Standard, Pioneer, Modern, Legacy, Pauper, Alchemy, Explorer, Historic of Timeless. Fysiek
dubbelzijdige layouts zijn expliciet `transform`, `modal_dfc` en `meld`.

## OpenAPI exporteren

```powershell
scryfall-matching-export-openapi --output openapi.json
```
