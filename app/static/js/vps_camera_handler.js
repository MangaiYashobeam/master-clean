/**
 * 🌐 VPS CAMERA HANDLER - Manejo de cámara del cliente para modo VPS
 * ===================================================================
 * Captura video de la cámara del navegador y lo envía al servidor para
 * procesamiento con MediaPipe.
 * 
 * FLUJO:
 * 1. getUserMedia() obtiene stream de la cámara del cliente
 * 2. Canvas captura frames del video
 * 3. Frames se envían al servidor via HTTP POST
 * 4. Servidor procesa con MediaPipe y retorna frame procesado
 * 5. Frame procesado se muestra en el cliente
 * 
 * VERSION: 2.3
 * - Agregado: Logging detallado para debugging
 * - Agregado: exercise_type en payload
 * - Agregado: Manejo de errores mejorado
 * - Agregado: Modo test sin MediaPipe
 * - Agregado: Log de primer frame enviado
 * - Agregado: _updateAnalysisUI para actualizar UI directamente
 * 
 * Autor: BIOTRACK Team
 * Fecha: 2025-12-14
 */

// ⚠️ VERSION MARKER - Si no ves este log, el archivo no se actualizó
console.log('🔵 VPS_CAMERA_HANDLER VERSION 2.3 LOADED');

class VPSCameraHandler {
    constructor(options = {}) {
        this.options = {
            targetFPS: options.targetFPS || 10,
            quality: options.quality || 0.6,
            width: options.width || 640,
            height: options.height || 480,
            videoElementId: options.videoElementId || 'videoFeed',
            canvasElementId: options.canvasElementId || 'captureCanvas',
            processEndpoint: options.processEndpoint || '/api/camera/process_frame',
            testMode: options.testMode || false,  // Modo test sin MediaPipe
            ...options
        };
        
        this.stream = null;
        this.videoElement = null;
        this.canvasElement = null;
        this.canvasContext = null;
        this.isRunning = false;
        this.frameCount = 0;
        this.lastFrameTime = 0;
        this.processingFrame = false;
        this.consecutiveErrors = 0;  // Contador de errores consecutivos
        this.maxConsecutiveErrors = 5;  // Máximo antes de reintentar
        
        console.log('[VPSCamera] Constructor - v2.3 inicializado');
        
        // Crear elementos necesarios
        this._createElements();
    }
    
    /**
     * Crea los elementos de video y canvas necesarios
     */
    _createElements() {
        // Obtener o crear elemento de video para captura (oculto)
        this.captureVideo = document.getElementById('vpsCaptureVideo');
        if (!this.captureVideo) {
            this.captureVideo = document.createElement('video');
            this.captureVideo.id = 'vpsCaptureVideo';
            this.captureVideo.autoplay = true;
            this.captureVideo.playsInline = true;
            this.captureVideo.muted = true;
            this.captureVideo.style.display = 'none';
            document.body.appendChild(this.captureVideo);
        }
        
        // Canvas para capturar frames
        this.canvasElement = document.getElementById(this.options.canvasElementId);
        if (!this.canvasElement) {
            this.canvasElement = document.createElement('canvas');
            this.canvasElement.id = this.options.canvasElementId;
            this.canvasElement.width = this.options.width;
            this.canvasElement.height = this.options.height;
            this.canvasElement.style.display = 'none';
            document.body.appendChild(this.canvasElement);
        }
        this.canvasContext = this.canvasElement.getContext('2d');
        
        // Elemento donde se mostrará el video procesado
        // Buscar primero 'processedFrame', luego 'videoFeed'
        this.videoElement = document.getElementById(this.options.videoElementId);
        if (!this.videoElement) {
            this.videoElement = document.getElementById('videoFeed');
        }
        
        // Si aún no existe, crear uno
        if (!this.videoElement) {
            console.warn('[VPSCamera] Elemento de video no encontrado, creando uno nuevo');
            const videoWrapper = document.getElementById('videoWrapper');
            if (videoWrapper) {
                const img = document.createElement('img');
                img.id = this.options.videoElementId || 'processedFrame';
                img.className = 'video-stream';
                img.alt = 'Video procesado';
                img.style.cssText = 'width: 100%; height: auto; display: block;';
                videoWrapper.appendChild(img);
                this.videoElement = img;
            }
        }
        
        console.log('[VPSCamera] videoElement:', this.videoElement?.id || 'NO ENCONTRADO');
    }
    
