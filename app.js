/**
 * AURA LOGx SIMULATOR - External Medical Equipment Telemetry Streamer
 * Core JavaScript Engine
 */

class AuraLogGenerator {
  constructor() {
    this.timer = null;
    this.isStreaming = false;
    this.isPaused = false;
    this.streamMode = 'single'; // 'single' or 'fleet'
    this.currentScenario = 'OK';
    this.fleetIndex = 0;

    // Statistics
    this.stats = {
      sent: 0,
      success: 0,
      anomalies: 0,
      errors: 0,
      totalLatencyMs: 0
    };

    this.logsHistory = [];

    // Preconfigured Fleet Devices
    this.fleetDevices = [
      { id: 'DEV000001', type: 'Ventilator', dept: 'Intensive Care Unit (ICU)' },
      { id: 'DEV000002', type: 'Patient monitor', dept: 'Intensive Care Unit (ICU)' },
      { id: 'DEV000003', type: 'CT scanner', dept: 'Radiology Department' },
      { id: 'DEV000004', type: 'Infusion pump', dept: 'General Ward' },
      { id: 'DEV000005', type: 'ECG machine', dept: 'Clinical Laboratory' }
    ];

    // Waveform Animation State
    this.waveformOffset = 0;
    this.waveformHeartRate = 68;

    this.initElements();
    this.attachEventListeners();
    this.updateEndpointPreview();
    this.initWaveformCanvas();
  }

  initElements() {
    // Inputs
    this.serverIpInput = document.getElementById('serverIp');
    this.serverPortInput = document.getElementById('serverPort');
    this.hospitalIdInput = document.getElementById('hospitalId');
    this.apiKeyInput = document.getElementById('apiKey');
    this.endpointPreview = document.getElementById('endpointPreview');

    this.deviceIdInput = document.getElementById('deviceId');
    this.deviceTypeSelect = document.getElementById('deviceType');
    this.departmentSelect = document.getElementById('department');
    this.intervalSelect = document.getElementById('intervalSelect');

    // Controls & Toggles
    this.btnStart = document.getElementById('btnStartStream');
    this.btnPause = document.getElementById('btnPauseStream');
    this.btnStop = document.getElementById('btnStopStream');
    this.btnStep = document.getElementById('btnStepOnce');
    this.btnPing = document.getElementById('btnTestPing');
    this.btnModeSingle = document.getElementById('btnModeSingle');
    this.btnModeFleet = document.getElementById('btnModeFleet');

    // Containers
    this.singleControls = document.getElementById('singleDeviceControls');
    this.fleetControls = document.getElementById('fleetDeviceList');

    // Status & Stat Displays
    this.systemStatusBadge = document.getElementById('systemStatusBadge');
    this.systemStatusText = document.getElementById('systemStatusText');
    this.statSent = document.getElementById('statSent');
    this.statSuccess = document.getElementById('statSuccess');
    this.statAnomalies = document.getElementById('statAnomalies');

    // Gauges
    this.gaugeBattery = document.getElementById('gaugeBattery');
    this.gaugeTemp = document.getElementById('gaugeTemp');
    this.gaugeLoad = document.getElementById('gaugeLoad');
    this.gaugeVoltage = document.getElementById('gaugeVoltage');
    this.barBattery = document.getElementById('barBattery');
    this.barTemp = document.getElementById('barTemp');
    this.barLoad = document.getElementById('barLoad');
    this.barVoltage = document.getElementById('barVoltage');
    this.lastActiveChip = document.getElementById('lastActiveDeviceChip');

    // Terminal
    this.terminalConsole = document.getElementById('terminalConsole');
    this.autoScrollCheck = document.getElementById('autoScrollCheck');
    this.btnClearConsole = document.getElementById('btnClearConsole');
    this.btnExportLogs = document.getElementById('btnExportLogs');
    this.footerLatency = document.getElementById('footerLatency');
    this.footerLastStatus = document.getElementById('footerLastStatus');
    this.footerErrorCode = document.getElementById('footerErrorCode');

    // Scenario Badge
    this.scenarioBadge = document.getElementById('currentScenarioBadge');
    this.signalPulseRate = document.getElementById('signalPulseRate');
  }

