#!/usr/bin/env python3
"""Insertar métodos VPS en live_analysis.js"""

# Leer archivo
with open("/home/biotrack/master-clean/app/static/js/live_analysis.js", "r") as f:
    lines = f.readlines()

# Encontrar línea de setupEventListeners
setup_line = None
for i, line in enumerate(lines):
    if "setupEventListeners()" in line and line.strip().startswith("setupEventListeners"):
        setup_line = i
        break

if setup_line:
    # Código VPS a insertar
    vps_code = '''
    startVPSFrameCapture() {
        console.log('[VPS] Iniciando captura...');
        const videoElement = document.getElementById('videoFeed');
        if (!videoElement || videoElement.tagName !== 'VIDEO') return;
        this.vpsCanvas = document.createElement('canvas');
        this.vpsContext = this.vpsCanvas.getContext('2d');
        this.vpsCanvas.width = 960;
        this.vpsCanvas.height = 540;
        this.vpsFrameInterval = setInterval(async () => {
            try {
                this.vpsContext.drawImage(videoElement, 0, 0, 960, 540);
                const frameB64 = this.vpsCanvas.toDataURL('image/jpeg', 0.8);
                const resp = await fetch('/api/vps/process_frame', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ frame: frameB64, exercise_key: this.config.exercise_key, segment_type: this.config.segment_type })
                });
                const result = await resp.json();
                if (result.success) this.updateVPSData(result);
            } catch (e) { console.error('[VPS]', e); }
        }, 100);
        console.log('[VPS] Captura activa');
    }
    
    stopVPSFrameCapture() {
        if (this.vpsFrameInterval) clearInterval(this.vpsFrameInterval);
    }
    
    updateVPSData(r) {
        const el = document.getElementById('currentAngle');
        if (el && r.current_angle) el.textContent = Math.round(r.current_angle) + '°';
    }

'''
    lines.insert(setup_line, vps_code)
    
    # Guardar
    with open("/home/biotrack/master-clean/app/static/js/live_analysis.js", "w") as f:
        f.writelines(lines)
    
    print(f"✅ Métodos VPS insertados en línea {setup_line}")
else:
    print("❌ No se encontró setupEventListeners")