    /**
     * Inicia la captura de cámara del cliente
     * @returns {Promise<boolean>}
     */
    async start() {
        // Evitar múltiples inicios simultáneos
        if (this.isRunning) {
            console.log('[VPSCamera] Ya está corriendo, ignorando start()');
            return true;
        }
        
        if (this._starting) {
            console.log('[VPSCamera] Ya está iniciando, ignorando start()');
            return false;
        }
        
        this._starting = true;
        console.log('[VPSCamera] Iniciando captura de cámara del cliente...');
        
        try {
            // Primero detener cualquier stream existente
            this.stop();
            
            // Pausa más larga para liberar el dispositivo completamente
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Intentar con diferentes configuraciones de constraints
            const constraintsList = [
                // Primero: constraints específicos
                {
                    video: {
                        width: { ideal: this.options.width },
                        height: { ideal: this.options.height },
                        facingMode: 'user'
                    },
                    audio: false
                },
                // Segundo: constraints simples
                {
                    video: {
                        facingMode: 'user'
                    },
                    audio: false
                },
                // Tercero: lo más básico posible
                {
                    video: true,
                    audio: false
                }
            ];
            
            let stream = null;
            let lastError = null;
            
            for (const constraints of constraintsList) {
                try {
                    console.log('[VPSCamera] Intentando con constraints:', JSON.stringify(constraints));
                    stream = await navigator.mediaDevices.getUserMedia(constraints);
                    console.log('[VPSCamera] ✅ Constraints aceptados');
                    break;
                } catch (err) {
                    console.warn('[VPSCamera] Constraints rechazados:', err.message);
                    lastError = err;
                    // Esperar antes de intentar el siguiente
                    await new Promise(resolve => setTimeout(resolve, 200));
                }
            }
            
            if (!stream) {
                throw lastError || new Error('No se pudo obtener acceso a la cámara');
            }
            
            this.stream = stream;
            
            // Asignar stream al video de captura
            this.captureVideo.srcObject = this.stream;
            
            // Esperar a que el video esté listo
            await new Promise((resolve, reject) => {
                this.captureVideo.onloadedmetadata = () => {
                    console.log('[VPSCamera] Metadata del video cargada');
                    resolve();
                };
                this.captureVideo.onerror = (e) => {
                    reject(new Error('Error cargando video: ' + e.message));
                };
                // Timeout de seguridad
                setTimeout(() => resolve(), 3000);
            });
            
            await this.captureVideo.play();
            
            console.log('[VPSCamera] ✅ Cámara del cliente iniciada');
            console.log(`[VPSCamera] Resolución: ${this.captureVideo.videoWidth}x${this.captureVideo.videoHeight}`);
            
            // Actualizar dimensiones del canvas
            this.canvasElement.width = this.captureVideo.videoWidth || this.options.width;
            this.canvasElement.height = this.captureVideo.videoHeight || this.options.height;
            
            // Iniciar bucle de captura
            this.isRunning = true;
            this._starting = false;
            
            // Mostrar el primer frame inmediatamente
            this._showFirstFrame();
            
            this._captureLoop();
            
            // Ocultar overlay de error si existe
            this._hideCameraError();
            
            // Mostrar indicador de modo VPS
            this._showVPSIndicator();
            
            // Ocultar loading overlay
            const loadingOverlay = document.getElementById('loadingOverlay');
            if (loadingOverlay) loadingOverlay.style.display = 'none';
            
            return true;
            
        } catch (error) {
            console.error('[VPSCamera] ❌ Error al acceder a la cámara:', error);
            this._starting = false;
            this._showCameraError(error);
            return false;
        }
    }
    
    /**
     * Muestra el primer frame capturado inmediatamente
     */
    _showFirstFrame() {
        if (this.videoElement && this.captureVideo.videoWidth > 0) {
            // Dibujar en canvas
            this.canvasContext.drawImage(
                this.captureVideo, 
                0, 0, 
                this.canvasElement.width, 
                this.canvasElement.height
            );
            // Mostrar en elemento
            const frame = this.canvasElement.toDataURL('image/jpeg', this.options.quality);
            this.videoElement.src = frame;
            this.videoElement.style.display = 'block'; // Asegurar que sea visible
            console.log('[VPSCamera] Primer frame mostrado, src length:', frame.length);
            console.log('[VPSCamera] Video element display:', this.videoElement.style.display);
            console.log('[VPSCamera] Video element dimensions:', this.videoElement.width, 'x', this.videoElement.height);
        } else {
            console.error('[VPSCamera] No se puede mostrar frame:', {
                hasVideoElement: !!this.videoElement,
                videoWidth: this.captureVideo?.videoWidth,
                videoHeight: this.captureVideo?.videoHeight
            });
        }
    }
    
