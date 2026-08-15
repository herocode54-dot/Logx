# AURA External Medical Equipment Log Generator & Telemetry Simulator

Standalone high-fidelity Medical Device Telemetry Generator & Anomaly Simulator designed to stream real-time sensor readings, operational metrics, and error codes over HTTP REST API into the **AURA AI-Powered Medical Device Reliability Intelligence Platform**.

---

## 🚀 Features

- **🌐 Interactive Web Application (`index.html`)**:
  - Glassmorphic dark cyberpunk UI with responsive layout.
  - Live animated oscilloscope waveform canvas that distorts during anomaly conditions.
  - Metric gauges: Battery Health, Component Temperature, Workload Factor, Supply Voltage.
  - Failure scenario injection: `BAT_CRITICAL`, `TEMP_CRITICAL`, `SENSOR_ERR`, `POWER_FLUC`, `SYS_RESET`.
  - Quick 1-click burst failure buttons.
  - Fleet Simulator mode (5 hospital devices in rotation) or Single Focused Device mode.
  - Live terminal console with real-time JSON payloads, auto-scroll, log filtering, and JSON export.
  - Server connection ping & latency monitor.

- **🐍 Standalone Python CLI (`external_hospital_log_generator.py`)**:
  - Lightweight script with no heavy dependencies (only `requests`).
  - Rich ANSI colored terminal output.
  - Configurable CLI flags for target server, hospital ID, stream intervals, count, and failure scenario.

---

## 📋 Telemetry Log JSON Payload Format

Every transmitted log strictly adheres to the AURA telemetry specification:

```json
{
  "hospital_id": "demo-hospital",
  "device_id": "DEV000001",
  "device_type": "Ventilator",
  "department": "Intensive Care Unit (ICU)",
  "timestamp": "2026-08-15T23:30:00Z",
  "battery_health": 88.5,
  "temperature": 37.2,
  "load_percent": 65.0,
  "error_code": "OK",
  "operating_hours": 1420.5,
  "voltage": 23.8
}
```

### Supported Error Codes:
- `OK` : Normal healthy device operation.
- `BAT_WARN` : Low battery health warning.
- `BAT_CRITICAL` : Critical battery degradation failure risk.
- `TEMP_WARN` : Elevated component temperature.
- `TEMP_CRITICAL` : High thermal overheating risk.
- `SENSOR_ERR` : Sensor calibration drift or noise.
- `POWER_FLUC` : Voltage fluctuation / supply instability.
- `SYS_RESET` : Microcontroller reboot/freeze event.

---

## 🛠️ Usage Instructions

### 1. Running the Web Simulator
Simply open `index.html` in any web browser, or serve it locally:

```bash
# Using Python
python -m http.server 3000

# Or open directly in browser
start index.html
```

1. Enter your Central AURA Server Host & Port (e.g. `127.0.0.1:8000` or the IP of your AURA server).
2. Click **Start Log Stream** to begin transmitting telemetry logs.
3. Use the **Failure Simulation Injector** buttons to trigger real-time anomalies for ML prediction.

---

### 2. Running the Python CLI Generator

```bash
# Basic usage with default settings (streams to 127.0.0.1:8000 every 3s)
python external_hospital_log_generator.py

# Custom Server IP & Port
python external_hospital_log_generator.py --server 192.168.1.50 --port 8000 --hospital demo-hospital

# Force a specific failure scenario (e.g. Battery Critical)
python external_hospital_log_generator.py --scenario BAT_CRITICAL --interval 1.0

# Stream 50 logs and exit
python external_hospital_log_generator.py --count 50
```

#### CLI Options:
| Flag | Default | Description |
|------|---------|-------------|
| `--server`, `-s` | `127.0.0.1` | Target AURA Server IP/host |
| `--port`, `-p` | `8000` | Target Server Port |
| `--hospital` | `demo-hospital` | Hospital Identifier |
| `--api-key` | `aura_live_ingest_key_2026` | Ingestion API Key |
| `--interval`, `-i` | `3.0` | Log transmission interval (seconds) |
| `--count`, `-c` | `0` (Infinite) | Total number of logs to send |
| `--scenario` | None (Dynamic) | Force specific failure code (`OK`, `BAT_CRITICAL`, `TEMP_CRITICAL`, etc.) |
| `--single` | False | Target a single device (`DEV000001`) instead of multi-device fleet |
