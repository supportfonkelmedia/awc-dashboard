# 7T Software (WMS) — schema export for Peliqan
#
# Purpose: discover tables/columns in 7T (Peliqan: DB7T / dbo) before wiring AWC KPIs.
# The 7T database has 100+ tables; run this once (or on demand) to map the schema.
#
# Peliqan setup:
#   1. Build → Apps → API endpoint handler → paste this file.
#   2. API route e.g. GET /7t/schema  (JWT on).
#   3. Call from browser or curl:
#        GET .../7t/schema?bundle=summary
#        GET .../7t/schema?bundle=kpi
#        GET .../7t/schema?bundle=full&filter=ontvang
#        GET .../7t/schema?table=Ontvangsten
#
# Query params:
#   bundle          = summary | kpi | full | table | databases   (default: summary)
#   schema          = dbo                              (default: dbo)
#   filter          = optional substring on table name (case-insensitive)
#   table           = single table name (with bundle=table)
#   include_counts  = 1 | 0                            (default: 0 — row counts are slow)
#   max_tables      = cap tables returned in full mode   (default: 200)
#
# Returns JSON (save response as documentation/7t_schema_export.json for offline review).

import json
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs

import pandas as pd

PROBE_SCHEMA = "dbo"
PROBE_TABLE = "Administraties"

# 7T is EXTERNAL SQL Server in Peliqan (not built-in DW like dw_2401).
# list_databases() only reads Peliqan metadata — no live SQL needed (that's why listing works).
# Live queries go through Trino federated engine:
#   trino = pq.trinoconnect()
#   trino.fetch('7t_db7t_7866', 'dbo', 'Administraties', df=True)
#   trino.fetch('7t_db7t_7866', query='SELECT … FROM dbo.Table', df=True)
# Fallback (some tenants): pq.dbconnect('7T') + fetch('DB7T', …)
CONNECT_7T = "7T"
FETCH_DB_7T = "DB7T"
TRINO_CATALOG_7T = "7t_db7t_7866"
CONNECT_7T_FALLBACKS = ("7T", "DB7T", "db_7t", "db7t")
DEFAULT_SCHEMA = "dbo"
AWC_ADMIN_CODE = "alaw"

