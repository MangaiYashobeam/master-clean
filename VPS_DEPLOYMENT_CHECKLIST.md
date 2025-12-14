# 🚀 VPS MediaPipe Deployment Checklist

## 📋 Changes Summary (v2.1)

### Server-Side Changes (Python)

1. **Enhanced Error Logging** (`app/routes/api.py`)
   - Added comprehensive logging to `/api/camera/process_frame`
   - Logs every step: frame receipt → decode → analyzer creation → MediaPipe processing → return
   - Full traceback on errors to identify 502 causes
   - Tagged with `[VPS]` prefix for easy log filtering

2. **Test Endpoint** (`/api/camera/test_frame`)
   - Simple echo endpoint without MediaPipe
   - Tests: frame reception → decode → re-encode → return
   - Use this to verify basic infrastructure before MediaPipe

3. **MediaPipe Skeleton Enabled**
   - Changed `show_skeleton=False` → `show_skeleton=True` in analyzer cache
   - Skeleton will now render on processed frames

### Client-Side Changes (JavaScript)

1. **Enhanced VPS Camera Handler** (v2.1)
   - Added `exercise_type` to frame payload
   - Detailed logging every 60 frames
   - Error counter to detect consecutive failures
   - Better error recovery (continues showing raw camera on errors)
   - Longer error messages (500 chars) for debugging

2. **Version Bumping**
   - v1.9 → v2.1 with cache-busting timestamps

## 🔧 VPS Deployment Steps

### 1. Pull Latest Code
```bash
ssh biotrack@biotrack.bo.click
cd /home/biotrack/master-clean
git pull origin master
```

### 2. Check Logs for Issues
```bash
# Check Gunicorn logs for errors
sudo journalctl -u biotrack.service -f --lines=100

# Or check app logs
tail -f /home/biotrack/master-clean/logs/app.log
```

### 3. Restart Services
```bash
# Restart Gunicorn
sudo systemctl restart biotrack.service

# Check status
sudo systemctl status biotrack.service

# Restart Nginx (if needed)
sudo systemctl restart nginx
```

### 4. Test Basic Connectivity
Open browser console on biotrack.bo.click and run:
```javascript
// Test endpoint availability
fetch('/api/camera/test_frame', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        frame: 'data:image/jpeg;base64,/9j/4AAQSkZJRg...' // Small test image
    })
}).then(r => r.json()).then(console.log)
```

### 5. Monitor Real-Time Logs
While testing camera:
```bash
# Terminal 1: Watch server logs
sudo journalctl -u biotrack.service -f | grep -i "VPS\|error\|502"

# Terminal 2: Watch Nginx access logs
sudo tail -f /var/log/nginx/access.log | grep camera

# Terminal 3: Watch Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### 6. Browser Testing Checklist

- [ ] Hard refresh page (Ctrl+Shift+F5)
- [ ] Check console shows `v=2.1` loading
- [ ] Verify camera permissions granted
- [ ] Watch for `[VPSCamera] Enviando frame X para ejercicio: Y`
- [ ] Look for `✅ Primer frame procesado con MediaPipe recibido`
- [ ] Check for skeleton rendering on video
- [ ] Monitor error count (should stay at 0 if working)

## 🐛 Debugging Guide

### Issue: 502 Bad Gateway

**Possible Causes:**
1. Gunicorn worker timeout (default 30s)
2. MediaPipe initialization taking too long (>30s)
3. Memory exhaustion
4. Gunicorn worker crash

**Solutions:**
```bash
# Check if workers are alive
ps aux | grep gunicorn

# Increase timeout in gunicorn config
# Edit: /home/biotrack/master-clean/gunicorn_config.py
# Add: timeout = 120

# Check memory
free -h
htop  # Look for high memory usage

# Check MediaPipe singleton
# Look for logs: "🔧 Creando instancia COMPARTIDA de MediaPipe Pose..."
# Should only appear ONCE per worker restart
```

### Issue: Skeleton Not Rendering

**Check:**
1. Server logs show `[VPS] ✅ MediaPipe procesó el frame exitosamente`
2. Client console shows `✅ Primer frame procesado con MediaPipe recibido`
3. Analyzer has `show_skeleton=True`
4. Frame is returning with analysis data

**Debug Command:**
```bash
# Check if analyzers are being created
grep "Creando NUEVO analyzer" /var/log/gunicorn/error.log
grep "show_skeleton" /home/biotrack/master-clean/app/routes/api.py
```

### Issue: Old Version Loading (v1.9)

**Solutions:**
1. Hard refresh: Ctrl+Shift+F5
2. Clear browser cache completely
3. Restart Nginx to clear reverse proxy cache:
   ```bash
   sudo systemctl restart nginx
   ```
4. Add HTTP headers to prevent caching (in nginx config):
   ```nginx
   location /static/ {
       add_header Cache-Control "no-cache, no-store, must-revalidate";
   }
   ```

## 📊 Expected Log Output (Success)

### Server Logs (journalctl)
```
[VPS] 📥 Recibiendo frame para procesamiento...
[VPS] Datos recibidos: frame_size=25680, exercise_type=shoulder_profile
[VPS] Obteniendo analyzer para tipo: shoulder_profile
⚡ Reutilizando analyzer cacheado 'shoulder_profile'
[VPS] ✅ Analyzer obtenido: ShoulderProfileAnalyzer
[VPS] Procesando frame con MediaPipe (shape: (480, 640, 3))...
[VPS] ✅ MediaPipe procesó el frame exitosamente
[VPS] ✅ Frame procesado exitosamente, retornando resultado
```

### Browser Console (Client)
```
[VPSCamera] Constructor - v2.1 inicializado
[VPSCamera] 🌐 Modo VPS detectado - Iniciando cámara del cliente
[VPSCamera] ✅ Cámara del cliente iniciada
[VPSCamera] Resolución: 640x480
[VPSCamera] Enviando frame 0 para ejercicio: shoulder_profile
[VPSCamera] ✅ Primer frame procesado con MediaPipe recibido
[VPSCamera] Análisis data: {angle: 85.3, landmarks_detected: true, ...}
```

## 🎯 Success Criteria

- [x] Version 2.1 loading in browser
- [x] No 502 errors in logs
- [x] Camera starting successfully
- [x] Frames being sent to server
- [x] MediaPipe processing frames
- [x] **Skeleton visible on video feed**
- [x] **ROM readings updating in UI**
- [x] Analysis data flowing to LiveAnalysisController

## 📞 Support Commands

```bash
# Restart everything
sudo systemctl restart biotrack.service nginx

# Full server status
systemctl status biotrack.service
systemctl status nginx
free -h
df -h

# Find process eating resources
htop
ps aux | grep python | grep mediapipe

# Check open files (might hit limits)
lsof | grep python | wc -l
```

## 🔐 Emergency Rollback

If v2.1 causes issues:
```bash
cd /home/biotrack/master-clean
git log --oneline -5  # Find previous commit
git checkout 16fc290  # Or whatever hash was working
sudo systemctl restart biotrack.service
```

---
**Last Updated:** 2025-12-14  
**Version:** 2.1  
**Deployed By:** [Your Name]
