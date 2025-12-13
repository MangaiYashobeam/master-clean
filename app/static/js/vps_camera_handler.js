/**
 * 🌐 VPS CAMERA HANDLER - Manejo de cámara del cliente para modo VPS
 * ===================================================================
 * Captura video de la cámara del navegador y lo envía al servidor para
 * procesamiento con MediaPipe.
 * 
 * FLUJO:
 * 1. getUserMedia() obtiene stream de la cámara del cliente
 * 2. Canvas captura frames del video
 * 3. Frames se envían al servidor via WebSocket o HTTP POST
 * 4. Servidor procesa con MediaPipe y retorna frame procesado
 * 5. Frame procesado se muestra en el cliente
 * 
 * Autor: BIOTRACK Team
 * Fecha: 2025-12-13
 */

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
        this.videoElement = document.getElementById(this.options.videoElementId);
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
            const response = await fetch(this.options.processEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    frame: rawFrame,
                    frame_number: this.frameCount
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // El API retorna 'frame' no 'processed_frame'
                if (data.success && data.frame) {
                    this._hasProcessedFrame = true;
                    // Mostrar frame procesado
                    if (this.videoElement) {
                        this.videoElement.src = data.frame;
                    }
                }
                
                // Actualizar datos de análisis si existen
                if (data.analysis && window.liveAnalysisController) {
                    window.liveAnalysisController.updateFromVPSData(data.analysis);
                }
            } else {
                // Si el servidor falla, mostrar frame raw
                if (this.videoElement) {
                    this.videoElement.src = rawFrame;
                }
                // Log error ocasionalmente
                if (this.frameCount % 30 === 0) {
                    console.warn(`[VPSCamera] Server error ${response.status}`);
                }
            }
        } catch (error) {
            // Si hay error de red, mostrar frame raw
            if (this.videoElement) {
                this.videoElement.src = rawFrame;
            }
            // Solo loguear errores ocasionalmente para no saturar la consola
            if (this.frameCount % 30 === 0) {
                console.warn('[VPSCamera] Error enviando frame:', error.message);
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
                    processedImg.style.cssText = videoFeed.style.cssText;
                    processedImg.alt = 'Video procesado';
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