# Tables already referenced in peliqan_awc_api_handler.py / PELIQAN_AWC_DASHBOARD.md
KPI_TABLES_KNOWN = [
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

# Keyword match for AWC warehouse KPI discovery (occupancy, OTIF, throughput, etc.)
KPI_NAME_KEYWORDS = (
    "ontvang",
    "order",
    "magazijn",
    "telling",
    "artikel",
    "lever",
    "pallet",
    "voorraad",
    "relatie",
    "administr",
    "klant",
    "pick",
    "ship",
    "expedit",
    "mutatie",
    "status",
    "datum",
    "schade",
    "damage",
)

_dbconn = None
_CONN_MODE = None
_WAREHOUSE_RESOLVED = None
_FETCH_DB_RESOLVED = None
_CONNECT_ERROR = None
_CONNECT_TRIED = []
_active_dbconn = None
_active_conn_mode = None
_active_warehouse = None
_active_fetch_db = None
_last_fetch_error = None


def iter_raw_databases(raw):
    if raw is None:
        return []
    if isinstance(raw, pd.DataFrame):
        raw = raw.to_dict(orient="records")
    if isinstance(raw, dict):
        raw = list(raw.values())
    if not isinstance(raw, (list, tuple)):
        return []
    return [db for db in raw if isinstance(db, dict)]


def get_active_catalog():
    return _active_fetch_db or _FETCH_DB_RESOLVED or TRINO_CATALOG_7T


def find_7t_database_record(catalog=None):
    catalog = str(catalog or get_active_catalog()).strip()
    for db in iter_raw_databases(list_peliqan_databases_raw()):
        if str(db.get("trino_catalog") or "").strip() == catalog:
            return db
        if str(db.get("name") or "").strip() == FETCH_DB_7T:
            return db
    return None


def list_peliqan_databases_raw():
    try:
        return pq.list_databases()
    except Exception:
        return None


def normalize_database_entries(raw):
    entries = []
    if raw is None:
        return entries
    if isinstance(raw, pd.DataFrame):
        raw = raw.to_dict(orient="records")
    if isinstance(raw, dict):
        raw = list(raw.values())
    if not isinstance(raw, (list, tuple)):
        return entries

    for db in raw:
        if not isinstance(db, dict):
            continue
        name = str(db.get("name") or "").strip()
        connection_name = str(
            db.get("connection_name") or db.get("connection") or ""
        ).strip()
        slug = str(db.get("slug") or db.get("warehouse") or "").strip()
        server = db.get("server") if isinstance(db.get("server"), dict) else {}
        entries.append(
            {
                "id": db.get("id"),
                "name": name or None,
                "connection_name": connection_name or server.get("name") or None,
                "slug": slug or None,
                "trino_catalog": db.get("trino_catalog"),
                "server_name": server.get("name"),
                "server_type": server.get("server_type"),
                "target_type": server.get("target_type"),
                "schema_count": len(db.get("schemas") or []),
                "table_count": len(db.get("tables") or []),
            }
        )
    return entries


def discover_7t_trino_catalog():
    for entry in normalize_database_entries(list_peliqan_databases_raw()):
        if not is_likely_7t_database(entry):
            continue
        catalog = str(entry.get("trino_catalog") or "").strip()
        if catalog:
            return catalog
    return TRINO_CATALOG_7T


def is_likely_7t_database(entry):
    parts = [
        str(entry.get("name") or ""),
        str(entry.get("connection_name") or ""),
        str(entry.get("slug") or ""),
    ]
    hay = " ".join(parts).lower().replace("_", "")
    return "7t" in hay or "db7t" in hay


def build_connect_attempts(preferred=None):
    attempts = []
    seen = set()

    def add(connect_id, fetch_db=None, source="manual"):
        connect_id = str(connect_id or "").strip()
        if not connect_id:
            return
        fetch_options = []
        for candidate in (fetch_db, connect_id):
            candidate = str(candidate or "").strip()
            if candidate and candidate not in fetch_options:
                fetch_options.append(candidate)
        key = (connect_id, tuple(fetch_options))
        if key in seen:
            return
        seen.add(key)
        attempts.append(
            {
                "connect_id": connect_id,
                "fetch_db_options": fetch_options,
                "source": source,
            }
        )

    add(CONNECT_7T, FETCH_DB_7T, "server_db_pair")

    if preferred:
        preferred = str(preferred).strip()
        if preferred.upper() == FETCH_DB_7T:
            add(CONNECT_7T, FETCH_DB_7T, "query_param_db_name")
        else:
            add(preferred, FETCH_DB_7T, "query_param_connect")
            add(preferred, preferred, "query_param_same")

    for wh in CONNECT_7T_FALLBACKS:
        if wh == CONNECT_7T:
            continue
        add(wh, FETCH_DB_7T if wh != FETCH_DB_7T else wh, "fallback")

    for entry in normalize_database_entries(list_peliqan_databases_raw()):
        name = entry.get("name") or ""
        connection_name = entry.get("connection_name") or ""
        slug = entry.get("slug") or ""
        if is_likely_7t_database(entry):
            if name:
                add(name, name, "list_databases.name")
            if connection_name:
                add(connection_name, name or connection_name, "list_databases.connection_name")
            if slug:
                add(slug, name or slug, "list_databases.slug")
        elif preferred and preferred.lower() == name.lower():
            add(name, name, "list_databases.exact_name")

    return attempts


def probe_result_ok(df):
    return df is not None and not df.empty


def build_fetch_probes(conn, fetch_key, fqn_catalog=None):
    """Peliqan external SQL Server rejects bare SELECT 1 — need table or FQN query."""
    fetch_key = str(fetch_key or "").strip()
    catalog = str(fqn_catalog or fetch_key).strip()
    sch = PROBE_SCHEMA
    tbl = PROBE_TABLE

    return [
        (
            "table_fetch",
            lambda: conn.fetch(fetch_key, sch, tbl, df=True),
        ),
        (
            "query_top1",
            lambda: conn.fetch(
                fetch_key,
                query=f"SELECT TOP 1 ID FROM {sch}.{tbl}",
                df=True,
            ),
        ),
        (
            "query_fqn",
            lambda: conn.fetch(
                fetch_key,
                query=f'SELECT TOP 1 ID FROM "{catalog}".{sch}."{tbl}"',
                df=True,
            ),
        ),
        (
            "query_information_schema",
            lambda: conn.fetch(
                fetch_key,
                query=(
                    f'SELECT table_name FROM "{catalog}".information_schema.tables '
                    f"WHERE table_schema = '{sch}' LIMIT 5"
                ),
                df=True,
            ),
        ),
    ]


def run_fetch_probes(conn, mode, fetch_key, tried, source, connect_id=None, fqn_catalog=None):
    connect_id = connect_id or fetch_key
    for probe_name, probe_fn in build_fetch_probes(conn, fetch_key, fqn_catalog):
        try:
            df = probe_fn()
            if probe_result_ok(df):
                return {
                    "mode": mode,
                    "conn": conn,
                    "connect_id": connect_id,
                    "fetch_db": fetch_key,
                    "probe": probe_name,
                    "source": source,
                }
        except Exception as e:
            tried.append(
                {
                    "mode": mode,
                    "connect_id": connect_id,
                    "fetch_db": fetch_key,
                    "probe": probe_name,
                    "source": source,
                    "error": f"{type(e).__name__}: {e}",
                }
            )
    return None


def try_trino_catalog(catalog, tried, source="trino", quick=False):
    catalog = str(catalog or "").strip()
    if not catalog:
        return None

    try:
        trino = pq.trinoconnect()
    except Exception as e:
        tried.append(
            {
                "mode": "trino",
                "catalog": catalog,
                "probe": "trinoconnect",
                "source": source,
                "error": f"{type(e).__name__}: {e}",
            }
        )
        return None

    return run_fetch_probes(
        trino,
        "trino",
        catalog,
        tried,
        source,
        connect_id="trino",
        fqn_catalog=catalog,
    )


def try_dbconnect_pair(connect_id, fetch_db, tried, source="dbconnect"):
    try:
        conn = pq.dbconnect(connect_id)
    except Exception as e:
        tried.append(
            {
                "mode": "dbconnect",
                "connect_id": connect_id,
                "fetch_db": fetch_db,
                "probe": "dbconnect",
                "source": source,
                "error": f"{type(e).__name__}: {e}",
            }
        )
        return None

    fetch_options = []
    for candidate in (fetch_db, FETCH_DB_7T):
        candidate = str(candidate or "").strip()
        if candidate and candidate not in fetch_options:
            fetch_options.append(candidate)

    for fetch_name in fetch_options:
        hit = run_fetch_probes(
            conn,
            "dbconnect",
            fetch_name,
            tried,
            source,
            connect_id=connect_id,
            fqn_catalog=TRINO_CATALOG_7T,
        )
        if hit:
            return hit
    return None


def run_all_connection_probes(preferred=None, quick=False):
    """Try connection strategies; stop on first success (quick=True for bundle=probe)."""
    tried = []
    results = []

    catalogs = []
    for catalog in (TRINO_CATALOG_7T, discover_7t_trino_catalog()):
        catalog = str(catalog or "").strip()
        if catalog and catalog not in catalogs:
            catalogs.append(catalog)

    for idx, catalog in enumerate(catalogs):
        hit = try_trino_catalog(
            catalog,
            tried,
            source="trino_catalog" if idx == 0 else "trino_fallback",
            quick=quick,
        )
        if hit:
            results.append(hit)
            if quick:
                return results, tried

    if quick:
        hit = try_dbconnect_pair(
            CONNECT_7T, FETCH_DB_7T, tried, source="quick_dbconnect"
        )
        if hit:
            results.append(hit)
        return results, tried

    for attempt in build_connect_attempts(preferred):
        connect_id = attempt["connect_id"]
        for fetch_db in attempt["fetch_db_options"]:
            hit = try_dbconnect_pair(
                connect_id, fetch_db, tried, source=attempt["source"]
            )
            if hit:
                results.append(hit)
                return results, tried

    return results, tried


def resolve_7t_connection(preferred=None):
    tried = []
    results, tried = run_all_connection_probes(preferred)
    if results:
        hit = results[0]
        return (
            hit["conn"],
            hit["mode"],
            hit["connect_id"],
            hit["fetch_db"],
            None,
            tried,
        )

    databases = normalize_database_entries(list_peliqan_databases_raw())
    likely_7t = [db for db in databases if is_likely_7t_database(db)]
    err = {
        "message": "Could not query 7T warehouse.",
        "tried": tried,
        "peliqan_databases": databases,
        "likely_7t": likely_7t,
        "trino_catalog_expected": discover_7t_trino_catalog(),
        "hint": (
            "7T is EXTERNAL SQL Server. list_databases() works without SQL; "
            "queries need pq.trinoconnect() + fetch('<trino_catalog>', …). "
            f"Expected catalog: {discover_7t_trino_catalog()}."
        ),
    }
    return None, None, None, None, err, tried


# Do not connect at import — every API call was running full probe before handler().
# Connection is resolved lazily on first data bundle (summary/kpi/full/table).


def parse_query(request):
    out = {}
    if request is None:
        return out
    if isinstance(request, dict):
        if isinstance(request.get("query"), dict):
            out.update(
                {
                    k: v[0] if isinstance(v, list) and v else v
                    for k, v in request["query"].items()
                }
            )
        elif isinstance(request.get("query_params"), dict):
            out.update(request["query_params"])
        qs = request.get("query_string") or request.get("queryString") or ""
        if isinstance(qs, str) and qs.strip():
            for k, v in parse_qs(qs.lstrip("?")).items():
                if v:
                    out.setdefault(k, v[0])
    else:
        if hasattr(request, "args"):
            for k in request.args:
                out[k] = request.args.get(k)
    return out


def set_active_connection(dbconn, conn_mode, connect_id, fetch_db=None):
    global _active_dbconn, _active_conn_mode, _active_warehouse, _active_fetch_db
    _active_dbconn = dbconn
    _active_conn_mode = conn_mode
    _active_warehouse = connect_id
    _active_fetch_db = fetch_db or connect_id


def adapt_query_for_trino(query, catalog):
    if not catalog or f'"{catalog}"' in query:
        return query
    q = query
    q = q.replace("INFORMATION_SCHEMA.", f'"{catalog}".information_schema.')
    q = q.replace("FROM sys.", f'FROM "{catalog}".sys.')
    q = q.replace("INNER JOIN sys.", f'INNER JOIN "{catalog}".sys.')
    q = re.sub(
        r"\bdbo\.([A-Za-z_][A-Za-z0-9_]*)",
        rf'"{catalog}".dbo."\1"',
        q,
    )
    return q


def fetch(query, fetch_db=None):
    global _last_fetch_error
    conn = _active_dbconn or _dbconn
    wh = (
        fetch_db
        or _active_fetch_db
        or _FETCH_DB_RESOLVED
        or FETCH_DB_7T
    )
    mode = _active_conn_mode or _CONN_MODE
    if conn is None:
        _last_fetch_error = "No active connection."
        return pd.DataFrame()
    sql = adapt_query_for_trino(query, wh) if mode == "trino" else query
    try:
        df = conn.fetch(wh, query=sql, df=True)
        _last_fetch_error = None
        return df if df is not None else pd.DataFrame()
    except Exception as e:
        _last_fetch_error = f"{type(e).__name__}: {e}"
        return pd.DataFrame()


def df_records(df):
    if df is None or df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))


