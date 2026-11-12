import requests, time, json, datetime
from collections import Counter

# Dagelijkse sync van Sprinter3000-zendingen naar sprinter_api.shipments.
# Sinds 12-11-2026 daarna ook offertes (sprinter_api.quotations) en bedrijven (sprinter_api.companies),
# volledig opnieuw (1.249 en 3.145 rijen; 2 en 4 aanvragen). Zie het blok onderaan.
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

# ---------- Offertes en bedrijven (sinds 12-11-2026) ----------
# Deze tabellen zijn op 10-11-2026 eenmalig gevuld (app 17863). Hier halen we ze elke run volledig opnieuw op.
# Elk record wordt eerst gelijkgetrokken met de kolomtypes van 12-11 (geen nieuwe gesplitste kolommen).
# Mocht de writer toch <kolom>__t/__s maken, dan voegen we die samen; we verwijderen ze nooit.
# Een fout hier laat de zendingen ongemoeid, maar laat de run wel falen zodat het opvalt.

EXTRA = [("quotations", "quotation_id"), ("companies", "company_id")]
extra_fouten = []

# Kolomtypes zoals ze op 12-11-2026 in de warehouse stonden. Nieuwe kolommen uit de API maakt de writer zelf aan.
TYPES_12_11 = {
    "quotations": "_sdc_batched_at=timestamp with time zone;_sdc_received_at=timestamp with time zone;_sdc_sequence=bigint;_sdc_table_version=bigint;api_lock=text;charges_details=text;create_date=timestamp with time zone;customer_company=text;customer_company_id=bigint;customer_contact=text;customer_contact_id=bigint;customs_goods=text;department=text;department_id=bigint;description=text;dimension_height=text;dimension_length=text;dimension_width=text;direction=text;external_reference=text;external_reference2=text;external_reference3=text;external_reference4=text;external_url=text;from_city=text;from_country_code=text;from_zip_code=text;goods_description=text;incoterms=text;incoterms_country_code=text;incoterms_place=text;loading_meter_conversion=bigint;milestone_icons=text;milestone_ids=text;note=text;notice_of_load=text;package_code=text;payment_term=text;payment_term_id=bigint;port_of_arrival_code=text;port_of_departure_code=text;print_detail_amounts=bigint;print_legs=bigint;print_total_amount=bigint;progress_percentage=bigint;quotation_id=bigint;quotation_number=text;quotation_status_id=bigint;report_date=timestamp with time zone;sales_invoice_customer_company_id=text;shipment_id=bigint;shipment_mode=text;shipment_number=text;shipment_owner=text;shipment_owner_id=text;shipment_status=bigint;shipment_status_code=text;shipment_type=text;special_notes=text;system_uuid=text;temperature_high=text;temperature_low=text;title=text;to_city=text;to_country_code=text;to_zip_code=text;total_co2_emissions=text;total_goods_value_amount=text;total_goods_value_currency_amount=text;total_goods_value_currency_code=text;total_gpm_amount=double precision;total_gross_weight=double precision;total_loading_meter=double precision;total_nett_weight=text;total_pieces=bigint;total_purchase_amount=double precision;total_sales_amount=double precision;total_volume=double precision;total_volume_weight=double precision;totalize_amounts_in_quotation=text;transit_time=text;transport_insurance=text;transport_insurance_cancel=text;transport_insurance_code_id=text;transport_insurance_coverageid=text;transport_insurance_currency=text;transport_insurance_goodsvalue=text;transport_insurance_processed=text;update_date=timestamp with time zone;valid_until=text;vat_code=text;vat_code_id=text;volume_weight_conversion=bigint",
    "companies": "_sdc_batched_at=timestamp with time zone;_sdc_received_at=timestamp with time zone;_sdc_sequence=bigint;_sdc_table_version=bigint;accounting_contact_id=bigint;agent_company_id=text;bank_account_number=text;bank_account_number_stripped=text;bic=text;coc_number=text;coc_number_checked=text;coc_number_result=text;coc_number_valid=bigint;company_id=bigint;create_date=timestamp with time zone;currency_code=text;eori=text;eori_checked=text;eori_result=text;eori_valid=bigint;external_reference=text;head_office_address_id=bigint;invoice_address_id=bigint;language=text;milestone_ids=text;name=text;note=text;pop_up_remark=text;primary_contact_id=bigint;private_person=bigint;role_icons=text;role_ids=text;selection_code_ids=text;update_date=timestamp with time zone;vat_number=text;vat_number_address=text;vat_number_checked=text;vat_number_name=text;vat_number_request_identifier=text;vat_number_stripped=text;vat_number_valid=bigint;website=text",
}

def kolomtypes(tabel):
    # Een query op information_schema mag niet vanuit een Peliqan-app (404); daarom de vaste lijst.
    vast = TYPES_12_11.get(tabel, "")
    return dict(x.split("=", 1) for x in vast.split(";") if x)

def kolomnamen(tabel):
    df = dbconn.fetch(DB, query=f"SELECT * FROM {SCHEMA}.{tabel} LIMIT 1", df=True)
    return set(df.columns)

def gelijktrekken(rec, types):
    for k, v in list(rec.items()):
        if isinstance(v, (dict, list)):
            rec[k] = v = json.dumps(v, ensure_ascii=False)
        t = types.get(k)
        if v is None or t is None:
            continue
        if t in ("double precision", "numeric", "real") and isinstance(v, (int, float)) and not isinstance(v, bool):
            rec[k] = float(v)
        elif t in ("bigint", "integer", "smallint") and isinstance(v, float) and v.is_integer():
            rec[k] = int(v)
        elif t == "text" and not isinstance(v, str):
            rec[k] = json.dumps(v) if isinstance(v, bool) else str(v)
    return rec

