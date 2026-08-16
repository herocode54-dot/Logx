#!/usr/bin/env python3
"""
====================================================================================================
LOGx — AURA Headless Telemetry Streamer v3.0
====================================================================================================
High-fidelity ML-calibrated medical equipment telemetry streamer for AURA AI Platform.
====================================================================================================
"""
import time
import json
import random
import datetime
import argparse
import sys

try:
    import requests
except ImportError:
    print("\n[ERROR] 'requests' package is required. Install it using:\n  pip install requests\n")
    sys.exit(1)

DEVICE_REGISTRY = [
    {"id": "DEV000001", "type": "Ventilator",       "dept": "Intensive Care Unit (ICU)"},
    {"id": "DEV000005", "type": "Patient monitor",   "dept": "Intensive Care Unit (ICU)"},
    {"id": "DEV000010", "type": "CT scanner",        "dept": "Radiology Department"},
    {"id": "DEV000015", "type": "MRI scanner",       "dept": "Radiology Department"},
    {"id": "DEV000020", "type": "Blood analyzer",    "dept": "Clinical Laboratory"},
    {"id": "DEV000025", "type": "Infusion pump",     "dept": "General Ward"},
    {"id": "DEV000030", "type": "Defibrillator",     "dept": "Intensive Care Unit (ICU)"},
    {"id": "DEV000035", "type": "ECG machine",       "dept": "General Ward"},
    {"id": "DEV000040", "type": "Ultrasound machine","dept": "Radiology Department"},
    {"id": "DEV000045", "type": "PCR machine",       "dept": "Clinical Laboratory"},
    {"id": "DEV000050", "type": "Anesthesia machine","dept": "Intensive Care Unit (ICU)"},
    {"id": "DEV000055", "type": "X-ray machine",     "dept": "Radiology Department"},
]

SCENARIOS = {
    "normal"      : {"bat":(85,99),"temp":(34,38),"load":(40,75),"volt":(22,24.5),"code":"OK",           "days":(7,60),    "cyc":(50,300),    "err7d":(0,2)},
    "bat_critical": {"bat":(10,22),"temp":(36,39),"load":(70,90),"volt":(20,23),  "code":"BAT_CRITICAL",  "days":(90,200),  "cyc":(800,1200),  "err7d":(3,8)},
    "temp_critical":{"bat":(65,85),"temp":(45,58),"load":(85,98),"volt":(19,21),  "code":"TEMP_CRITICAL", "days":(60,150),  "cyc":(300,700),   "err7d":(2,6)},
    "sensor_err"  : {"bat":(70,90),"temp":(37,41),"load":(60,85),"volt":(21,24),  "code":"SENSOR_ERR",    "days":(45,120),  "cyc":(200,600),   "err7d":(8,20)},
    "power_fluc"  : {"bat":(60,80),"temp":(38,44),"load":(80,95),"volt":(15,19.5),"code":"POWER_FLUC",    "days":(60,180),  "cyc":(300,700),   "err7d":(4,12)},
    "maintenance" : {"bat":(55,78),"temp":(38,42),"load":(70,88),"volt":(21,23.5),"code":"BAT_WARN",      "days":(180,400), "cyc":(600,1000),  "err7d":(2,7)},
    "sys_reset"   : {"bat":(50,75),"temp":(39,46),"load":(88,99),"volt":(18,22),  "code":"SYS_RESET",     "days":(90,250),  "cyc":(400,900),   "err7d":(3,10)},
    "cascade"     : {"bat":(8,15), "temp":(50,62),"load":(95,99),"volt":(12,17),  "code":"BAT_CRITICAL",  "days":(300,600), "cyc":(1100,1500), "err7d":(20,40)},
}

def rng(lo, hi): return round(random.uniform(lo, hi), 1)
def rngi(lo, hi): return random.randint(lo, hi)