def sql_escape_literal(value):
    return str(value).replace("'", "''")


def load_tables_from_metadata(schema_name, catalog=None):
    """Same source as Peliqan explorer — no live SQL required."""
    catalog = catalog or get_active_catalog()
    db = find_7t_database_record(catalog)
    if db is None:
        return pd.DataFrame(), "metadata_not_found"

    schema_map = {}
    for schema in db.get("schemas") or []:
        if isinstance(schema, dict) and schema.get("id") is not None:
            schema_map[schema["id"]] = schema.get("name") or schema_name

    sch_low = schema_name.lower()
    rows = []
    for table in db.get("tables") or []:
        if not isinstance(table, dict):
            continue
        tname = table.get("name")
        if not tname:
            continue
        sch = schema_map.get(table.get("schema_id"), schema_name)
        if str(sch).lower() != sch_low:
            continue
        rows.append(
            {
                "table_schema": sch,
                "table_name": str(tname),
                "table_type": "BASE TABLE",
            }
        )

    if not rows:
        return pd.DataFrame(), "metadata_empty"

    return (
        pd.DataFrame(rows).sort_values("table_name").reset_index(drop=True),
        "peliqan_metadata",
    )


def load_tables_trino_sql(schema_name, catalog=None):
    catalog = sql_escape_literal(catalog or get_active_catalog())
    sch = sql_escape_literal(schema_name)
    df = fetch(
        f"""
        SELECT
            table_schema,
            table_name,
            table_type
        FROM "{catalog}".information_schema.tables
        WHERE lower(table_schema) = lower('{sch}')
        ORDER BY table_name
        """
    )
    return df, "trino_information_schema"


