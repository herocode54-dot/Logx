#!/usr/bin/env python3
"""
====================================================================================================
AURA MEDICAL DEVICE RELIABILITY INTELLIGENCE PLATFORM
EXTERNAL MEDICAL EQUIPMENT LOG GENERATOR & TELEMETRY STREAMER (CLI)
====================================================================================================
Description: Standalone python simulator that streams live medical device telemetry logs over HTTP REST API
             into the central AURA platform server.
====================================================================================================
"""

import sys
import time
import json
import random
import datetime
import argparse
try:
    import requests
except ImportError:
    print("\n[ERROR] 'requests' package is required. Install it using:\n  pip install requests\n")
    sys.exit(1)

# ANSI Color Codes for Terminal Output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

DEVICES_CATALOG = [
    {"id": "DEV000001", "type": "Ventilator", "dept": "Intensive Care Unit (ICU)"},
    {"id": "DEV000002", "type": "Patient monitor", "dept": "Intensive Care Unit (ICU)"},
    {"id": "DEV000003", "type": "CT scanner", "dept": "Radiology Department"},
    {"id": "DEV000004", "type": "Infusion pump", "dept": "General Ward"},
    {"id": "DEV000005", "type": "ECG machine", "dept": "Clinical Laboratory"},
    {"id": "DEV000006", "type": "MRI scanner", "dept": "Radiology Department"},
    {"id": "DEV000007", "type": "Defibrillator", "dept": "Emergency Ward"},
    {"id": "DEV000008", "type": "Dialysis unit", "dept": "Nephrology Unit"}
]

SCENARIOS = ["OK", "BAT_WARN", "BAT_CRITICAL", "TEMP_WARN", "TEMP_CRITICAL", "SENSOR_ERR", "POWER_FLUC", "SYS_RESET"]

def generate_telemetry_payload(hospital_id: str, device: dict, force_scenario: str = None) -> dict:
    """
    Generates a telemetry log conforming strictly to the AURA Ingestion Specification.
    """
    scenario = force_scenario if force_scenario else random.choice(["OK", "OK", "OK", "OK", "OK", "BAT_WARN", "TEMP_WARN"])
    
    battery = round(random.uniform(85.0, 99.0), 1)
    temp = round(random.uniform(35.5, 37.8), 1)
    load = round(random.uniform(40.0, 80.0), 1)
    voltage = round(random.uniform(23.2, 24.5), 1)
    op_hours = round(random.uniform(500.0, 4800.0), 1)
    error_code = scenario

    if scenario == "BAT_CRITICAL":
        battery = round(random.uniform(12.0, 22.0), 1)
        voltage = round(random.uniform(16.5, 18.5), 1)
        load = round(random.uniform(75.0, 95.0), 1)
    elif scenario == "BAT_WARN":
        battery = round(random.uniform(24.0, 32.0), 1)
    elif scenario == "TEMP_CRITICAL":
        temp = round(random.uniform(45.0, 52.5), 1)
        load = round(random.uniform(85.0, 98.0), 1)
    elif scenario == "TEMP_WARN":
        temp = round(random.uniform(39.0, 42.5), 1)
    elif scenario == "SENSOR_ERR":
        temp = round(random.uniform(15.0, 65.0), 1) # Erratic noise
        battery = round(random.uniform(30.0, 90.0), 1)
    elif scenario == "POWER_FLUC":
        voltage = round(random.uniform(13.0, 28.0), 1)
    elif scenario == "SYS_RESET":
        load = 99.9
        op_hours = 0.5

    payload = {
        "hospital_id": hospital_id,
        "device_id": device["id"],
        "device_type": device["type"],
        "department": device["dept"],
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "battery_health": battery,
        "temperature": temp,
        "load_percent": load,
        "error_code": error_code,
        "operating_hours": op_hours,
        "voltage": voltage
    }
    return payload