    /**
     * Detiene la captura
     */
    stop() {
        if (!this.stream && !this.isRunning) {
            return; // Nada que detener
        }
        console.log('[VPSCamera] Deteniendo captura...');
        this.isRunning = false;
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => {
                console.log('[VPSCamera] Deteniendo track:', track.kind);
                track.stop();
            });
            this.stream = null;
        }
        
        if (this.captureVideo) {
            this.captureVideo.srcObject = null;
        }
    }
    
    /**
     * Bucle de captura y envío de frames
     */
    async _captureLoop() {
        if (!this.isRunning) return;
        
        // Log inicial del bucle de captura
        if (this.frameCount === 0) {
            console.log('[VPSCamera] 🔄 Iniciando bucle de captura de frames...');
        }
        
        const now = performance.now();
        const elapsed = now - this.lastFrameTime;
        const frameInterval = 1000 / this.options.targetFPS;
        
        if (elapsed >= frameInterval && !this.processingFrame) {
            this.lastFrameTime = now;
            this.processingFrame = true;
            
            try {
                await this._processFrame();
            } catch (error) {
                console.error('[VPSCamera] Error procesando frame:', error);
            }
            
            this.processingFrame = false;
            this.frameCount++;
        }
        
        // Continuar el bucle
        requestAnimationFrame(() => this._captureLoop());
    }
    
    /**
     * Captura un frame, lo envía al servidor y muestra el resultado
     */
    async _processFrame() {
        // Dibujar frame actual en canvas
        this.canvasContext.drawImage(
            this.captureVideo, 
            0, 0, 
            this.canvasElement.width, 
            this.canvasElement.height
        );
        
        // Mostrar frame raw inmediatamente (mientras esperamos procesamiento)
        const rawFrame = this.canvasElement.toDataURL('image/jpeg', this.options.quality);
        
        // Si no hay frame procesado aún, mostrar el raw
        if (this.videoElement && !this._hasProcessedFrame) {
            this.videoElement.src = rawFrame;
        }
        
        // Enviar al servidor para procesamiento
        try {
            // Obtener exercise_type del controller si existe
            const exerciseType = window.liveAnalysisController?.currentExercise?.type || 'shoulder_profile';
            
            // Log solo cada 60 frames (cada ~6 segundos a 10fps)
            if (this.frameCount === 0) {
                console.log('[VPSCamera] 📤 Enviando PRIMER frame al servidor...');
            } else if (this.frameCount % 60 === 0) {
                console.log('[VPSCamera] 📤 Enviando frame', this.frameCount, 'para ejercicio:', exerciseType);
            }
            
            const response = await fetch(this.options.processEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    frame: rawFrame,
                    frame_number: this.frameCount,
                    exercise_type: exerciseType
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Log de éxito solo la primera vez
                if (!this._hasProcessedFrame) {
                    console.log('[VPSCamera] ✅ Primer frame procesado con MediaPipe recibido');
                    console.log('[VPSCamera] Análisis data:', data.analysis);
                }
                
                // Resetear contador de errores en caso de éxito
                this.consecutiveErrors = 0;
                
                // El API retorna 'frame' no 'processed_frame'
                if (data.success && data.frame) {
                    this._hasProcessedFrame = true;
                    // Mostrar frame procesado
                    if (this.videoElement) {
                        this.videoElement.src = data.frame;
                    }
                }
                
                // Actualizar datos de análisis si existen
                if (data.analysis) {
                    // Intentar actualizar via controller
                    if (window.liveAnalysisController && typeof window.liveAnalysisController.updateFromVPSData === 'function') {
                        window.liveAnalysisController.updateFromVPSData(data.analysis);
                    }
                    
                    // También actualizar UI directamente como respaldo
                    this._updateAnalysisUI(data.analysis);
                }
            } else {
                this.consecutiveErrors++;
                
                // Si el servidor falla, mostrar frame raw
                if (this.videoElement) {
                    this.videoElement.src = rawFrame;
                }
                
                // Log error ocasionalmente
                if (this.frameCount % 30 === 0 || this.consecutiveErrors === 1) {
                    console.error(`[VPSCamera] ❌ Server error ${response.status} (${this.consecutiveErrors} consecutivos)`);
                    // Intentar leer el mensaje de error
                    response.text().then(text => {
                        console.error('[VPSCamera] Error response:', text.substring(0, 500));
                    }).catch(() => {});
                }
                
                // Si hay muchos errores consecutivos, intentar reiniciar
                if (this.consecutiveErrors >= this.maxConsecutiveErrors) {
                    console.warn('[VPSCamera] Demasiados errores consecutivos, modo solo cámara activado');
                    // Continuar mostrando cámara sin procesar
                }
            }
        } catch (error) {
            this.consecutiveErrors++;
            
            // Si hay error de red, mostrar frame raw
            if (this.videoElement) {
                this.videoElement.src = rawFrame;
            }
            // Solo loguear errores ocasionalmente para no saturar la consola
            if (this.frameCount % 30 === 0 || this.consecutiveErrors === 1) {
                console.error(`[VPSCamera] ❌ Error enviando frame (${this.consecutiveErrors} consecutivos):`, error.message);
            }
        }
    }
    
    /**
     * Muestra indicador de modo VPS
     */
    _showVPSIndicator() {
        let indicator = document.getElementById('vpsModeIndicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'vpsModeIndicator';
            indicator.innerHTML = `
                <i class="bi bi-cloud-check"></i>
                <span>Modo VPS - Cámara del navegador</span>
            `;
            indicator.style.cssText = `
                position: fixed;
                top: 10px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(40, 167, 69, 0.9);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                z-index: 10001;
                display: flex;
                align-items: center;
                gap: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            `;
            document.body.appendChild(indicator);
            
            // Auto-ocultar después de 5 segundos
            setTimeout(() => {
                indicator.style.transition = 'opacity 0.5s';
                indicator.style.opacity = '0';
                setTimeout(() => indicator.remove(), 500);
            }, 5000);
        }
    }
    
    /**
     * Actualiza la UI de análisis directamente desde los datos del servidor
     * Esta es una actualización directa como respaldo al controller
     */
    _updateAnalysisUI(analysis) {
        try {
            // Actualizar ángulo actual
            const angleElement = document.getElementById('currentAngle');
            if (angleElement && analysis.angle !== undefined) {
                angleElement.textContent = `${analysis.angle.toFixed(1)}°`;
            }
            
            // Actualizar min/max
            const minAngleElement = document.getElementById('minAngle');
            if (minAngleElement && analysis.min_angle !== undefined) {
                minAngleElement.textContent = `${analysis.min_angle.toFixed(1)}°`;
            }
            
            const maxAngleElement = document.getElementById('maxAngle');
            if (maxAngleElement && analysis.max_angle !== undefined) {
                maxAngleElement.textContent = `${analysis.max_angle.toFixed(1)}°`;
            }
            
            // Actualizar ROM
            const romElement = document.getElementById('romValue') || document.getElementById('currentROM');
            if (romElement && analysis.rom !== undefined) {
                romElement.textContent = `${analysis.rom.toFixed(1)}°`;
            }
            
            // Actualizar indicador de detección
            const detectionBadge = document.getElementById('detectionStatus');
            if (detectionBadge) {
                if (analysis.landmarks_detected) {
                    detectionBadge.className = 'badge bg-success';
                    detectionBadge.textContent = 'Persona detectada';
                } else {
                    detectionBadge.className = 'badge bg-warning';
                    detectionBadge.textContent = 'Buscando...';
                }
            }
            
            // Actualizar barra de progreso visual si existe
            const progressBar = document.getElementById('romProgressBar');
            if (progressBar && analysis.angle !== undefined) {
                // Normalizar el ángulo a un porcentaje (0-180 grados)
                const percentage = Math.min(100, (analysis.angle / 180) * 100);
                progressBar.style.width = `${percentage}%`;
                progressBar.setAttribute('aria-valuenow', percentage);
            }
            
        } catch (error) {
            // No es crítico si falla la actualización UI
            console.warn('[VPSCamera] Error actualizando UI:', error);
        }
    }
    
    /**
     * Muestra error de cámara
     */
    _showCameraError(error) {
        let errorMsg = 'No se pudo acceder a la cámara.';
        
        if (error.name === 'NotAllowedError') {
            errorMsg = 'Permiso de cámara denegado. Por favor, permite el acceso a la cámara en tu navegador.';
        } else if (error.name === 'NotFoundError') {
            errorMsg = 'No se encontró ninguna cámara. Asegúrate de que tu dispositivo tiene una cámara conectada.';
        } else if (error.name === 'NotReadableError') {
            errorMsg = 'La cámara está siendo usada por otra aplicación.';
        }
        
        // Mostrar en el elemento de video
        if (this.videoElement) {
            const parent = this.videoElement.parentElement;
            if (parent) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'camera-error-overlay';
                errorDiv.innerHTML = `
                    <div class="error-content">
                        <i class="bi bi-camera-video-off" style="font-size: 3rem; color: #dc3545;"></i>
                        <h5 class="mt-3">Error de Cámara</h5>
                        <p>${errorMsg}</p>
                        <button class="btn btn-primary mt-2" onclick="window.vpsCameraHandler?.start()">
                            <i class="bi bi-arrow-clockwise me-2"></i>Reintentar
                        </button>
                    </div>
                `;
                errorDiv.style.cssText = `
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.9);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                    color: white;
                    z-index: 100;
                `;
                parent.style.position = 'relative';
                
                // Remover error anterior si existe
                const existingError = parent.querySelector('.camera-error-overlay');
                if (existingError) existingError.remove();
                
                parent.appendChild(errorDiv);
            }
        }
        
        // Ocultar loading overlay
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) loadingOverlay.style.display = 'none';
        
        // También mostrar toast
        if (typeof showToast === 'function') {
            showToast(errorMsg, 'error');
        }
    }
    
    /**
     * Oculta el error de cámara
     */
    _hideCameraError() {
        if (this.videoElement) {
            const parent = this.videoElement.parentElement;
            if (parent) {
                const errorDiv = parent.querySelector('.camera-error-overlay');
                if (errorDiv) errorDiv.remove();
            }
        }
    }
    
    /**
     * Lista las cámaras disponibles
     * @returns {Promise<Array>}
     */
    static async listCameras() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            return devices.filter(device => device.kind === 'videoinput').map((device, index) => ({
                index: index,
                deviceId: device.deviceId,
                label: device.label || `Cámara ${index + 1}`,
                groupId: device.groupId
            }));
        } catch (error) {
            console.error('[VPSCamera] Error listando cámaras:', error);
            return [];
        }
    }
}