def load_tables_trino_show(schema_name, catalog=None):
    catalog = sql_escape_literal(catalog or get_active_catalog())
    sch = sql_escape_literal(schema_name)
    df = fetch(f'SHOW TABLES FROM "{catalog}"."{sch}"')
    if df is None or df.empty:
        return pd.DataFrame(), "trino_show_empty"

    name_col = None
    for candidate in ("Table", "table_name", "Tables_in_" + schema_name):
        if candidate in df.columns:
            name_col = candidate
            break
    if name_col is None:
        name_col = df.columns[0]

    rows = [
        {
            "table_schema": schema_name,
            "table_name": str(value),
            "table_type": "BASE TABLE",
        }
        for value in df[name_col].tolist()
        if value is not None and str(value).strip() != ""
    ]
    if not rows:
        return pd.DataFrame(), "trino_show_empty"
    return pd.DataFrame(rows), "trino_show"


def load_tables(schema_name):
    mode = _active_conn_mode or _CONN_MODE
    if mode == "trino":
        for loader in (
            load_tables_from_metadata,
            load_tables_trino_show,
            load_tables_trino_sql,
        ):
            df, source = loader(schema_name)
            if df is not None and not df.empty:
                return df, source
        return pd.DataFrame(), "trino_all_failed"

    sch = sql_escape_literal(schema_name)
    df = fetch(
        f"""
        SELECT
            TABLE_SCHEMA AS table_schema,
            TABLE_NAME   AS table_name,
            TABLE_TYPE   AS table_type
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = '{sch}'
          AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """
    )
    return df, "dbconnect_information_schema"