def run_streamer(server_ip: str, server_port: int, hospital_id: str, api_key: str, interval: float, count: int, force_scenario: str, fleet_mode: bool):
    ingest_url = f"http://{server_ip}:{server_port}/api/v1/ingest/telemetry"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
        "Hospital-ID": hospital_id
    }

    print("=" * 80)
    print(f"{CYAN}{BOLD} AURA EXTERNAL HOSPITAL MEDICAL LOG GENERATOR & STREAMER{RESET}")
    print("=" * 80)
    print(f" {BOLD}Target Server URL:{RESET}  {ingest_url}")
    print(f" {BOLD}Hospital ID:{RESET}        {hospital_id}")
    print(f" {BOLD}Stream Mode:{RESET}        {'Fleet (Multi-Device Round-Robin)' if fleet_mode else 'Single Device (DEV000001)'}")
    print(f" {BOLD}Stream Interval:{RESET}    {interval} seconds")
    print(f" {BOLD}Active Scenario:{RESET}    {force_scenario if force_scenario else 'Dynamic (Normal with periodic failures)'}")
    print("=" * 80)
    print(f"{YELLOW}Press Ctrl+C at any time to pause or terminate the stream.{RESET}\n")

    step = 0
    dev_index = 0
    success_count = 0
    failure_count = 0

    try:
        while True:
            step += 1
            if count and step > count:
                print(f"\n{GREEN}[COMPLETE] Finished sending requested {count} telemetry logs.{RESET}")
                break

            if fleet_mode:
                dev = DEVICES_CATALOG[dev_index]
                dev_index = (dev_index + 1) % len(DEVICES_CATALOG)
            else:
                dev = DEVICES_CATALOG[0]

            # In dynamic mode, inject a simulated failure every 10 logs
            step_scenario = force_scenario
            if not step_scenario:
                if step % 10 == 0:
                    step_scenario = random.choice(["BAT_CRITICAL", "TEMP_CRITICAL", "SENSOR_ERR"])
                else:
                    step_scenario = "OK"

            payload = generate_telemetry_payload(hospital_id, dev, force_scenario=step_scenario)
            now_str = datetime.datetime.now().strftime("%H:%M:%S")

            try:
                start_t = time.perf_counter()
                res = requests.post(ingest_url, json=payload, headers=headers, timeout=5.0)
                latency_ms = round((time.perf_counter() - start_t) * 1000)

                if res.status_code == 200:
                    success_count += 1
                    try:
                        data = res.json()
                        status = data.get("status", "INGESTED")
                        anomaly_score = data.get("anomaly_score", "N/A")
                        anomaly_flag = data.get("anomaly_detected", False)
                    except Exception:
                        status = "200 OK"
                        anomaly_score = "N/A"
                        anomaly_flag = False

                    if payload["error_code"] != "OK" or anomaly_flag:
                        tag_color = RED
                        code_tag = f"{RED}[FAULT: {payload['error_code']}]{RESET}"
                    else:
                        tag_color = GREEN
                        code_tag = f"{GREEN}[OK]{RESET}"

                    print(f"[{now_str}] {code_tag} {CYAN}{payload['device_id']}{RESET} ({dev['type']}) ➔ {tag_color}ACK 200{RESET} | Anomaly Score: {MAGENTA}{anomaly_score}{RESET} | Bat: {payload['battery_health']}% | Temp: {payload['temperature']}°C ({latency_ms}ms)")
                else:
                    failure_count += 1
                    print(f"[{now_str}] {RED}[HTTP {res.status_code}]{RESET} {payload['device_id']} Error: {res.text[:120]} ({latency_ms}ms)")

            except requests.exceptions.ConnectionError:
                failure_count += 1
                print(f"[{now_str}] {RED}[CONN ERROR]{RESET} Unable to connect to {ingest_url}. Is AURA backend running?")
            except requests.exceptions.Timeout:
                failure_count += 1
                print(f"[{now_str}] {RED}[TIMEOUT]{RESET} Request timed out after 5 seconds.")
            except Exception as e:
                failure_count += 1
                print(f"[{now_str}] {RED}[ERROR]{RESET} {e}")

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Telemetry stream interrupted by user.{RESET}")
        print(f"Summary: {GREEN}{success_count} logs acknowledged{RESET}, {RED}{failure_count} errors/dropped{RESET} out of {step - 1} transmissions.")

def main():
    parser = argparse.ArgumentParser(
        description="AURA External Medical Equipment Telemetry Streamer & Anomaly Generator"
    )
    parser.add_argument("--server", "-s", default="127.0.0.1", help="Target AURA Server Host or IP (default: 127.0.0.1)")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Target Server Port (default: 8000)")
    parser.add_argument("--hospital", default="demo-hospital", help="Target Hospital ID (default: demo-hospital)")
    parser.add_argument("--api-key", default="aura_live_ingest_key_2026", help="Ingestion API Key (default: aura_live_ingest_key_2026)")
    parser.add_argument("--interval", "-i", type=float, default=3.0, help="Stream interval in seconds (default: 3.0)")
    parser.add_argument("--count", "-c", type=int, default=0, help="Number of logs to send (0 = infinite continuous stream)")
    parser.add_argument("--scenario", choices=SCENARIOS, default=None, help="Force a continuous failure scenario (e.g. BAT_CRITICAL, TEMP_CRITICAL, SENSOR_ERR)")
    parser.add_argument("--fleet", action="store_true", default=True, help="Simulate multi-device hospital fleet (default: True)")
    parser.add_argument("--single", action="store_true", help="Simulate single device only (DEV000001)")

    args = parser.parse_args()
    fleet_mode = not args.single

    run_streamer(
        server_ip=args.server,
        server_port=args.port,
        hospital_id=args.hospital,
        api_key=args.api_key,
        interval=args.interval,
        count=args.count,
        force_scenario=args.scenario,
        fleet_mode=fleet_mode
    )

if __name__ == "__main__":
    main()
