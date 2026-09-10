# Peliqan 7T handler deploy (WMS + Dock-to-Stock)

After changing `documentation/peliqan_7t_api_handler.py`:

1. Open Peliqan → API endpoint handler for 7T WMS (`/awc/7t` or your configured route).
2. Paste the updated handler script from `documentation/peliqan_7t_api_handler.py`.
3. Save and publish.
4. Clear Laravel cache: `php artisan cache:clear` (WMS responses are cached ~600s per year).
5. Clear Laravel cache (required after handler update):

```bash
php artisan cache:clear
```

6. Validate Dock-to-Stock (Brief Fonkel deel 3):

```bash
php scripts/verify_dock_to_stock.php 2026
```

The script prints `configured_url` — should match your Peliqan endpoint, e.g.
`https://api.eu.peliqan.io/2401/awc/7t` (set as `PELIQAN_AWC_7T_URL` in `.env`).

`handler_version` must contain `dock-to-stock-v3` or newer. v3 routes Dock-to-Stock
through Trino (`7t_db7t_7866`) when plain DB7T cannot reach Spare_Orders joins.

Step-by-step SQL probe:

```bash
php scripts/verify_dock_to_stock.php 2026 --probe
```

Control figures (whole 2026, stand 3 sep 2026):

- Meetbare orders: **~6.765**
- Binnen 24 uur: **~5.049** (**74,6%**)
- Dekking: **~61%** van geloste inbounds

Query parameter: `?year=2026` (defaults to current calendar year).