  attachEventListeners() {
    // Config input changes update URL preview
    [this.serverIpInput, this.serverPortInput].forEach(el => {
      el.addEventListener('input', () => this.updateEndpointPreview());
    });

    // Mode switches
    this.btnModeSingle.addEventListener('click', () => this.setMode('single'));
    this.btnModeFleet.addEventListener('click', () => this.setMode('fleet'));

    // Streaming actions
    this.btnStart.addEventListener('click', () => this.startStreaming());
    this.btnPause.addEventListener('click', () => this.pauseStreaming());
    this.btnStop.addEventListener('click', () => this.stopStreaming());
    this.btnStep.addEventListener('click', () => this.sendSingleTelemetry());
    this.btnPing.addEventListener('click', () => this.pingServer());

    // Scenario buttons
    document.querySelectorAll('.scenario-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const scenario = btn.getAttribute('data-scenario');
        this.setScenario(scenario);
      });
    });

    // Console actions
    this.btnClearConsole.addEventListener('click', () => this.clearConsole());
    this.btnExportLogs.addEventListener('click', () => this.exportLogs());

    // Interval changes during live stream
    this.intervalSelect.addEventListener('change', () => {
      if (this.isStreaming && !this.isPaused) {
        this.restartStreamInterval();
      }
    });
  }

  getEndpoint() {
    const ip = this.serverIpInput.value.trim() || '127.0.0.1';
    const port = this.serverPortInput.value.trim() || '8000';
    return `http://${ip}:${port}/api/v1/ingest/telemetry`;
  }

  updateEndpointPreview() {
    this.endpointPreview.textContent = this.getEndpoint();
  }

  setMode(mode) {
    this.streamMode = mode;
    if (mode === 'single') {
      this.btnModeSingle.classList.add('active');
      this.btnModeFleet.classList.remove('active');
      this.singleControls.style.display = 'grid';
      this.fleetControls.style.display = 'none';
      this.logTerminal(`Switched to Single Device Mode (${this.deviceIdInput.value})`, 'system-msg');
    } else {
      this.btnModeSingle.classList.remove('active');
      this.btnModeFleet.classList.add('active');
      this.singleControls.style.display = 'none';
      this.fleetControls.style.display = 'flex';
      this.logTerminal(`Switched to Fleet Simulator Mode (5 hospital devices rotating)`, 'system-msg');
    }
  }

  setScenario(scenario) {
    this.currentScenario = scenario;
    document.querySelectorAll('.scenario-btn').forEach(b => {
      if (b.getAttribute('data-scenario') === scenario) {
        b.classList.add('active');
      } else {
        b.classList.remove('active');
      }
    });

    this.scenarioBadge.textContent = `ACTIVE: ${scenario}`;
    if (scenario === 'OK') {
      this.scenarioBadge.style.color = 'var(--color-success)';
      this.scenarioBadge.style.borderColor = 'rgba(16, 185, 129, 0.3)';
      this.scenarioBadge.style.background = 'rgba(16, 185, 129, 0.15)';
      this.waveformHeartRate = 68;
      this.signalPulseRate.textContent = 'RATE: 68 BPM / NORMAL';
      this.signalPulseRate.style.color = 'var(--color-success)';
    } else {
      this.scenarioBadge.style.color = 'var(--color-danger)';
      this.scenarioBadge.style.borderColor = 'rgba(239, 68, 68, 0.4)';
      this.scenarioBadge.style.background = 'rgba(239, 68, 68, 0.15)';
      this.waveformHeartRate = 125;
      this.signalPulseRate.textContent = `RATE: 125 BPM / FAULT: ${scenario}`;
      this.signalPulseRate.style.color = 'var(--color-danger)';
    }

    this.logTerminal(`Simulation scenario set to: ${scenario}`, 'system-msg');
  }

  quickInject(scenario) {
    this.setScenario(scenario);
    this.logTerminal(`⚡ Instant Failure Injected: ${scenario}`, 'log-danger');
    this.sendSingleTelemetry(scenario);
  }

  /**
   * Generate Telemetry Payload matching exact specification
   */
  generatePayload(overrideScenario = null) {
    const scenario = overrideScenario || this.currentScenario;
    const hosp = this.hospitalIdInput.value.trim() || 'demo-hospital';

    let devId, devType, dept;

    if (this.streamMode === 'single') {
      devId = this.deviceIdInput.value.trim() || 'DEV000001';
      devType = this.deviceTypeSelect.value;
      dept = this.departmentSelect.value;
    } else {
      const dev = this.fleetDevices[this.fleetIndex];
      devId = dev.id;
      devType = dev.type;
      dept = dev.dept;
      this.fleetIndex = (this.fleetIndex + 1) % this.fleetDevices.length;
    }

    let battery = +(85 + Math.random() * 14).toFixed(1);
    let temp = +(36.2 + Math.random() * 1.6).toFixed(1);
    let load = +(45 + Math.random() * 35).toFixed(1);
    let voltage = +(23.5 + Math.random() * 1.0).toFixed(1);
    let operatingHours = +(1200 + Math.random() * 3000).toFixed(1);
    let errorCode = scenario;

    // Apply Scenario Modifications
    if (scenario === 'BAT_CRITICAL') {
      battery = +(12.0 + Math.random() * 12.0).toFixed(1);
      voltage = +(17.5 + Math.random() * 1.5).toFixed(1);
      load = +(80 + Math.random() * 18).toFixed(1);
    } else if (scenario === 'BAT_WARN') {
      battery = +(26.0 + Math.random() * 8.0).toFixed(1);
    } else if (scenario === 'TEMP_CRITICAL') {
      temp = +(46.0 + Math.random() * 8.0).toFixed(1);
      load = +(90 + Math.random() * 9).toFixed(1);
    } else if (scenario === 'TEMP_WARN') {
      temp = +(39.5 + Math.random() * 3.0).toFixed(1);
    } else if (scenario === 'SENSOR_ERR') {
      temp = +(20.0 + Math.random() * 50.0).toFixed(1); // Erratic noise
      battery = +(50.0 + Math.random() * 40.0).toFixed(1);
    } else if (scenario === 'POWER_FLUC') {
      voltage = +(14.0 + Math.random() * 15.0).toFixed(1);
    } else if (scenario === 'SYS_RESET') {
      load = 99.0;
      operatingHours = 0.5;
    }

    const payload = {
      hospital_id: hosp,
      device_id: devId,
      device_type: devType,
      department: dept,
      timestamp: new Date().toISOString(),
      battery_health: battery,
      temperature: temp,
      load_percent: load,
      error_code: errorCode,
      operating_hours: operatingHours,
      voltage: voltage
    };

    return payload;
  }

  /**
   * Update visual gauges based on payload values
   */
  updateGauges(payload) {
    this.gaugeBattery.innerHTML = `${payload.battery_health}<span class="unit">%</span>`;
    this.gaugeTemp.innerHTML = `${payload.temperature}<span class="unit">°C</span>`;
    this.gaugeLoad.innerHTML = `${payload.load_percent}<span class="unit">%</span>`;
    this.gaugeVoltage.innerHTML = `${payload.voltage}<span class="unit">V</span>`;

    this.barBattery.style.width = `${Math.min(100, Math.max(0, payload.battery_health))}%`;
    if (payload.battery_health < 25) {
      this.barBattery.style.background = 'var(--color-danger)';
    } else if (payload.battery_health < 50) {
      this.barBattery.style.background = 'var(--color-warning)';
    } else {
      this.barBattery.style.background = 'var(--color-success)';
    }

    const tempPct = Math.min(100, Math.max(0, ((payload.temperature - 20) / 40) * 100));
    this.barTemp.style.width = `${tempPct}%`;
    if (payload.temperature >= 44) {
      this.barTemp.style.background = 'var(--color-danger)';
    } else if (payload.temperature >= 39) {
      this.barTemp.style.background = 'var(--color-warning)';
    } else {
      this.barTemp.style.background = 'var(--color-primary)';
    }

    this.barLoad.style.width = `${payload.load_percent}%`;
    this.barVoltage.style.width = `${Math.min(100, (payload.voltage / 30) * 100)}%`;

    this.lastActiveChip.textContent = `${payload.device_id} (${payload.device_type})`;
    this.footerErrorCode.textContent = payload.error_code;
    if (payload.error_code === 'OK') {
      this.footerErrorCode.className = 'tag-ok';
    } else {
      this.footerErrorCode.className = 'tag-alert';
    }
  }

  /**
   * Send single telemetry HTTP POST request
   */
  async sendSingleTelemetry(overrideScenario = null) {
    const payload = this.generatePayload(overrideScenario);
    this.updateGauges(payload);

    const url = this.getEndpoint();
    const apiKey = this.apiKeyInput.value.trim();
    const hospId = this.hospitalIdInput.value.trim();

    this.stats.sent++;
    this.statSent.textContent = this.stats.sent;

    const startTime = performance.now();

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
          'Hospital-ID': hospId
        },
        body: JSON.stringify(payload)
      });

      const latency = Math.round(performance.now() - startTime);
      this.footerLatency.textContent = `${latency} ms`;

      let responseData = null;
      try {
        responseData = await response.json();
      } catch (e) {
        responseData = { text: await response.text() };
      }

      if (response.ok) {
        this.stats.success++;
        this.statSuccess.textContent = this.stats.success;
        this.footerLastStatus.textContent = `HTTP ${response.status} OK`;
        this.footerLastStatus.className = 'tag-ok';

        const isAnomaly = responseData.anomaly_detected || 
                          responseData.anomaly_score > 0.6 || 
                          payload.error_code !== 'OK';

        if (isAnomaly) {
          this.stats.anomalies++;
          this.statAnomalies.textContent = this.stats.anomalies;
        }

        const logType = isAnomaly ? 'log-warning' : 'log-success';
        const anomalyStr = responseData.anomaly_score !== undefined ? ` | Anomaly Score: ${responseData.anomaly_score}` : '';
        const serverStatus = responseData.status || 'INGESTED';

        this.logTerminal(
          `POST ➔ <strong>${payload.device_id}</strong> (${payload.device_type}) | Code: <span class="json-tag ${payload.error_code === 'OK' ? 'tag-ok' : 'tag-alert'}">${payload.error_code}</span> | Bat: ${payload.battery_health}% | Temp: ${payload.temperature}°C | Server: ${serverStatus}${anomalyStr} (${latency}ms)`,
          logType
        );
      } else {
        this.stats.errors++;
        this.footerLastStatus.textContent = `HTTP ${response.status}`;
        this.footerLastStatus.className = 'tag-alert';
        this.logTerminal(
          `HTTP ERROR ${response.status} for ${payload.device_id}: ${JSON.stringify(responseData)}`,
          'log-error'
        );
      }

      this.logsHistory.push({
        timestamp: new Date().toISOString(),
        payload: payload,
        response: responseData,
        status: response.status,
        latencyMs: latency
      });

    } catch (error) {
      const latency = Math.round(performance.now() - startTime);
      this.footerLatency.textContent = `${latency} ms`;
      this.stats.errors++;
      this.footerLastStatus.textContent = 'CONNECT ERR';
      this.footerLastStatus.className = 'tag-alert';

      this.logTerminal(
        `Failed to reach AURA Server at ${url}: ${error.message}. Ensure backend is running on target machine.`,
        'log-error'
      );

      this.logsHistory.push({
        timestamp: new Date().toISOString(),
        payload: payload,
        error: error.message,
        status: 'FAILED',
        latencyMs: latency
      });
    }
  }

  /**
   * Ping Server Health Check
   */
  async pingServer() {
    const ip = this.serverIpInput.value.trim() || '127.0.0.1';
    const port = this.serverPortInput.value.trim() || '8000';
    const healthUrl = `http://${ip}:${port}/docs`;

    this.logTerminal(`Pinging target server http://${ip}:${port} ...`, 'system-msg');
    const start = performance.now();
    try {
      await fetch(`http://${ip}:${port}/api/v1/devices/overview`, { method: 'GET', mode: 'no-cors' });
      const lat = Math.round(performance.now() - start);
      this.logTerminal(`Target Server http://${ip}:${port} is reachable! (${lat}ms)`, 'log-success');
    } catch (err) {
      this.logTerminal(`Target Server test responded. Ensure CORS or API is active on port ${port}.`, 'log-warning');
    }
  }

  startStreaming() {
    if (this.isStreaming && !this.isPaused) return;

    this.isStreaming = true;
    this.isPaused = false;

    this.btnStart.style.display = 'none';
    this.btnPause.style.display = 'inline-flex';
    this.btnStop.style.display = 'inline-flex';

    this.updateStatusBadge('STREAMING', 'streaming');
    const intervalMs = parseInt(this.intervalSelect.value, 10) || 3000;

    this.logTerminal(`Started continuous telemetry stream (Every ${intervalMs / 1000}s) to ${this.getEndpoint()}`, 'system-msg');

    // Send first log immediately
    this.sendSingleTelemetry();

    this.timer = setInterval(() => {
      this.sendSingleTelemetry();
    }, intervalMs);
  }

  pauseStreaming() {
    if (!this.isStreaming) return;

    if (!this.isPaused) {
      clearInterval(this.timer);
      this.isPaused = true;
      this.btnPause.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
        Resume Stream
      `;
      this.updateStatusBadge('PAUSED', 'paused');
      this.logTerminal('Telemetry stream paused.', 'guide-msg');
    } else {
      this.isPaused = false;
      this.btnPause.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>
        Pause Stream
      `;
      this.updateStatusBadge('STREAMING', 'streaming');
      const intervalMs = parseInt(this.intervalSelect.value, 10) || 3000;
      this.timer = setInterval(() => {
        this.sendSingleTelemetry();
      }, intervalMs);
      this.logTerminal('Telemetry stream resumed.', 'system-msg');
    }
  }

  restartStreamInterval() {
    clearInterval(this.timer);
    const intervalMs = parseInt(this.intervalSelect.value, 10) || 3000;
    this.timer = setInterval(() => {
      this.sendSingleTelemetry();
    }, intervalMs);
    this.logTerminal(`Stream frequency updated to ${intervalMs / 1000}s interval.`, 'system-msg');
  }

  stopStreaming() {
    clearInterval(this.timer);
    this.isStreaming = false;
    this.isPaused = false;

    this.btnStart.style.display = 'inline-flex';
    this.btnPause.style.display = 'none';
    this.btnStop.style.display = 'none';

    this.updateStatusBadge('STANDBY', 'idle');
    this.logTerminal('Telemetry stream stopped.', 'guide-msg');
  }

  updateStatusBadge(text, className) {
    this.systemStatusText.textContent = text;
    const dot = this.systemStatusBadge.querySelector('.status-indicator-dot');
    dot.className = `status-indicator-dot ${className}`;
  }

  logTerminal(message, cssClass = '') {
    const entry = document.createElement('div');
    entry.className = `terminal-entry ${cssClass}`;

    const time = new Date().toLocaleTimeString('en-GB', { hour12: false });
    entry.innerHTML = `<span class="time">[${time}]</span> <span class="msg">${message}</span>`;

    this.terminalConsole.appendChild(entry);

    if (this.autoScrollCheck.checked) {
      this.terminalConsole.scrollTop = this.terminalConsole.scrollHeight;
    }
  }

  clearConsole() {
    this.terminalConsole.innerHTML = `
      <div class="terminal-entry system-msg">
        <span class="time">[CLEARED]</span>
        <span class="msg">Terminal console log buffer reset.</span>
      </div>
    `;
  }

  exportLogs() {
    if (this.logsHistory.length === 0) {
      alert('No logs recorded yet to export.');
      return;
    }
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(this.logsHistory, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `aura_telemetry_logs_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  }

  /**
   * Oscilloscope Real-time Waveform Canvas Render
   */
  initWaveformCanvas() {
    const canvas = document.getElementById('waveformCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const draw = () => {
      const width = canvas.width;
      const height = canvas.height;
      const midY = height / 2;

      ctx.fillStyle = '#070a10';
      ctx.fillRect(0, 0, width, height);

      // Draw subtle grid
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
      ctx.lineWidth = 1;
      for (let x = 0; x < width; x += 30) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += 20) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // ECG wave calculation
      ctx.beginPath();
      ctx.strokeStyle = this.currentScenario === 'OK' ? '#10b981' : '#ef4444';
      ctx.lineWidth = 2;
      ctx.shadowColor = this.currentScenario === 'OK' ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)';
      ctx.shadowBlur = 6;

      const speed = this.currentScenario === 'OK' ? 2.5 : 4.5;
      this.waveformOffset += speed;

      for (let x = 0; x < width; x++) {
        const t = (x + this.waveformOffset) % 180;
        let y = midY;

        // ECG P-Q-R-S-T wave model
        if (t > 40 && t < 55) {
          y -= Math.sin(((t - 40) / 15) * Math.PI) * 6; // P wave
        } else if (t >= 55 && t < 62) {
          y += ((t - 55) / 7) * 4; // Q wave
        } else if (t >= 62 && t < 72) {
          y -= ((t - 62) / 10) * 32; // R spike
        } else if (t >= 72 && t < 80) {
          y += ((t - 72) / 8) * 12; // S drop
        } else if (t >= 95 && t < 125) {
          y -= Math.sin(((t - 95) / 30) * Math.PI) * 10; // T wave
        }

        // Add anomaly distortion if in failure scenario
        if (this.currentScenario !== 'OK') {
          y += (Math.random() - 0.5) * 6;
        }

        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }

      ctx.stroke();
      ctx.shadowBlur = 0; // reset shadow

      requestAnimationFrame(draw);
    };

    draw();
  }
}

// Instantiate Global App Instance
let app;
window.addEventListener('DOMContentLoaded', () => {
  app = new AuraLogGenerator();
});
