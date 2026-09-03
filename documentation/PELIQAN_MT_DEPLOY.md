# Peliqan MT handler deploy (Deel 1 KPI's)

After changing `documentation/peliqan_mt_api_handler.py`:

1. Open Peliqan → API endpoint handler for MT dashboard (`/mt/data`).
2. Paste the updated handler script from `documentation/peliqan_mt_api_handler.py`.
3. Save and publish.
4. Clear Laravel cache if needed: `php artisan cache:clear` (Peliqan responses are cached ~120s).
5. Validate winrate control figures on full history:
   - Verkooppijplijn: **27.1%** (55 won / 148 lost)
   - AFC Verkooplijn: **66.7%** (16 won / 8 lost)
6. Validate bruto marge per loonkosten jaar totals (2024/2025) against Brief Fonkel deel 1.
7. If KPI totals are zero while month rows exist: redeploy after the `debit_credit` null-handling fix in `sql_marge_per_loon_monthly` (Cashweb often leaves D/C empty; amounts are pre-signed).

Wage account lists live in `config/mt_kpi.php` (Laravel) and `MT_KPI_CONFIG` at the top of the Python handler — keep both in sync when finance updates accounts.
