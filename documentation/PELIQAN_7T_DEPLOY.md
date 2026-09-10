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

The script prints `handler_version` — must contain `dock-to-stock-v2` or newer.
If you see `ERROR_APPLICATION_DOES_NOT_EXIST`, redeploy v2+ (fixes wrong `7T` fetch key).

Control figures (whole 2026, stand 3 sep 2026):

- Meetbare orders: **~6.765**
- Binnen 24 uur: **~5.049** (**74,6%**)
- Dekking: **~61%** van geloste inbounds

Query parameter: `?year=2026` (defaults to current calendar year).
