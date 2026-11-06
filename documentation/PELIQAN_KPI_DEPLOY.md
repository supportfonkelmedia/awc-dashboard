# Peliqan KPI handler deploy

After changing `documentation/peliqan_kpi_api_handler.py`:

- If Laravel/Peliqan returns **`invalid_scherm`** while logs show `scherm` in the outbound query (HTTP 200 body with `invalid_scherm`): redeploy **v6** (`HANDLER_VERSION` contains `v6-request-dict-query-string`). Peliqan passes `request` as a **dict** `{method, url, path, query_string, headers, data, form}` ([docs](https://docs.peliqan.io/publish-apis)); earlier versions treated that dict as the params themselves and never read `request['query_string']`. The error body now always includes `handler_version`, `scherm_received` and `parsed_keys`, so a stale deploy is visible immediately.

1. Peliqan → **Apps** → API endpoint handler (new or duplicate MT handler app).
2. Paste the full script from `documentation/peliqan_kpi_api_handler.py`.
3. **API endpoints** → GET route, e.g. `/kpi/data`, attach handler, JWT enabled.
4. Copy **Final URL** (no `?`) into Laravel `.env`:

   ```env
   PELIQAN_KPI_DATA_URL=https://api.eu.peliqan.io/{tenant}/kpi/data
   PELIQAN_JWT=...
   PELIQAN_KPI_CACHE_TTL=3600
   ```

   Optional debugging — log every Peliqan GET (query + response body, **no JWT**) to `storage/logs/peliqan-*.log`:

   ```env
   PELIQAN_HTTP_LOG=true
   LOG_CHANNEL=stack
   LOG_STACK=daily
   ```

5. Smoke test (replace URL and token):

   ```bash
   curl -s -H "Authorization: JWT $PELIQAN_JWT" \
     "$PELIQAN_KPI_DATA_URL?bundle=screen&scherm=strategisch" | head
   ```

6. In the app: open `/kpi/strategisch` — header datacontroles and config row counts should populate.

Laravel proxy (authenticated): `GET /kpi/peliqan/data?bundle=screen&scherm=strategisch` (`route('kpi.peliqan')`).

| bundle | params | use |
| --- | --- | --- |
| `screen` | `scherm` | Full screen payload (config, oordel, trend, controles, registry) |
| `controles` | — | Header pills only |
| `drill` | `views` (comma), optional `limit` | Drill-down tables |
| `registry` | — | KPI registry rows |

Tables live in warehouse `dw_2401`, schema `"My Queries"`, suffix `_my_queries` (see Overdracht).

## Handmatige invoer (Fonkel MariaDB)

Until a Peliqan write handler pushes to `kpi_invoer.handmatig`, the app stores rows in **`kpi_handmatige_invoer`** (run `php artisan migrate`). Chloë can sync these into Peliqan or enable a write bundle on the KPI handler later.

`POST /kpi/invoer/handmatig` (auth) — eNPS and A/B Players only, scope `concern`.

`POST /kpi/invoer/doelen` (auth) — doelen staging in `kpi_doelen_invoer`; `geldig_vanaf` must be day 1 of a month.

Export staging for Chloë:

```bash
php artisan kpi:export-invoer --pretty
```
