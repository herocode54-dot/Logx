#!/usr/bin/env python3
"""
====================================================================================================
LOGx — Autonomous Random Telemetry & ML Anomaly Streamer
====================================================================================================
Automatically generates and streams mixed random telemetry logs (healthy OK values combined
with realistic random critical and warning conditions) into AURA AI Platform.
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

def rng(lo, hi): return round(random.uniform(lo, hi), 1)
def rngi(lo, hi): return random.randint(lo, hi)

def generate_autonomous_random_payload(hospital_id: str, anomaly_prob: float = 0.25) -> dict:
    dev = random.choice(DEVICE_REGISTRY)
    is_anomaly = random.random() < anomaly_prob

    error_code = "OK"
    battery = rng(85.0, 99.0)
    temp = rng(34.5, 37.8)
    load = rng(40.0, 75.0)
    volt = rng(22.5, 24.5)
    op_hours = rng(200.0, 3500.0)
    humidity = rng(35.0, 65.0)
    cycles = rngi(50, 400)
    days_maint = rngi(5, 90)
    err7d = rngi(0, 2)

    if is_anomaly:
        archetype = random.choice([
            "BAT_CRITICAL", "BAT_WARN", "TEMP_CRITICAL", "TEMP_WARN",
            "SENSOR_ERR", "POWER_FLUC", "SYS_RESET", "CASCADE"
        ])

        if archetype == "BAT_CRITICAL":
            error_code = "BAT_CRITICAL"
            battery = rng(10.0, 22.0)
            volt = rng(18.0, 22.0)
            load = rng(70.0, 90.0)
            cycles = rngi(800, 1200)
            days_maint = rngi(90, 250)
        elif archetype == "BAT_WARN":
            error_code = "BAT_WARN"
            battery = rng(24.0, 35.0)
            cycles = rngi(600, 900)
        elif archetype == "TEMP_CRITICAL":
            error_code = "TEMP_CRITICAL"
            temp = rng(46.0, 58.0)
            load = rng(85.0, 98.0)
            humidity = rng(60.0, 85.0)
        elif archetype == "TEMP_WARN":
            error_code = "TEMP_WARN"
            temp = rng(39.0, 43.5)
        elif archetype == "SENSOR_ERR":
            error_code = "SENSOR_ERR"
            err7d = rngi(8, 25)
            temp = rng(36.0, 42.0)
        elif archetype == "POWER_FLUC":
            error_code = "POWER_FLUC"
            volt = rng(14.0, 19.0)
            load = rng(80.0, 95.0)
            err7d = rngi(5, 15)
        elif archetype == "SYS_RESET":
            error_code = "SYS_RESET"
            load = rng(92.0, 99.9)
            temp = rng(40.0, 47.0)
        elif archetype == "CASCADE":
            error_code = "BAT_CRITICAL"
            battery = rng(8.0, 15.0)
            temp = rng(48.0, 60.0)
            load = rng(94.0, 99.0)
            volt = rng(12.0, 16.5)
            days_maint = rngi(300, 600)
            cycles = rngi(1100, 1500)

    payload = {
        "hospital_id": hospital_id,
        "device_id": dev["id"],
        "device_type": dev["type"],
        "department": dev["dept"],
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "battery_health": battery,
        "temperature": temp,
        "load_percent": load,
        "error_code": error_code,
        "operating_hours": op_hours,
        "voltage": volt,
        "humidity": humidity,
        "error_count_7d": err7d,
        "battery_cycles": cycles,
        "days_since_maint": days_maint
    }
    return payload

def main():
    p = argparse.ArgumentParser(description="LOGx Autonomous Random Telemetry Streamer")
    p.add_argument("--host", default="127.0.0.1", help="AURA host (default: 127.0.0.1)")
    p.add_argument("--port", default="8000", help="AURA port (default: 8000)")
    p.add_argument("--hospital", default="demo-hospital", help="Hospital ID")
    p.add_argument("--interval", type=float, default=3.0, help="Seconds between logs (default: 3.0)")
    p.add_argument("--anomaly-prob", type=float, default=0.25, help="Probability of random failure injection (0.0 to 1.0)")
    p.add_argument("--count", type=int, default=0, help="Logs to send (0 = infinite)")
    args = p.parse_args()

    url = f"http://{args.host}:{args.port}/api/v1/ingest/telemetry"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "aura_live_ingest_key_2026",
        "Hospital-ID": args.hospital
    }

    print("=" * 80)
    print(" LOGx Autonomous Random Telemetry Streamer")
    print(f" Target Server : {url}")
    print(f" Interval      : {args.interval}s | Anomaly Rate: {int(args.anomaly_prob*100)}%")
    print("=" * 80)
    print("Streaming live mixed telemetry logs... Press Ctrl+C to stop.\n")

    step = 0
    while True:
        step += 1
        if args.count and step > args.count:
            print(f"\n[DONE] Sent requested {args.count} logs.")
            break

        payload = generate_autonomous_random_payload(args.hospital, args.anomaly_prob)

        try:
            start_t = time.perf_counter()
            r = requests.post(url, json=payload, headers=headers, timeout=5)
            lat = round((time.perf_counter() - start_t) * 1000)

            if r.status_code == 200:
                d = r.json()
                risk = d.get("risk_level", "LOW")
                health = d.get("overall_health", 90.0)
                anomaly = d.get("anomaly_score", 15.0)

                icon = "🚨 CRITICAL" if risk == "CRITICAL" else ("⚠️ HIGH" if risk == "HIGH" else ("📊 MEDIUM" if risk == "MEDIUM" else "✅ LOW"))
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {icon:11} | {payload['device_id']} ({payload['device_type']}) "
                      f"Code:{payload['error_code']:13} Bat:{payload['battery_health']:5}% Temp:{payload['temperature']:5}°C "
                      f"➔ Risk:{risk:8} Health:{health:5}% Anomaly:{anomaly} ({lat}ms)")
            else:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ HTTP {r.status_code}: {r.text[:120]}")
        except requests.exceptions.ConnectionError:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Connection failed to {url}. Is AURA server running?")
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Error: {e}")

        time.sleep(args.interval)

if __name__ == "__main__":
    main()