def load_columns(schema_name, table_names=None):
    mode = _active_conn_mode or _CONN_MODE
    sch = sql_escape_literal(schema_name)
    table_filter = ""
    if table_names:
        safe = ", ".join(
            "'" + sql_escape_literal(t) + "'" for t in table_names
        )
        if mode == "trino":
            table_filter = f" AND table_name IN ({safe})"
        else:
            table_filter = f" AND c.TABLE_NAME IN ({safe})"

    if mode == "trino":
        catalog = sql_escape_literal(get_active_catalog())
        return fetch(
            f"""
            SELECT
                table_schema,
                table_name,
                column_name,
                ordinal_position,
                data_type,
                character_maximum_length AS char_max_length,
                numeric_precision,
                numeric_scale,
                is_nullable
            FROM "{catalog}".information_schema.columns
            WHERE lower(table_schema) = lower('{sch}')
            {table_filter}
            ORDER BY table_name, ordinal_position
            """
        )

    return fetch(
        f"""
        SELECT
            c.TABLE_SCHEMA     AS table_schema,
            c.TABLE_NAME       AS table_name,
            c.COLUMN_NAME      AS column_name,
            c.ORDINAL_POSITION AS ordinal_position,
            c.DATA_TYPE        AS data_type,
            c.CHARACTER_MAXIMUM_LENGTH AS char_max_length,
            c.NUMERIC_PRECISION AS numeric_precision,
            c.NUMERIC_SCALE    AS numeric_scale,
            c.IS_NULLABLE      AS is_nullable
        FROM INFORMATION_SCHEMA.COLUMNS AS c
        WHERE c.TABLE_SCHEMA = '{sch}'
        {table_filter}
        ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION
        """
    )