def schema_extra(rows, types):
    props = {}
    for row in rows:
        for k, v in row.items():
            t = types.get(k)
            if t and t.startswith("timestamp"):
                props[k] = {"type": ["string", "null"], "format": "date-time"}; continue
            if t in ("double precision", "numeric", "real"): tt = "number"
            elif t in ("bigint", "integer", "smallint"): tt = "integer"
            elif t == "boolean": tt = "boolean"
            elif t == "text": tt = "string"
            elif v is None: continue
            elif isinstance(v, bool): tt = "boolean"
            elif isinstance(v, int): tt = "integer"
            elif isinstance(v, float): tt = "number"
            else: tt = "string"
            props[k] = {"type": [tt, "null"]}
    return {"properties": props}

def sync_volledig(tabel, pk):
    types = kolomtypes(tabel)
    if not types:
        raise RuntimeError(f"geen kolomtypes bekend voor {SCHEMA}.{tabel}")
    gestart = datetime.datetime.now(datetime.timezone.utc)
    off, opgehaald, aanvragen, ids = 0, 0, 0, []
    while True:
        rr = requests.get(f"{BASE}/{tabel}", headers=h, params={"offset": off, "limit": LIMIT}, timeout=180)
        aanvragen += 1
        if rr.status_code == 429:
            raise RuntimeError(f"{tabel}: Sprinter-limiet bereikt bij offset {off}")
        if rr.status_code != 200:
            raise RuntimeError(f"{tabel}: offset {off}: HTTP {rr.status_code} {rr.text[:200]}")
        body = rr.json()
        its = [gelijktrekken(x, types) for x in (body if isinstance(body, list) else [])]
        for i in range(0, len(its), 500):
            chunk = its[i:i+500]
            res = dbconn.write(SCHEMA, tabel, chunk, object_schema=schema_extra(chunk, types), pk=pk)
            if isinstance(res, dict) and str(res.get("status", "")).lower() not in ("success", "ok", "succeeded", ""):
                logs = (res.get("detail") or {}).get("logs") or []
                for line in logs[-10:]:
                    print("  ", str(line)[:600])
                raise RuntimeError(f"write naar {SCHEMA}.{tabel} mislukt: {str(res)[:300]}")
        opgehaald += len(its)
        ids.extend(int(x[pk]) for x in its if x.get(pk) is not None)
        if len(its) < LIMIT or aanvragen >= 20:
            break
        off += LIMIT
        time.sleep(1)
    # Gesplitste datumkolommen (als de writer die alsnog maakt) samenvoegen, alleen voor rijen uit deze run.
    try:
        nu = kolomnamen(tabel)
    except Exception as e:
        nu = set()
        print(f"{tabel}: kolomnamen niet op te vragen ({str(e)[:150]}); gesplitste kolommen niet gecontroleerd")
    for col, t in types.items():
        if t.startswith("timestamp") and (f"{col}__t" in nu or f"{col}__s" in nu):
            delen = []
            if f"{col}__t" in nu: delen.append(f'"{col}__t"')
            if f"{col}__s" in nu: delen.append(f'NULLIF("{col}__s", \'\')::timestamptz')
            sql(f'''UPDATE {SCHEMA}.{tabel} SET "{col}" = COALESCE({", ".join(delen)})
                    WHERE _sdc_batched_at >= '{gestart.isoformat()}' AND COALESCE({", ".join(delen)}) IS NOT NULL''')
            print(f"{tabel}: gesplitste kolom {col} samengevoegd")
    try:
        pq.refresh_table(database_name=DB, schema_name=SCHEMA, table_name=tabel, is_async=False)
    except Exception as e:
        print("refresh:", e)
    # De writer schrijft alleen gewijzigde rijen opnieuw (_sdc_batched_at blijft anders staan).
    # Controle: staat elke opgehaalde id in de tabel?
    uniek = sorted(set(ids))
    res = dbconn.fetch(DB, query=f"SELECT COUNT(*) AS n FROM {SCHEMA}.{tabel} WHERE {pk} IN ({','.join(map(str, uniek)) or 'NULL'})")
    aanwezig = int(scalar(res, "n"))
    res = dbconn.fetch(DB, query=f"SELECT COUNT(*) AS n FROM {SCHEMA}.{tabel} WHERE _sdc_batched_at >= '{gestart.isoformat()}'")
    bijgewerkt = int(scalar(res, "n"))
    print(f"{tabel}: opgehaald {opgehaald} | aanvragen {aanvragen} | aanwezig {aanwezig} van {len(uniek)} | nieuw of gewijzigd {bijgewerkt}")
    if aanwezig < len(uniek):
        raise RuntimeError(f"{tabel}: {len(uniek) - aanwezig} van {len(uniek)} opgehaalde rijen ontbreken in de warehouse")

for tabel, pk in EXTRA:
    try:
        sync_volledig(tabel, pk)
    except Exception as e:
        print(f"FOUT bij {tabel}: {str(e)[:400]}")
        extra_fouten.append(f"{tabel}: {str(e)[:200]}")

if extra_fouten:
    raise RuntimeError("zendingen bijgewerkt, maar: " + " | ".join(extra_fouten))
print("KLAAR")
