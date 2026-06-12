"""One-off: build documentation/awc_7t_kpi_schema.json from 7t export."""
import json
import re
from pathlib import Path

SRC = Path(__file__).parent / "7t_export_20260611_072424.json"
OUT = Path(__file__).parent / "awc_7t_kpi_schema.json"


def norm_col(name: str) -> str:
    if not name:
        return name
    return re.sub(r'^"|"$', "", str(name).strip('"'))

QUERY_FIELDS = {
    "bezetting_locaties": [
        "ID",
        "Naam",
        "Magazijn_ID",
        "Geblokkeerd_Voor_Picken",
        "Extern",
        "Magazijn_Plaatssoort_ID",
    ],
    "bezetting_palletplaatsen": ["ID", "Aantal_Palletplaatsen"],
    "bezetting_magazijnen": ["ID", "Administratie_ID"],
    "bezetting_voorraad": ["Magazijn_Plts_ID", "Technische_Voorraad", "Er_Is_Voorraad"],
    "ontvangsten": [
        "ID",
        "Datum",
        "Aankomst_Leverancier",
        "Ontvangst_Definitief",
        "Relatie_ID",
        "MutatieDatum",
        "Status",
        "Administratie_ID",
    ],
    "telling_locaties": [
        "ID",
        "Telling_ID",
        "Totaal_Aantal_Verwacht",
        "Totaal_Aantal_Geteld",
        "Totaal_Aantal_Correctie",
        "Telling_Gereed",
        "Datum_Telling_Gereed",
    ],
    "tellingen": ["ID", "Magazijn_ID"],
    "leverdata": [
        "ID",
        "Orderregel_ID",
        "Informatief",
        "Oude_Leverdatum",
        "Nieuwe_Leverdatum",
        "AanmaakDatum",
    ],
    "orderregels": ["ID", "Order_ID"],
    "orders": ["ID", "Administratie_ID"],
    "administraties": ["ID", "Tekst_Code", "Naam"],
}

data = json.loads(SRC.read_text(encoding="utf-8"))
tables = {}
for t in data.get("tables", []):
    cols = [norm_col(c.get("column_name", "")) for c in t.get("columns", [])]
    tables[t["table_name"]] = {
        "present": t.get("present", True),
        "columns": cols,
        "column_count": len(cols),
    }

out = {
    "source_export": SRC.name,
    "schema_version": data.get("exported_at"),
    "catalog": data.get("catalog"),
    "schema": data.get("schema"),
    "awc_admin_code": data.get("awc_admin_code"),
    "tables": tables,
    "query_fields": QUERY_FIELDS,
}

OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
print(f"Wrote {OUT} ({len(tables)} tables)")

# Compact manifest for peliqan_awc_api_handler.py (paste into SCHEMA_MANIFEST).
manifest = {
    "source_export": out["source_export"],
    "schema_version": out["schema_version"],
    "catalog": out["catalog"],
    "schema": out["schema"],
    "awc_admin_code": out["awc_admin_code"],
    "kpi_tables": sorted(tables.keys()),
    "query_fields": QUERY_FIELDS,
    "assumed_columns": {"Administraties": ["Tekst_Code"]},
}
manifest_path = Path(__file__).parent / "awc_7t_schema_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"Wrote {manifest_path}")

handler_path = Path(__file__).parent / "peliqan_awc_api_handler.py"
handler_src = handler_path.read_text(encoding="utf-8")
manifest_py = json.dumps(manifest, indent=4)
marker_start = "SCHEMA_MANIFEST = "
marker_end = "\n\nTRINO_CATALOG_7T"
start = handler_src.find(marker_start)
end = handler_src.find(marker_end)
if start == -1 or end == -1:
    print("WARN: could not patch peliqan_awc_api_handler.py (markers missing)")
else:
    patched = (
        handler_src[: start + len(marker_start)]
        + manifest_py
        + handler_src[end:]
    )
    handler_path.write_text(patched, encoding="utf-8")
    print(f"Patched SCHEMA_MANIFEST in {handler_path.name}")