def load_row_counts(schema_name):
    sch = sql_escape_literal(schema_name)
    return fetch(
        f"""
        SELECT
            s.name AS table_schema,
            t.name AS table_name,
            SUM(p.rows) AS row_count_approx
        FROM sys.tables AS t
        INNER JOIN sys.schemas AS s ON t.schema_id = s.schema_id
        INNER JOIN sys.partitions AS p ON t.object_id = p.object_id
        WHERE p.index_id IN (0, 1)
          AND s.name = '{sch}'
        GROUP BY s.name, t.name
        ORDER BY t.name
        """
    )


def load_foreign_keys(schema_name):
    sch = sql_escape_literal(schema_name)
    return fetch(
        f"""
        SELECT
            fk.name AS fk_name,
            sch1.name AS from_schema,
            tab1.name AS from_table,
            col1.name AS from_column,
            sch2.name AS to_schema,
            tab2.name AS to_table,
            col2.name AS to_column
        FROM sys.foreign_keys AS fk
        INNER JOIN sys.foreign_key_columns AS fkc
            ON fk.object_id = fkc.constraint_object_id
        INNER JOIN sys.tables AS tab1
            ON fkc.parent_object_id = tab1.object_id
        INNER JOIN sys.schemas AS sch1
            ON tab1.schema_id = sch1.schema_id
        INNER JOIN sys.columns AS col1
            ON fkc.parent_object_id = col1.object_id
           AND fkc.parent_column_id = col1.column_id
        INNER JOIN sys.tables AS tab2
            ON fkc.referenced_object_id = tab2.object_id
        INNER JOIN sys.schemas AS sch2
            ON tab2.schema_id = sch2.schema_id
        INNER JOIN sys.columns AS col2
            ON fkc.referenced_object_id = col2.object_id
           AND fkc.referenced_column_id = col2.column_id
        WHERE sch1.name = '{sch}'
        ORDER BY tab1.name, fk.name, fkc.constraint_column_id
        """
    )


def load_administraties_sample():
    return fetch(
        """
        SELECT TOP 20
            ID, Code, Naam
        FROM dbo.Administraties
        ORDER BY Code
        """
    )


def is_kpi_relevant(table_name):
    low = table_name.lower()
    if table_name in KPI_TABLES_KNOWN:
        return True
    return any(k in low for k in KPI_NAME_KEYWORDS)


def apply_name_filter(table_name, name_filter):
    if not name_filter:
        return True
    return name_filter.lower() in table_name.lower()


def build_counts_map(counts_df):
    out = {}
    if counts_df is None or counts_df.empty:
        return out
    for _, row in counts_df.iterrows():
        out[str(row["table_name"])] = int(row.get("row_count_approx") or 0)
    return out


def group_columns(columns_df):
    grouped = {}
    if columns_df is None or columns_df.empty:
        return grouped
    for _, row in columns_df.iterrows():
        tname = str(row["table_name"])
        grouped.setdefault(tname, []).append(
            {
                "column_name": row["column_name"],
                "ordinal_position": int(row["ordinal_position"]),
                "data_type": row["data_type"],
                "char_max_length": row.get("char_max_length"),
                "numeric_precision": row.get("numeric_precision"),
                "numeric_scale": row.get("numeric_scale"),
                "is_nullable": row["is_nullable"],
            }
        )
    return grouped


def table_entry(name, schema_name, counts_map, columns_by_table, flags=None):
    flags = flags or {}
    return {
        "table_schema": schema_name,
        "table_name": name,
        "row_count_approx": counts_map.get(name),
        "column_count": len(columns_by_table.get(name, [])),
        "columns": columns_by_table.get(name, []),
        **flags,
    }


def resolve_bundle(q):
    b = str(q.get("bundle", "summary")).lower().strip()
    if b not in ("summary", "kpi", "full", "table", "databases", "probe"):
        b = "summary"
    return b


def probe_bundle_response(preferred=None):
    # Fast path only — no list_databases(), no row counts, stop on first working mode.
    results, tried = run_all_connection_probes(preferred, quick=True)
    return {
        "ok": bool(results),
        "bundle": "probe",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "trino_catalog_expected": TRINO_CATALOG_7T,
        "working_modes": [
            {
                "mode": r["mode"],
                "connect_id": r["connect_id"],
                "fetch_db": r["fetch_db"],
                "probe": r["probe"],
                "source": r["source"],
            }
            for r in results
        ],
        "connection_attempts": tried,
        "hint": (
            "External SQL Server needs table-based fetch (not bare SELECT 1). "
            "Probe tries dbo.Administraties + information_schema. "
            "For summary use include_counts=0."
        ),
    }