// Instancia global
window.vpsCameraHandler = null;
window.vpsCameraInitializing = false;  // Flag para evitar inicialización doble

/**
 * Inicializa el handler de cámara VPS si estamos en modo VPS
 */
async function initVPSCameraIfNeeded() {
    // Evitar inicialización doble
    if (window.vpsCameraHandler || window.vpsCameraInitializing) {
        console.log('[VPSCamera] Ya inicializado o en proceso, saltando...');
        return;
    }
    
    window.vpsCameraInitializing = true;
    
    try {
        // Verificar si estamos en modo VPS
        const response = await fetch('/api/camera/mode');
        const data = await response.json();
        
        if (data.success && data.mode === 'vps') {
            console.log('[VPSCamera] 🌐 Modo VPS detectado - Iniciando cámara del cliente');
            
            // Ocultar el img del video feed del servidor
            const videoFeed = document.getElementById('videoFeed');
            if (videoFeed) {
                videoFeed.style.display = 'none';
                
                // Crear elemento img para frames procesados si no existe
                if (!document.getElementById('processedFrame')) {
                    const processedImg = document.createElement('img');
                    processedImg.id = 'processedFrame';
                    processedImg.className = 'video-stream';
                    // Copiar estilos pero asegurar que sea visible
                    processedImg.style.cssText = videoFeed.style.cssText;
                    processedImg.style.display = 'block'; // Forzar visible
                    processedImg.style.width = '100%';
                    processedImg.style.height = 'auto';
                    processedImg.style.objectFit = 'contain';
                    processedImg.style.backgroundColor = '#000';
                    processedImg.alt = 'Video procesado';
                    console.log('[VPSCamera] Creando elemento processedFrame con display:', processedImg.style.display);
                    videoFeed.parentElement.appendChild(processedImg);
                }
            }
            
            // Crear e iniciar handler
            window.vpsCameraHandler = new VPSCameraHandler({
                videoElementId: 'processedFrame',
                targetFPS: data.settings?.processing_fps || 10,
                quality: (data.settings?.jpeg_quality || 50) / 100,
                width: data.settings?.processing_width || 640,
                height: data.settings?.processing_height || 480
            });
            
            await window.vpsCameraHandler.start();
        } else {
            console.log('[VPSCamera] 💻 Modo LocalHost - Usando video feed del servidor');
        }
    } catch (error) {
        console.warn('[VPSCamera] Error verificando modo:', error);
    } finally {
        window.vpsCameraInitializing = false;
    }
}

// NO auto-inicializar - live_analysis.js maneja la inicialización
// Esto evita doble inicialización y errores "Device in use"
// La función initVPSCameraIfNeeded() es llamada desde live_analysis.js cuando es necesario
