import requests, time, json, datetime
from collections import Counter

# Dagelijkse sync van Sprinter3000-zendingen naar sprinter_api.shipments.
# De Sprinter-lijst (GET /shipments) staat op volgorde NIEUWSTE EERST: offset 0 = nieuwste zendingen.
# Elke run halen we de eerste WINDOW zendingen opnieuw op (nieuwe + recent gewijzigde).
# Zondag een dieper venster, zodat late wijzigingen (facturatie, bedragen) ook binnenkomen.
# Sprinter staat max. 100 aanvragen per uur per endpoint toe; deze run gebruikt er 3 tot 15.
#
# LET OP datumkolommen: de Peliqan-writer (target-postgres) schrijft create_date, update_date en
# report_date naar gesplitste kolommen <naam>__t (timestamp) en <naam>__s (tekst). De KPI-queries
# lezen de gewone kolommen create_date / update_date / report_date. Na elke write voegen we de
# gesplitste kolommen samen in de gewone kolom. NOOIT de __t/__s-kolommen verwijderen: dan faalt
# elke write met KeyError('create_date__t') (zo gebeurd op 10-11-2026).
# dbconn.write geeft bij een fout status 'failed' terug zonder exception; we controleren elke write.

BASE = "https://amsterdamfreight.sprinter3000.com/sapi"
SCHEMA = "sprinter_api"
DB = pq.DW_NAME
LIMIT = 1000
WINDOW = 15000 if datetime.date.today().weekday() == 6 else 3000
DATE_COLS = ["create_date", "update_date", "report_date"]

dbconn = pq.dbconnect(DB)

NUM_COLS = {"total_gpm_amount","total_gross_weight","total_loading_meter","total_nett_weight","total_pieces",
            "total_purchase_amount","total_sales_amount","total_volume","total_volume_weight",
            "loading_meter_conversion","volume_weight_conversion","progress_percentage"}

def sql(q):
    dbconn.execute(DB, query=q)

def clean(rec):
    for k, v in list(rec.items()):
        if isinstance(v, (dict, list)):
            rec[k] = json.dumps(v, ensure_ascii=False)
        elif k in NUM_COLS and isinstance(v, int) and not isinstance(v, bool):
            rec[k] = float(v)
    return rec

def schema_for(rows):
    props = {}
    for row in rows:
        for k, v in row.items():
            if k in DATE_COLS: props[k] = {"type": ["string","null"], "format": "date-time"}; continue
            if k in NUM_COLS: t = "number"
            elif v is None: continue
            elif isinstance(v, bool): t = "boolean"
            elif isinstance(v, int): t = "integer"
            elif isinstance(v, float): t = "number"
            else: t = "string"
            prev = props.get(k, {}).get("type", [None])[0]
            if prev and prev != t:
                t = "number" if {prev, t} <= {"integer","number"} else "string"
            props[k] = {"type": [t, "null"]}
    return {"properties": props}

def write_checked(chunk):
    res = dbconn.write(SCHEMA, "shipments", chunk, object_schema=schema_for(chunk), pk="shipment_id")
    if isinstance(res, dict) and str(res.get("status", "")).lower() not in ("success", "ok", "succeeded", ""):
        logs = (res.get("detail") or {}).get("logs") or []
        print("WRITE MISLUKT. Laatste regels van de writer:")
        for line in logs[-15:]:
            print("  ", str(line)[:600])
        raise RuntimeError(f"write naar {SCHEMA}.shipments mislukt: {str(res)[:300]}")
    return res

def scalar(res, col):
    if isinstance(res, list):
        return res[0][col]
    return res[col].iloc[0]

# Gesplitste datumkolommen moeten bestaan voor de writer (leeg is prima).
for col in DATE_COLS:
    sql(f'ALTER TABLE {SCHEMA}.shipments ADD COLUMN IF NOT EXISTS "{col}__t" timestamptz')
    sql(f'ALTER TABLE {SCHEMA}.shipments ADD COLUMN IF NOT EXISTS "{col}__s" text')

started = datetime.datetime.now(datetime.timezone.utc)

key = pq.get_secret("sprinter_client_key").strip()
r = requests.get(f"{BASE}/authorize/{key}", timeout=30); r.raise_for_status()
h = {"Authorization": f"Bearer {r.json()['bearer_token']}"}

offset, total, calls = 0, 0, 0
dates = Counter(); t0 = time.time()
while offset < WINDOW:
    rr = requests.get(f"{BASE}/shipments", headers=h, params={"offset": offset, "limit": LIMIT}, timeout=180)
    calls += 1
    if rr.status_code == 429:
        raise RuntimeError(f"Sprinter-limiet bereikt bij offset {offset}; volgende run haalt het in")
    if rr.status_code != 200:
        raise RuntimeError(f"offset {offset}: HTTP {rr.status_code} {rr.text[:200]}")
    body = rr.json()
    its = [clean(x) for x in (body if isinstance(body, list) else [])]
    for i in range(0, len(its), 500):
        write_checked(its[i:i+500])
    total += len(its)
    dates.update((s.get("create_date") or "")[:7] for s in its)
    print(f"offset {offset}: {len(its)} ({int(time.time()-t0)}s)")
    if len(its) < LIMIT:
        break
    offset += LIMIT
    time.sleep(1)

# Gesplitste datumkolommen samenvoegen in de gewone kolommen, alleen voor rijen uit deze run.
for col in DATE_COLS:
    sql(f'''UPDATE {SCHEMA}.shipments
            SET "{col}" = COALESCE("{col}__t", NULLIF("{col}__s", '')::timestamptz)
            WHERE _sdc_batched_at >= '{started.isoformat()}'
              AND ("{col}__t" IS NOT NULL OR NULLIF("{col}__s", '') IS NOT NULL)''')

try:
    pq.refresh_table(database_name=DB, schema_name=SCHEMA, table_name="shipments", is_async=False)
except Exception as e:
    print("refresh:", e)

# Controle: zijn de opgehaalde zendingen geschreven, en hebben ze een rapportdatum?
res = dbconn.fetch(DB, query=f"""SELECT COUNT(*) AS n,
        SUM(CASE WHEN report_date IS NULL THEN 1 ELSE 0 END) AS zonder_datum
    FROM {SCHEMA}.shipments WHERE _sdc_batched_at >= '{started.isoformat()}'""")
landed, zonder = int(scalar(res, "n")), int(scalar(res, "zonder_datum") or 0)
print(f"opgehaald: {total} | aanvragen: {calls} | geschreven: {landed} | zonder rapportdatum: {zonder} | per aanmaakmaand (nieuwste): {dict(sorted(dates.items())[-4:])}")
if landed < 0.95 * total:
    raise RuntimeError(f"maar {landed} van {total} zendingen staan na de run in de warehouse; write controleren")
if zonder > 0.05 * landed:
    raise RuntimeError(f"{zonder} van {landed} zendingen zonder rapportdatum; samenvoegen datumkolommen controleren")
print("KLAAR")
