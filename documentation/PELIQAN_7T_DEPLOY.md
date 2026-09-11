# Peliqan 7T handler deploy (WMS + Dock-to-Stock)

After changing `documentation/peliqan_7t_api_handler.py`:

1. Open Peliqan → API endpoint handler for 7T WMS (`/awc/7t` or your configured route).
2. Paste the updated handler script from `documentation/peliqan_7t_api_handler.py`.
3. Save and publish.
4. On the server `.env`, ensure:
   ```env
   PELIQAN_AWC_7T_URL=https://api.eu.peliqan.io/2401/awc/7t
   PELIQAN_WMS_TIMEOUT=300
   ```
5. Clear config/cache:
   ```bash
   php artisan config:clear
   php artisan cache:clear
   ```

## Validate Dock-to-Stock (Brief Fonkel deel 3)

**Full KPI** (2 Trino queries, may take 1–3 min first run):

```bash
php scripts/verify_dock_to_stock.php 2026
```

**Light probe** (2 quick Trino checks, no full monthly breakdown):

```bash
php scripts/verify_dock_to_stock.php 2026 --probe
```

Control figures (whole 2026, stand 3 sep 2026):

- Measurable orders: **~6.765**
- Within 24 hours: **~5.049** (**74,6%**)
- Coverage: **~61%** of unloaded inbounds

`handler_version` must contain `dock-to-stock-v5` or newer. Dock-to-Stock runs via **Trino** catalog `7t_db7t_7866`.

If you see `cURL error 28` timeout → raise `PELIQAN_WMS_TIMEOUT` to `300` or `600`.
