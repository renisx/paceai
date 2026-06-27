"""
PaceAI — Backend per Railway
Legge i dati da Garmin Connect (SSO non ufficiale)
e li serve all'app HTML via API REST.
"""
import os, json, datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

try:
    import garminconnect
    GARMIN_OK = True
except ImportError:
    GARMIN_OK = False

app = Flask(__name__, static_folder="static")
CORS(app)

# Sessione Garmin in memoria (dura finché il server gira)
_client = None
_client_email = None

# ─── AUTH ───────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def login():
    global _client, _client_email
    body = request.get_json(force=True)
    email    = body.get("email","").strip()
    password = body.get("password","").strip()
    if not email or not password:
        return jsonify({"error":"Email e password richiesti"}), 400
    if not GARMIN_OK:
        return jsonify({"error":"garminconnect non installato"}), 500
    try:
        c = garminconnect.Garmin(email, password)
        c.login()
        _client = c
        _client_email = email
        name = c.get_full_name()
        return jsonify({"success": True, "name": name or email})
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route("/api/status")
def status():
    return jsonify({
        "ok": True,
        "garmin_lib": GARMIN_OK,
        "logged_in": _client is not None,
        "user": _client_email
    })

# ─── DATI GIORNALIERI ───────────────────────────────────
@app.route("/api/garmin/daily")
def daily():
    if not _client:
        return jsonify({"error":"Non autenticato"}), 401
    date = request.args.get("date", datetime.date.today().isoformat())
    week_ago = (datetime.date.fromisoformat(date) - datetime.timedelta(days=7)).isoformat()
    out = {"date": date}

    def safe(fn):
        try: return fn()
        except: return None

    # Body Battery
    bb = safe(lambda: _client.get_body_battery(date))
    if bb:
        last = bb[-1] if isinstance(bb, list) else bb
        out["body_battery"] = last.get("charged") or last.get("bodyBatteryStatValue")

    # HRV
    hrv = safe(lambda: _client.get_hrv_data(date))
    if hrv:
        s = hrv.get("hrvSummary", {})
        out["hrv"] = s.get("lastNight5MinHigh") or s.get("weeklyAvg")
        out["hrv_status"] = s.get("hrvStatusType")

    # FC riposo
    rhr = safe(lambda: _client.get_rhr_day(date))
    if rhr:
        vals = rhr.get("allMetrics",{}).get("metricsMap",{}).get("WELLNESS_RESTING_HEART_RATE",[{}])
        out["resting_hr"] = vals[0].get("value") if vals else None

    # Sonno
    sl = safe(lambda: _client.get_sleep_data(date))
    if sl and "dailySleepDTO" in sl:
        dto = sl["dailySleepDTO"]
        out["sleep_score"]  = dto.get("sleepScores",{}).get("overall",{}).get("value")
        secs = dto.get("sleepTimeSeconds")
        out["sleep_hours"]  = round(secs/3600,1) if secs else None

    # Stress
    st = safe(lambda: _client.get_stress_data(date))
    if st:
        out["avg_stress"] = st.get("avgStressLevel")

    # Passi
    sp = safe(lambda: _client.get_steps_data(date))
    if sp:
        out["steps"] = sum(s.get("steps",0) for s in sp if s.get("steps"))

    # Training readiness
    tr = safe(lambda: _client.get_training_readiness(date))
    if tr:
        r = tr[-1] if isinstance(tr,list) else tr
        out["training_readiness"] = r.get("score")
        out["training_status"]    = r.get("primaryFactor")

    # VO2 Max
    mx = safe(lambda: _client.get_max_metrics(date))
    if mx:
        for m in mx:
            if "generic" in m:
                out["vo2max"] = m["generic"].get("vo2MaxValue")
                break

    # Ultimi run
    acts = safe(lambda: _client.get_activities_by_date(week_ago, date, "running")) or []
    runs = []
    for a in acts[:7]:
        spd = a.get("averageSpeed",0)
        pace = None
        if spd and spd > 0:
            ps = 1000/spd
            pace = f"{int(ps//60)}:{int(ps%60):02d}"
        runs.append({
            "date":         a.get("startTimeLocal","")[:10],
            "distance_km":  round(a.get("distance",0)/1000, 2),
            "avg_pace":     pace,
            "avg_hr":       a.get("averageHR"),
            "calories":     a.get("calories"),
        })
    out["recent_runs"] = runs
    out["weekly_km"]   = round(sum(r["distance_km"] for r in runs), 1)

    return jsonify(out)

# ─── SERVE APP HTML ─────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:p>")
def static_files(p):
    return send_from_directory("static", p)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
