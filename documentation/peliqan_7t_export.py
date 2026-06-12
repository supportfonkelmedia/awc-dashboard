# 7T (DB7T) schema export — Peliqan DATA APP
#
# Setup:
#   Build → Apps → New app → paste this script → Run
#   (NOT an API endpoint handler)
#
# Uses Peliqan metadata for table list (fast, same as explorer).
# Uses Trino catalog 7t_db7t_7866 for live reads / column samples.

import json
from datetime import datetime, timezone

TRINO_CATALOG = "7t_db7t_7866"
DB_NAME = "DB7T"
SCHEMA = "dbo"
AWC_ADMIN = "alaw"

KPI_TABLES = [
    "Administraties",
    "Magazijn_Plaatscodes",
    "Magazijn_Plaatssoorten",
    "Magazijnen",
    "Artikel_Magazijnlocaties",
    "Ontvangsten",
    "Telling_Locaties",
    "Tellingen",
    "Orderregel_Leverdata",
    "Orderregels",
    "Orders",
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def iter_databases():
    try:
        raw = pq.list_databases()
    except Exception:
        return []
    if isinstance(raw, dict):
        raw = list(raw.values())
    if not isinstance(raw, (list, tuple)):
        return []
    return [db for db in raw if isinstance(db, dict)]


def find_db7t():
    for db in iter_databases():
        if str(db.get("trino_catalog") or "") == TRINO_CATALOG:
            return db
        if str(db.get("name") or "") == DB_NAME:
            return db
    return None


def schema_map(db):
    out = {}
    for s in db.get("schemas") or []:
        if isinstance(s, dict) and s.get("id") is not None:
            out[s["id"]] = s.get("name") or SCHEMA
    return out


def tables_from_metadata():
    db = find_db7t()
    if db is None:
        return None, []

    smap = schema_map(db)
    tables = []
    for t in db.get("tables") or []:
        if not isinstance(t, dict) or not t.get("name"):
            continue
        sch = smap.get(t.get("schema_id"), SCHEMA)
        if str(sch).lower() != SCHEMA.lower():
            continue
        name = str(t["name"])
        tables.append(
            {
                "name": name,
                "table_id": t.get("id"),
                "known_kpi": name in KPI_TABLES,
            }
        )
    tables.sort(key=lambda x: x["name"])
    return db, tables


def columns_from_get_table(table_id):
    if not table_id:
        return None
    try:
        meta = pq.get_table(table_id)
    except Exception:
        return None
    if not isinstance(meta, dict):
        return None
    inner = meta.get("meta") if isinstance(meta.get("meta"), dict) else {}
    fields = inner.get("all_fields") or meta.get("all_fields") or meta.get("fields")
    if not fields:
        return None
    cols = []
    for f in fields:
        if isinstance(f, dict):
            cols.append(
                {
                    "column_name": f.get("name") or f.get("column_name"),
                    "data_type": f.get("type") or f.get("data_type"),
                }
            )
        elif isinstance(f, str):
            cols.append({"column_name": f, "data_type": None})
    return cols or None


def columns_from_trino(table_name, limit=1):
    trino = pq.trinoconnect()
    df = trino.fetch(TRINO_CATALOG, SCHEMA, table_name, df=True)
    if df is None or getattr(df, "empty", True):
        df = trino.fetch(
            TRINO_CATALOG,
            query=(
                f'SELECT TOP {int(limit)} * '
                f'FROM "{TRINO_CATALOG}".{SCHEMA}."{table_name}"'
            ),
            df=True,
        )
    if df is None or getattr(df, "empty", True):
        return []
    return [{"column_name": c, "data_type": str(df[c].dtype)} for c in df.columns]


def export_tables():
    db, tables = tables_from_metadata()
    if db is None:
        return {"ok": False, "error": f"{DB_NAME} not found in pq.list_databases()"}
    names = [t["name"] for t in tables]
    return {
        "ok": True,
        "exported_at": now_iso(),
        "source": "peliqan_metadata",
        "catalog": TRINO_CATALOG,
        "schema": SCHEMA,
        "table_count": len(names),
        "kpi_present": [t for t in KPI_TABLES if t in names],
        "kpi_missing": [t for t in KPI_TABLES if t not in names],
        "tables": tables,
    }


def export_kpi():
    db, tables = tables_from_metadata()
    if db is None:
        return {"ok": False, "error": f"{DB_NAME} not found in metadata"}
    by_name = {t["name"]: t for t in tables}
    out = []
    for name in KPI_TABLES:
        entry = by_name.get(name)
        cols, source = None, None
        if entry:
            cols = columns_from_get_table(entry.get("table_id"))
            if cols:
                source = "get_table"
        if not cols:
            try:
                cols = columns_from_trino(name)
                source = "trino_sample"
            except Exception as e:
                cols = []
                source = f"{type(e).__name__}: {e}"
        out.append(
            {
                "table_name": name,
                "present": entry is not None,
                "columns_source": source,
                "columns": cols or [],
            }
        )
    return {
        "ok": True,
        "exported_at": now_iso(),
        "catalog": TRINO_CATALOG,
        "schema": SCHEMA,
        "awc_admin_code": AWC_ADMIN,
        "tables": out,
    }


def export_one_table(table_name):
    table_name = str(table_name or "").strip()
    if not table_name:
        return {"ok": False, "error": "Pick a table name"}

    _, tables = tables_from_metadata()
    by_name = {t["name"]: t for t in tables}
    entry = by_name.get(table_name)

    cols, source = None, None
    if entry:
        cols = columns_from_get_table(entry.get("table_id"))
        if cols:
            source = "get_table"
    if not cols:
        cols = columns_from_trino(table_name, limit=3)
        source = "trino_sample"

    return {
        "ok": True,
        "exported_at": now_iso(),
        "table_name": table_name,
        "in_metadata": entry is not None,
        "columns_source": source,
        "columns": cols or [],
    }


def ping_trino():
    trino = pq.trinoconnect()
    df = trino.fetch(TRINO_CATALOG, SCHEMA, "Administraties", df=True)
    n = 0 if df is None else len(df)
    return n > 0, n


# --- UI (runs when you open the app in Peliqan) ---

st.set_page_config(page_title="7T Export", layout="wide")
st.title("7T / DB7T schema export")
st.caption(f"Trino `{TRINO_CATALOG}` · schema `{SCHEMA}` · filter AWC `{AWC_ADMIN}`")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Test Trino", use_container_width=True):
        with st.spinner("Reading dbo.Administraties…"):
            try:
                ok, n = ping_trino()
                if ok:
                    st.success(f"OK — {n} row(s) from Administraties")
                else:
                    st.error("Connected but 0 rows")
            except Exception as e:
                st.error(f"{type(e).__name__}: {e}")

with col2:
    load_tables = st.button("List tables", use_container_width=True)

with col3:
    load_kpi = st.button("Export KPI tables", use_container_width=True)

st.divider()

if load_tables:
    with st.spinner("Loading from Peliqan metadata…"):
        st.session_state["export"] = export_tables()

if load_kpi:
    with st.spinner("Loading KPI tables + columns…"):
        st.session_state["export"] = export_kpi()

one_table = st.text_input("Single table (optional)", placeholder="Ontvangsten")
if st.button("Export one table") and one_table.strip():
    with st.spinner(f"Loading {one_table}…"):
        st.session_state["export"] = export_one_table(one_table.strip())

data = st.session_state.get("export")
if data:
    if not data.get("ok"):
        st.error(data.get("error", "Export failed"))
    else:
        st.success(
            f"Exported at {data.get('exported_at', '')}"
            + (
                f" — {data.get('table_count')} tables"
                if data.get("table_count") is not None
                else ""
            )
        )

        if data.get("kpi_present") is not None:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**KPI present**")
                st.write(", ".join(data["kpi_present"]) or "—")
            with c2:
                st.markdown("**KPI missing**")
                st.write(", ".join(data["kpi_missing"]) or "—")

        if data.get("tables") and data["tables"] and "name" in data["tables"][0]:
            import pandas as pd

            df = pd.DataFrame(data["tables"])
            st.dataframe(df[["name", "known_kpi", "table_id"]], use_container_width=True)

        if data.get("tables") and data["tables"] and "table_name" in data["tables"][0]:
            for tbl in data["tables"]:
                with st.expander(
                    f"{tbl['table_name']} — {len(tbl.get('columns') or [])} cols"
                    + (" ✓" if tbl.get("present") else " ✗")
                ):
                    if tbl.get("columns"):
                        st.dataframe(tbl["columns"], use_container_width=True)
                    else:
                        st.write("No columns")

        if data.get("columns"):
            st.dataframe(data["columns"], use_container_width=True)

        st.download_button(
            "Download JSON",
            data=json.dumps(data, indent=2, default=str),
            file_name=f"7t_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )

        with st.expander("Raw JSON"):
            st.json(data)