def databases_bundle_response(preferred=None):
    databases = normalize_database_entries(list_peliqan_databases_raw())
    likely_7t = [db for db in databases if is_likely_7t_database(db)]
    return {
        "ok": True,
        "bundle": "databases",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "databases": databases,
        "likely_7t": likely_7t,
        "connection_attempts": build_connect_attempts(preferred),
        "connect_expected": CONNECT_7T,
        "fetch_db_expected": FETCH_DB_7T,
        "hint": (
            "7T SQL Server: pq.dbconnect('7T') + fetch('DB7T', …). "
            "Set warehouse=7T on the debug page (server name, not database name)."
        ),
    }


def handler(request):
    q = parse_query(request)
    bundle = resolve_bundle(q)
    schema_name = str(q.get("schema") or DEFAULT_SCHEMA)
    name_filter = str(q.get("filter") or "").strip()
    single_table = str(q.get("table") or "").strip()
    include_counts = str(q.get("include_counts", "0")).lower() not in (
        "0",
        "false",
        "no",
    )
    max_tables = max(1, min(int(q.get("max_tables") or 200), 500))

    warehouse_override = str(q.get("warehouse") or "").strip()

    if bundle == "databases":
        return databases_bundle_response(warehouse_override or CONNECT_7T)

    if bundle == "probe":
        return probe_bundle_response(warehouse_override or CONNECT_7T)

    dbconn = _dbconn
    conn_mode = _CONN_MODE
    connect_id = _WAREHOUSE_RESOLVED or CONNECT_7T
    fetch_db = _FETCH_DB_RESOLVED or FETCH_DB_7T
    connect_err = _CONNECT_ERROR

    if warehouse_override and warehouse_override not in (connect_id, fetch_db):
        dbconn, conn_mode, connect_id, fetch_db, connect_err, tried = resolve_7t_connection(
            warehouse_override
        )
    elif dbconn is None:
        dbconn, conn_mode, connect_id, fetch_db, connect_err, tried = resolve_7t_connection(
            CONNECT_7T
        )
    else:
        tried = _CONNECT_TRIED

    if dbconn is None:
        err = (
            connect_err
            if isinstance(connect_err, dict)
            else {"message": str(connect_err or "7T connection unavailable")}
        )
        return {
            "ok": False,
            "error": err.get("message"),
            "warehouse_expected": CONNECT_7T,
            "connection_attempts": err.get("tried") or tried,
            "peliqan_databases": err.get("peliqan_databases")
            or normalize_database_entries(list_peliqan_databases_raw()),
            "likely_7t": err.get("likely_7t") or [],
            "hint": err.get("hint"),
        }

    set_active_connection(dbconn, conn_mode, connect_id, fetch_db)

    tables_df, tables_source = load_tables(schema_name)
    all_names = (
        [str(x) for x in tables_df["table_name"].tolist()]
        if not tables_df.empty
        else []
    )

    counts_map = (
        build_counts_map(load_row_counts(schema_name))
        if include_counts
        else {}
    )

    if bundle == "table":
        if not single_table:
            return {
                "ok": False,
                "error": "bundle=table requires query param table=<name>",
                "example_tables": KPI_TABLES_KNOWN,
            }
        if single_table not in all_names:
            return {
                "ok": False,
                "error": f"Table '{single_table}' not found in schema '{schema_name}'",
                "matching_tables": [
                    t for t in all_names if single_table.lower() in t.lower()
                ][:25],
            }
        cols_df = load_columns(schema_name, [single_table])
        cols_by_table = group_columns(cols_df)
        fks = load_foreign_keys(schema_name)
        fk_rows = []
        if not fks.empty:
            fk_rows = df_records(
                fks[
                    (fks["from_table"] == single_table)
                    | (fks["to_table"] == single_table)
                ]
            )
        return {
            "ok": True,
            "warehouse": connect_id,
            "connection_mode": conn_mode,
            "connect_id": connect_id,
            "fetch_db": fetch_db,
            "schema": schema_name,
            "bundle": bundle,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "table": table_entry(
                single_table,
                schema_name,
                counts_map,
                cols_by_table,
                {"known_kpi_table": single_table in KPI_TABLES_KNOWN},
            ),
            "foreign_keys": fk_rows,
        }

    if bundle == "summary":
        rows = []
        for name in all_names:
            if not apply_name_filter(name, name_filter):
                continue
            rows.append(
                {
                    "table_name": name,
                    "row_count_approx": counts_map.get(name),
                    "known_kpi_table": name in KPI_TABLES_KNOWN,
                    "kpi_keyword_match": is_kpi_relevant(name)
                    and name not in KPI_TABLES_KNOWN,
                }
            )
        kpi_matches = [r for r in rows if r["known_kpi_table"] or r["kpi_keyword_match"]]
        return {
            "ok": True,
            "warehouse": connect_id,
            "connection_mode": conn_mode,
            "connect_id": connect_id,
            "fetch_db": fetch_db,
            "schema": schema_name,
            "bundle": bundle,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "tables_source": tables_source,
            "last_fetch_error": _last_fetch_error,
            "table_count": len(all_names),
            "filtered_count": len(rows),
            "kpi_tables_known": KPI_TABLES_KNOWN,
            "kpi_tables_known_present": [
                t for t in KPI_TABLES_KNOWN if t in all_names
            ],
            "kpi_tables_known_missing": [
                t for t in KPI_TABLES_KNOWN if t not in all_names
            ],
            "kpi_relevant_tables": kpi_matches,
            "tables": rows,
            "administraties_sample": df_records(load_administraties_sample()),
            "awc_admin_code": AWC_ADMIN_CODE,
            "next_steps": [
                "bundle=kpi — columns for known + keyword-matched tables",
                "bundle=full&filter=order — all columns, optional name filter",
                "bundle=table&table=Ontvangsten — one table + foreign keys",
            ],
        }

    if bundle == "kpi":
        selected = []
        for name in all_names:
            if is_kpi_relevant(name) and apply_name_filter(name, name_filter):
                selected.append(name)
        selected = sorted(set(selected))
        cols_df = load_columns(schema_name, selected)
        cols_by_table = group_columns(cols_df)
        tables_out = [
            table_entry(
                name,
                schema_name,
                counts_map,
                cols_by_table,
                {
                    "known_kpi_table": name in KPI_TABLES_KNOWN,
                    "kpi_keyword_match": is_kpi_relevant(name)
                    and name not in KPI_TABLES_KNOWN,
                },
            )
            for name in selected
        ]
        return {
            "ok": True,
            "warehouse": connect_id,
            "connection_mode": conn_mode,
            "connect_id": connect_id,
            "fetch_db": fetch_db,
            "schema": schema_name,
            "bundle": bundle,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "table_count": len(all_names),
            "kpi_table_count": len(tables_out),
            "kpi_tables_known": KPI_TABLES_KNOWN,
            "tables": tables_out,
            "foreign_keys": df_records(load_foreign_keys(schema_name)),
            "administraties_sample": df_records(load_administraties_sample()),
            "awc_admin_code": AWC_ADMIN_CODE,
        }

    # bundle == full
    filtered_names = [
        n for n in all_names if apply_name_filter(n, name_filter)
    ][:max_tables]
    cols_df = load_columns(schema_name, filtered_names)
    cols_by_table = group_columns(cols_df)
    tables_out = [
        table_entry(name, schema_name, counts_map, cols_by_table)
        for name in filtered_names
    ]
    return {
        "ok": True,
        "warehouse": connect_id,
        "connection_mode": conn_mode,
        "connect_id": connect_id,
        "fetch_db": fetch_db,
        "schema": schema_name,
        "bundle": bundle,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "table_count": len(all_names),
        "returned_count": len(tables_out),
        "truncated": len(filtered_names) < len(
            [n for n in all_names if apply_name_filter(n, name_filter)]
        ),
        "max_tables": max_tables,
        "tables": tables_out,
        "note": "Use filter= or bundle=kpi to narrow output on large databases.",
    }