def build_payload(device, scenario_name="normal"):
    sc = SCENARIOS[scenario_name]
    return {
        "hospital_id"    : "demo-hospital",
        "device_id"      : device["id"],
        "device_type"    : device["type"],
        "department"     : device["dept"],
        "timestamp"      : datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "battery_health" : rng(*sc["bat"]),
        "temperature"    : rng(*sc["temp"]),
        "load_percent"   : rng(*sc["load"]),
        "voltage"        : rng(*sc["volt"]),
        "error_code"     : sc["code"],
        "operating_hours": rng(500, 6000),
        "humidity"       : rng(35, 75),
        "battery_cycles" : rngi(*sc["cyc"]),
        "days_since_maint": rngi(*sc["days"]),
        "error_count_7d" : rngi(*sc["err7d"]),
    }

def main():
    p = argparse.ArgumentParser(description="LOGx AURA Headless Streamer v3.0")
    p.add_argument("--host",     default="127.0.0.1", help="Target AURA Host / IP (default: 127.0.0.1)")
    p.add_argument("--port",     default="8000", help="Target AURA Port (default: 8000)")
    p.add_argument("--scenario", default="normal", choices=list(SCENARIOS.keys()), help="Failure scenario")
    p.add_argument("--interval", type=float, default=3.0, help="Stream interval in seconds")
    p.add_argument("--device",   default=None, help="Specific device ID (e.g. DEV000001)")
    p.add_argument("--count",    type=int, default=0, help="Total logs to send (0 = infinite)")
    args = p.parse_args()

    url = f"http://{args.host}:{args.port}/api/v1/ingest/telemetry"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "aura_live_ingest_key_2026",
        "Hospital-ID": "demo-hospital"
    }

    print("=" * 80)
    print(" LOGx AURA Headless Telemetry Streamer v3.0")
    print(f" Target Server : {url}")
    print(f" Scenario      : {args.scenario} (Interval: {args.interval}s)")
    print(f" Battery Range : {SCENARIOS[args.scenario]['bat']}% | Error Code: {SCENARIOS[args.scenario]['code']}")
    print("=" * 80)
    print("Press Ctrl+C to stop streaming.\n")

    step = 0
    while True:
        step += 1
        if args.count and step > args.count:
            print(f"\n[DONE] Sent requested {args.count} logs.")
            break

        if args.device:
            device = next((d for d in DEVICE_REGISTRY if d["id"] == args.device), DEVICE_REGISTRY[0])
        else:
            device = random.choice(DEVICE_REGISTRY)

        # In normal mode, periodically inject a failure every 8th log to simulate realistic conditions
        sc = args.scenario if args.scenario != "normal" else ("bat_critical" if step % 8 == 0 else "normal")
        payload = build_payload(device, sc)

        try:
            start_t = time.perf_counter()
            r = requests.post(url, json=payload, headers=headers, timeout=5)
            lat = round((time.perf_counter() - start_t) * 1000)

            if r.status_code == 200:
                d = r.json()
                risk = d.get("risk_level", "?")
                health = d.get("overall_health", 0)
                anomaly = d.get("anomaly_score", 0)

                icon = "🚨 CRITICAL!" if risk == "CRITICAL" else ("⚠️ HIGH!" if risk == "HIGH" else ("📊 MEDIUM" if risk == "MEDIUM" else "✅ LOW"))
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {icon} {device['id']} ({device['type']}) "
                      f"Code:{payload['error_code']:13} Bat:{payload['battery_health']:5}% Temp:{payload['temperature']:5}°C "
                      f"➔ Risk:{risk:8} Health:{health:5}% Anomaly:{anomaly} ({lat}ms)")
            else:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ HTTP {r.status_code}: {r.text[:150]}")
        except requests.exceptions.ConnectionError:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Cannot connect to AURA at {url} — is backend running?")
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Error: {e}")

        time.sleep(args.interval)

if __name__ == "__main__":
    main()
