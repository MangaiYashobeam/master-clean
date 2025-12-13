/**
 * 🎯 LIVE ANALYSIS CONTROLLER - Control del Análisis en Vivo
 * ===========================================================
 * Controla la interfaz de análisis en tiempo real
 * 
 * RESPONSABILIDADES:
 * - Polling de datos del analyzer cada 500ms
 * - Actualización de métricas en UI
 * - Control de sesión con estados (DETECTING → ORIENTATION → POSTURE → COUNTDOWN → ANALYZING)
 * - Gráfico de ROM en tiempo real
 * - Modal de resultados
 * 
 * Autor: BIOTRACK Team
 * Fecha: 2025-11-26
 * Versión: 3.0 - Con flujo de estados
 */

class LiveAnalysisController {
    constructor(config) {
        this.config = config;
        this.isActive = false;
        this.pollingInterval = null;
        this.sessionPollingInterval = null;
        this.romChart = null;
        this.dataPoints = [];
        this.maxDataPoints = 50;
        
        // Estado de la sesión con estados
        this.sessionState = 'IDLE';
        this.useNewFlow = true; // Usar nuevo flujo con estados
        
        // 📊 Guardar último resultado para historial
        this.lastFinalData = null;
        
        // 📍 Guardar el lado detectado en TIEMPO REAL (del polling)
        // Este es el que se muestra en "Datos en Tiempo Real" y debe usarse para guardar
        this.lastDetectedSide = null;
        
        // 🛡️ Flag para evitar doble guardado
        this.isSaving = false;
        
        // 🎯 DATOS DE SUJETO (si es análisis de sujeto en vez de auto-análisis)
        // Se obtiene del data-attribute del video feed
        const videoFeed = document.getElementById('videoFeed');
        this.analysisSubjectId = videoFeed?.dataset?.subjectId ? parseInt(videoFeed.dataset.subjectId) : null;
        this.analysisSubjectName = videoFeed?.dataset?.subjectName || null;
        
        // Log para debug
        if (this.analysisSubjectId) {
            console.log(`[LiveAnalysis] 🎯 MODO ANÁLISIS DE SUJETO: ${this.analysisSubjectName} (ID: ${this.analysisSubjectId})`);
        } else {
            console.log('[LiveAnalysis] 👤 MODO AUTO-ANÁLISIS (historial personal)');
        }
        
        // 🦵 ANÁLISIS BILATERAL SECUENCIAL (hip abduction)
        this.isSequentialBilateral = false;    // Modo bilateral secuencial activo
        this.sequentialFirstLeg = null;        // Primera pierna seleccionada ('left' o 'right')
        this.sequentialSecondLeg = null;       // Segunda pierna (calculada)
        this.sequentialCurrentLeg = null;      // Pierna en análisis actual
        this.sequentialPhase = 0;              // 0=no iniciado, 1=primera pierna, 2=segunda pierna
        this.sequentialFirstResult = null;     // Resultado de primera pierna
        this.sequentialSecondResult = null;    // Resultado de segunda pierna
        
        // Inicializar
        this.init();
    }
    
    /**
     * Inicialización del controller
     */
    init() {
        console.log('[LiveAnalysis] Inicializando con config:', this.config);
        
        // Crear overlay de pantalla completa
        createFullscreenOverlay();
        
        // Crear overlay de estado (para el nuevo flujo)
        this.createStateOverlay();
        
        // Inicializar gráfico de ROM
        this.initROMChart();
        
        // Event listeners
        this.setupEventListeners();
        
        // Ocultar overlay cuando el video stream empiece a funcionar
        setTimeout(() => {
            const overlay = document.getElementById('loadingOverlay');
            if (overlay) {
                overlay.style.display = 'none';
            }
        }, 3000);
        
        // ⚡ INICIAR POLLING AUTOMÁTICAMENTE
        this.startDataPolling();
        
        // 📊 Cargar historial reciente al iniciar
        this.loadRecentHistory();
        
        console.log('[LiveAnalysis] Inicialización completa - Polling automático activo');
    }
    
    /**
     * Crea el overlay para mostrar estados del análisis
     */
    createStateOverlay() {
        const videoWrapper = document.getElementById('videoWrapper');
        if (!videoWrapper) return;
        
        // Verificar si ya existe
        if (document.getElementById('stateOverlay')) return;
        
        const overlay = document.createElement('div');
        overlay.id = 'stateOverlay';
        overlay.className = 'state-overlay hidden';
        overlay.innerHTML = `
            <div class="state-content">
                <div class="state-icon">
                    <i class="bi bi-hourglass-split"></i>
                </div>
                <h3 class="state-title">Preparando...</h3>
                <p class="state-message">Por favor espere</p>
                <div class="state-progress">
                    <div class="state-progress-bar"></div>
                </div>
                <div class="countdown-display hidden">
                    <span class="countdown-number">3</span>
                </div>
            </div>
        `;
        
        // Agregar estilos inline para el overlay
        // Inicia OPACO (0.85), se hace semi-transparente (0.40) solo durante ANALYZING
        overlay.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 100;
            color: white;
            text-align: center;
        `;
        
        videoWrapper.appendChild(overlay);
        
        // Agregar estilos CSS
        this.addStateStyles();
    }
    
    /**
     * Agrega estilos CSS para el overlay de estados
     */
    addStateStyles() {
        if (document.getElementById('stateOverlayStyles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'stateOverlayStyles';
        styles.textContent = `
            .state-overlay.hidden {
                display: none !important;
            }
            .state-content {
                padding: 30px;
            }
            .state-icon {
                font-size: 4rem;
                margin-bottom: 20px;
                animation: pulse 1.5s infinite;
            }
            .state-icon.success { color: #4CAF50; }
            .state-icon.warning { color: #FFC107; }
            .state-icon.info { color: #2196F3; }
            .state-icon.countdown { color: #00d4ff; font-size: 6rem; }
            
            .state-title {
                font-size: 1.5rem;
                font-weight: 600;
                margin-bottom: 10px;
            }
            .state-message {
                font-size: 1rem;
                color: #ccc;
                margin-bottom: 20px;
            }
            .state-progress {
                width: 200px;
                height: 6px;
                background: rgba(255,255,255,0.2);
                border-radius: 3px;
                margin: 0 auto;
                overflow: hidden;
            }
            .state-progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #667eea, #764ba2);
                width: 0%;
                transition: width 0.3s ease;
            }
            .countdown-display {
                margin-top: 20px;
            }
            .countdown-display.hidden {
                display: none;
            }
            .countdown-number {
                font-size: 5rem;
                font-weight: 700;
                color: #00d4ff;
                text-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
                animation: countdownPulse 1s ease-in-out;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.7; transform: scale(1.05); }
            }
            @keyframes countdownPulse {
                0% { transform: scale(1.5); opacity: 0; }
                50% { transform: scale(1); opacity: 1; }
                100% { transform: scale(0.9); opacity: 0.8; }
            }
        `;
        document.head.appendChild(styles);
    }
    
    /**
     * Configurar event listeners
     */
    setupEventListeners() {
        // Detectar cuando se cierra la ventana/tab
        window.addEventListener('beforeunload', (e) => {
            if (this.isActive || this.isSequentialBilateral) {
                // Usar sendBeacon para request síncrono que funciona en beforeunload
                // Esto asegura que la sesión se limpie incluso al cerrar el navegador
                navigator.sendBeacon('/api/camera/release', '');
                
                // También intentar stopAnalysis (aunque es async y puede no completar)
                this.stopAnalysis(false); // Sin mostrar modal
                
                // Mensaje de confirmación (algunos navegadores lo ignoran)
                e.preventDefault();
                e.returnValue = '';
            }
        });
    }
    
    /**
     * Inicializa el gráfico de ROM con Chart.js
     */
    initROMChart() {
        const ctx = document.getElementById('romChart');
        if (!ctx) {
            console.warn('[LiveAnalysis] Canvas romChart no encontrado');
            return;
        }
        
        this.romChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Ángulo (°)',
                    data: [],
                    borderColor: 'rgba(102, 126, 234, 1)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 2,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: this.config.max_angle,
                        ticks: {
                            callback: function(value) {
                                return value + '°';
                            }
                        }
                    },
                    x: {
                        display: false // Ocultar eje X para simplificar
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y.toFixed(1) + '°';
                            }
                        }
                    }
                },
                animation: {
                    duration: 0 // Sin animación para actualización fluida
                }
            }
        });
        
        console.log('[LiveAnalysis] Gráfico ROM inicializado');
    }
    
    /**
     * Inicia la sesión oficial de análisis
     * Usa el nuevo flujo con estados: DETECTING → ORIENTATION → POSTURE → COUNTDOWN → ANALYZING
     * 
     * NOTA: Para hip_abduction, primero muestra modal de selección de pierna
     */
    async startAnalysis() {
        console.log('[LiveAnalysis] Iniciando sesión con flujo de estados...');
        
        // 🦵 CHECK: ¿Es hip_abduction? → Mostrar modal de selección de pierna
        const exerciseId = `${this.config.segment_type}_${this.config.exercise_key}`;
        
        if (exerciseId === 'hip_abduction') {
            console.log('[LiveAnalysis] Hip abduction detectado - Mostrando modal de selección de pierna');
            this.showLegSelectionModal();
            return;  // El flujo continúa cuando el usuario seleccione la pierna
        }
        
        // Para otros ejercicios, continuar con flujo normal
        await this.startAnalysisWithLeg(null);
    }
    
    /**
     * Muestra el modal de selección de pierna para hip abduction
     */
    showLegSelectionModal() {
        // Resetear estado bilateral
        this.isSequentialBilateral = true;
        this.sequentialPhase = 0;
        this.sequentialFirstLeg = null;
        this.sequentialSecondLeg = null;
        this.sequentialFirstResult = null;
        this.sequentialSecondResult = null;
        
        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('legSelectionModal'));
        modal.show();
    }
    
    /**
     * Inicia el análisis con la pierna seleccionada (o null para análisis normal)
     */
    async startAnalysisWithLeg(selectedLeg) {
        console.log('[LiveAnalysis] Iniciando análisis con pierna:', selectedLeg || 'ambas/no aplica');
        
        // Determinar si debemos suprimir el TTS del backend
        // En modo bilateral secuencial, SIEMPRE suprimir TTS del backend (para ambas piernas)
        // El frontend llamará al TTS solo cuando tenga el resultado combinado final
        const shouldSuppressTTS = this.isSequentialBilateral;
        console.log('[LiveAnalysis] shouldSuppressTTS:', shouldSuppressTTS, 'isSequentialBilateral:', this.isSequentialBilateral);
        
        try {
            // 1º RESETEAR ROM para empezar desde cero
            const resetResponse = await fetch('/api/analysis/reset', {
                method: 'POST'
            });
            
            if (!resetResponse.ok) {
                console.warn('[LiveAnalysis] No se pudo resetear ROM, continuando...');
            }
            
            // 2º CONFIGURAR PIERNA EN EL ANALYZER (solo para hip abduction)
            if (selectedLeg) {
                const legResponse = await fetch('/api/session/set_leg', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        leg: selectedLeg,
                        suppress_tts: shouldSuppressTTS
                    })
                });
                
                if (!legResponse.ok) {
                    console.warn('[LiveAnalysis] No se pudo configurar pierna, continuando...');
                }
            }
            
            // 3º INICIAR SESIÓN CON ESTADOS
            const exerciseId = `${this.config.segment_type}_${this.config.exercise_key}`;
            
            const response = await fetch('/api/session/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    exercise_id: exerciseId,
                    selected_leg: selectedLeg,
                    suppress_tts_result: shouldSuppressTTS  // Suprimir TTS en primera pierna
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.isActive = true;
                this.sessionState = data.session.state;
                
                // Actualizar UI
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                
                // Mostrar overlay de estado
                this.showStateOverlay(data.session.state, data.session.message);
                
                // Iniciar polling de estado de sesión
                this.startSessionPolling();
                
                // Sincronizar botones de pantalla completa
                if (typeof isFullscreenMode !== 'undefined' && isFullscreenMode) {
                    syncButtonStates();
                }
                
                console.log('[LiveAnalysis] Sesión iniciada - Estado:', data.session.state);
            } else {
                throw new Error(data.error || 'Error al iniciar sesión');
            }
        } catch (error) {
            console.error('[LiveAnalysis] Error al iniciar sesión:', error);
            alert('Error al iniciar la sesión: ' + error.message);
        }
    }
    
    /**
     * Inicia el polling del estado de la sesión
     */
    startSessionPolling() {
        if (this.sessionPollingInterval) {
            clearInterval(this.sessionPollingInterval);
        }
        
        this.sessionPollingInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/session/status');
                const data = await response.json();
                
                if (data.success && data.session) {
                    this.handleSessionState(data.session);
                } else if (!data.session) {
                    // Sesión terminada
                    this.stopSessionPolling();
                    this.hideStateOverlay();
                }
            } catch (error) {
                console.error('[LiveAnalysis] Error en session polling:', error);
            }
        }, 300); // Polling más frecuente para estados (300ms)
    }
    
    /**
     * Detiene el polling del estado de sesión
     */
    stopSessionPolling() {
        if (this.sessionPollingInterval) {
            clearInterval(this.sessionPollingInterval);
            this.sessionPollingInterval = null;
        }
    }
    
    /**
     * Maneja los cambios de estado de la sesión
     */
    handleSessionState(session) {
        const prevState = this.sessionState;
        this.sessionState = session.state;
        
        // Configuración de cada estado
        const stateConfig = {
            'DETECTING_PERSON': {
                icon: 'bi-person-bounding-box',
                iconClass: 'info',
                title: 'Buscando Persona',
                showProgress: true
            },
            'CHECKING_ORIENTATION': {
                icon: 'bi-arrows-angle-expand',
                iconClass: 'warning',
                title: 'Verificando Orientación',
                showProgress: true
            },
            'CHECKING_POSTURE': {
                icon: 'bi-person-check',
                iconClass: 'warning',
                title: 'Verificando Postura',
                showProgress: true
            },
            'COUNTDOWN': {
                icon: 'bi-stopwatch',
                iconClass: 'countdown',
                title: 'Prepárate',
                showCountdown: true
            },
            'ANALYZING': {
                icon: 'bi-activity',
                iconClass: 'success',
                title: 'Analizando',
                showProgress: true
            },
            'COMPLETED': {
                icon: 'bi-check-circle',
                iconClass: 'success',
                title: '¡Completado!',
                autoHide: true
            }
        };
        
        const config = stateConfig[session.state];
        
        if (config) {
            this.updateStateOverlay(
                config.icon,
                config.iconClass,
                config.title,
                session.message,
                session.progress,
                config.showCountdown ? session.countdown : null
            );
            
            // Estado COMPLETED - mostrar resultados
            if (session.state === 'COMPLETED') {
                console.log('[LiveAnalysis] Estado COMPLETED recibido, resultado:', session.result);
                
                // IMPORTANTE: Detener polling INMEDIATAMENTE para evitar que vuelva a mostrar overlay
                this.stopSessionPolling();
                
                setTimeout(() => {
                    // Ocultar overlay y limpiar estado
                    this.hideStateOverlay();
                    this.isActive = false;
                    
                    // Actualizar botones
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                    
                    // Sincronizar botones de pantalla completa
                    if (typeof syncButtonStates === 'function') {
                        syncButtonStates();
                    }
                    
                    // 🦵 MANEJO DE ANÁLISIS BILATERAL SECUENCIAL
                    if (this.isSequentialBilateral && session.result) {
                        this.handleSequentialBilateralCompletion(session.result);
                        return;
                    }
                    
                    // Mostrar resultados si hay (flujo normal)
                    if (session.result) {
                        this.showResults(session.result);
                    } else {
                        // Si no hay resultado, mostrar mensaje informativo
                        console.warn('[LiveAnalysis] Análisis completado sin resultado válido');
                        alert('El análisis se completó pero no se pudo calcular un ROM válido. Intente de nuevo manteniendo la posición correcta durante todo el análisis.');
                    }
                }, 1000);
                
                // Salir temprano para no seguir procesando
                return;
            }
            
            // Estado ERROR
            if (session.state === 'ERROR') {
                // Detener polling INMEDIATAMENTE
                this.stopSessionPolling();
                
                setTimeout(() => {
                    this.hideStateOverlay();
                    this.isActive = false;
                    
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                    
                    // Sincronizar botones de pantalla completa
                    if (typeof syncButtonStates === 'function') {
                        syncButtonStates();
                    }
                    
                    alert('Error en el análisis: ' + session.message);
                }, 500);
                
                return;
            }
        }
    }
    
    /**
     * Muestra el overlay de estado
     */
    showStateOverlay(state, message) {
        const overlay = document.getElementById('stateOverlay');
        if (overlay) {
            overlay.classList.remove('hidden');
            this.updateStateOverlay('bi-hourglass-split', 'info', 'Iniciando...', message, 0);
        }
    }
    
    /**
     * Actualiza el overlay de estado
     */
    updateStateOverlay(icon, iconClass, title, message, progress, countdown = null) {
        const overlay = document.getElementById('stateOverlay');
        if (!overlay) return;
        
        const iconEl = overlay.querySelector('.state-icon');
        const titleEl = overlay.querySelector('.state-title');
        const messageEl = overlay.querySelector('.state-message');
        const progressBar = overlay.querySelector('.state-progress-bar');
        const countdownDisplay = overlay.querySelector('.countdown-display');
        const countdownNumber = overlay.querySelector('.countdown-number');
        
        if (iconEl) {
            iconEl.innerHTML = `<i class="bi ${icon}"></i>`;
            iconEl.className = 'state-icon ' + iconClass;
        }
        if (titleEl) titleEl.textContent = title;
        if (messageEl) messageEl.textContent = message;
        if (progressBar) progressBar.style.width = `${(progress || 0) * 100}%`;
        
        // 🎨 OPACIDAD DINÁMICA: Semi-transparente SOLO durante ANALYZING
        // Fases preparatorias: opaco (0.85) para enfocar atención
        // Fase ANALYZING: semi-transparente (0.40) para ver el video
        if (title === 'Analizando') {
            overlay.style.background = 'rgba(0, 0, 0, 0.40)';
        } else {
            overlay.style.background = 'rgba(0, 0, 0, 0.85)';
        }
        
        // Mostrar countdown si aplica
        if (countdown !== null && countdownDisplay && countdownNumber) {
            countdownDisplay.classList.remove('hidden');
            countdownNumber.textContent = countdown;
        } else if (countdownDisplay) {
            countdownDisplay.classList.add('hidden');
        }
    }
    
    /**
     * Oculta el overlay de estado
     */
    hideStateOverlay() {
        const overlay = document.getElementById('stateOverlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }
    
    /**
     * Detiene la sesión oficial de análisis
     * Usa el nuevo endpoint de sesión con estados
     */
    async stopAnalysis(showModal = true) {
        console.log('[LiveAnalysis] Deteniendo sesión...');
        
        try {
            // Detener polling de sesión primero
            this.stopSessionPolling();
            this.hideStateOverlay();
            
            // Llamar al nuevo endpoint de sesión
            const response = await fetch('/api/session/stop', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.isActive = false;
                this.sessionState = 'IDLE';
                
                // Actualizar UI
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                
                // Sincronizar botones de pantalla completa
                if (typeof isFullscreenMode !== 'undefined' && isFullscreenMode) {
                    syncButtonStates();
                }
                
                // Mostrar modal de resultados si hay resultado
                if (showModal && data.result && data.result.result) {
                    this.showResults(data.result.result);
                } else if (showModal) {
                    // Fallback: obtener datos actuales del analyzer
                    const currentData = await fetch('/api/analysis/current_data');
                    const currentDataJson = await currentData.json();
                    if (currentDataJson.success) {
                        this.showResults(currentDataJson.data);
                    }
                }
                
                console.log('[LiveAnalysis] Sesión detenida');
            } else {
                throw new Error(data.error || 'Error al detener sesión');
            }
        } catch (error) {
            console.error('[LiveAnalysis] Error al detener sesión:', error);
            
            // Fallback: detener con endpoint antiguo
            try {
                await fetch('/api/analysis/stop', { method: 'POST' });
            } catch (e) {}
            
            this.isActive = false;
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            
            // Sincronizar botones de pantalla completa
            if (typeof syncButtonStates === 'function') {
                syncButtonStates();
            }
        }
    }
    
    /**
     * Reinicia el ROM máximo
     */
    async resetROM() {
        console.log('[LiveAnalysis] Reiniciando ROM...');
        
        if (!confirm('¿Estás seguro de reiniciar el ROM máximo?')) {
            return;
        }
        
        try {
            const response = await fetch('/api/analysis/reset', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // Limpiar gráfico
                this.dataPoints = [];
                if (this.romChart) {
                    this.romChart.data.labels = [];
                    this.romChart.data.datasets[0].data = [];
                    this.romChart.update();
                }
                
                // Resetear métricas
                document.getElementById('maxROM').textContent = '0°';
                
                console.log('[LiveAnalysis] ROM reiniciado exitosamente');
            } else {
                throw new Error(data.error || 'Error al reiniciar ROM');
            }
        } catch (error) {
            console.error('[LiveAnalysis] Error al reiniciar ROM:', error);
            alert('Error al reiniciar ROM: ' + error.message);
        }
    }
    
    /**
     * Inicia el polling de datos cada 500ms
     * NOTA: El polling corre SIEMPRE (no depende de isActive)
     */
    startDataPolling() {
        console.log('[LiveAnalysis] Iniciando polling de datos...');
        
        // Evitar múltiples intervalos
        if (this.pollingInterval) {
            return;
        }
        
        this.pollingInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/analysis/current_data');
                const data = await response.json();
                
                if (response.ok && data.success) {
                    this.updateUI(data.data);
                }
            } catch (error) {
                // Solo loguear errores reales, no en cada polling
            }
        }, 500); // Actualizar cada 500ms (2 veces por segundo es suficiente)
        
        console.log('[LiveAnalysis] Polling configurado - actualizando cada 500ms');
    }
    
    /**
     * Detiene el polling de datos
     */
    stopDataPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
            console.log('[LiveAnalysis] Polling detenido');
        }
    }
    
    /**
     * Actualiza la UI con los datos actuales
     */
    updateUI(data) {
        // 📍 Guardar el lado detectado en tiempo real para usarlo al guardar
        if (data.side && data.side !== 'Detectando...' && data.side !== 'none') {
            this.lastDetectedSide = data.side;
        }
        
        // Mapear lado a etiqueta corta
        const sideLabels = {
            'left': 'IZQ',
            'right': 'DER',
            'izquierdo': 'IZQ',
            'derecho': 'DER',
            'Detectando...': '...',
            'none': '---'
        };
        const sideLabel = sideLabels[data.side] || '---';
        
        // Actualizar ángulo actual CON LADO
        const angleElement = document.getElementById('currentAngle');
        if (angleElement && data.angle !== undefined) {
            const angleAbs = Math.abs(data.angle).toFixed(1);
            angleElement.textContent = `${angleAbs}° (${sideLabel})`;
        }
        
        // Actualizar ROM máximo
        const romElement = document.getElementById('maxROM');
        if (romElement && data.max_rom !== undefined) {
            romElement.textContent = `${data.max_rom.toFixed(1)}°`;
        }
        
        // Para análisis frontal bilateral
        if (data.left_angle !== undefined && data.right_angle !== undefined) {
            angleElement.textContent = `Izq: ${data.left_angle.toFixed(1)}° | Der: ${data.right_angle.toFixed(1)}°`;
            // Usar max_left_angle y max_right_angle (nombres del backend)
            const leftMax = data.max_left_angle || data.left_max_rom || 0;
            const rightMax = data.max_right_angle || data.right_max_rom || 0;
            romElement.textContent = `Izq: ${leftMax.toFixed(1)}° | Der: ${rightMax.toFixed(1)}°`;
        }
        
        // Actualizar estado de postura
        const postureElement = document.getElementById('postureStatus');
        if (postureElement && data.posture_valid !== undefined) {
            if (data.posture_valid) {
                postureElement.innerHTML = `
                    <i class="bi bi-check-circle-fill"></i>
                    <span>Postura Correcta</span>
                `;
                postureElement.classList.add('valid');
                postureElement.classList.remove('invalid');
            } else {
                postureElement.innerHTML = `
                    <i class="bi bi-exclamation-triangle-fill"></i>
                    <span>Ajusta tu postura</span>
                `;
                postureElement.classList.add('invalid');
                postureElement.classList.remove('valid');
            }
        }
        
        // Actualizar FPS
        const fpsElement = document.getElementById('fpsDisplay');
        if (fpsElement && data.fps !== undefined) {
            fpsElement.textContent = `${data.fps} FPS`;
        }
        
        // Actualizar gráfico
        if (this.romChart) {
            const angleValue = Math.abs(data.angle || data.left_angle || 0);
            this.updateChart(angleValue);
        }
        
        // Si estamos en modo pantalla completa, actualizar también esas métricas
        if (isFullscreenMode) {
            updateFullscreenMetrics();
        }
    }
    
    /**
     * Actualiza el gráfico de ROM
     */
    updateChart(angle) {
        if (!this.romChart) return;
        
        const now = new Date();
        const timeLabel = now.toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
        
        // Agregar dato
        this.romChart.data.labels.push(timeLabel);
        this.romChart.data.datasets[0].data.push(angle);
        
        // Mantener solo los últimos N puntos
        if (this.romChart.data.labels.length > this.maxDataPoints) {
            this.romChart.data.labels.shift();
            this.romChart.data.datasets[0].data.shift();
        }
        
        // Actualizar sin animación
        this.romChart.update('none');
    }
    
    /**
     * Muestra el modal de resultados
     */
    showResults(finalData) {
        if (!finalData) {
            console.warn('[LiveAnalysis] No hay datos finales para mostrar');
            return;
        }
        
        console.log('[LiveAnalysis] Mostrando resultados:', finalData);
        
        // 📊 Guardar datos finales para poder guardar en historial
        this.lastFinalData = finalData;
        
        // Verificar si es análisis bilateral (frontal)
        const isBilateral = finalData.is_bilateral === true;
        
        const unilateralResult = document.getElementById('unilateralResult');
        const bilateralResult = document.getElementById('bilateralResult');
        
        if (isBilateral && finalData.left_max_rom !== null && finalData.right_max_rom !== null) {
            // Mostrar resultados bilaterales
            unilateralResult.style.display = 'none';
            bilateralResult.style.display = 'block';
            
            document.getElementById('leftROM').textContent = `${finalData.left_max_rom.toFixed(1)}°`;
            document.getElementById('rightROM').textContent = `${finalData.right_max_rom.toFixed(1)}°`;
            
            // Clasificación INDIVIDUAL para cada lado - USAR BACKEND SI EXISTE
            // El backend usa rom_standards con rangos específicos por ejercicio
            let leftClass, rightClass;
            
            if (finalData.left_classification) {
                leftClass = this.getClassificationStyle(finalData.left_classification);
                console.log('[showResults] Clasificación izq del backend:', finalData.left_classification);
            } else {
                leftClass = this.classifyROM(finalData.left_max_rom);
                console.log('[showResults] Clasificación izq local (fallback):', leftClass.label);
            }
            
            if (finalData.right_classification) {
                rightClass = this.getClassificationStyle(finalData.right_classification);
                console.log('[showResults] Clasificación der del backend:', finalData.right_classification);
            } else {
                rightClass = this.classifyROM(finalData.right_max_rom);
                console.log('[showResults] Clasificación der local (fallback):', rightClass.label);
            }
            
            const leftClassEl = document.getElementById('leftClassification');
            const rightClassEl = document.getElementById('rightClassification');
            
            if (leftClassEl) {
                leftClassEl.textContent = leftClass.label;
                leftClassEl.className = 'badge ms-2 ' + leftClass.class;
            }
            if (rightClassEl) {
                rightClassEl.textContent = rightClass.label;
                rightClassEl.className = 'badge ms-2 ' + rightClass.class;
            }
            
            // Mostrar asimetría
            const asymmetry = Math.abs(finalData.left_max_rom - finalData.right_max_rom);
            const asymmetryValueEl = document.getElementById('asymmetryValue');
            const asymmetryBadgeEl = document.getElementById('asymmetryBadge');
            
            if (asymmetryValueEl) {
                asymmetryValueEl.textContent = `${asymmetry.toFixed(1)}°`;
            }
            if (asymmetryBadgeEl) {
                if (asymmetry < 10) {
                    asymmetryBadgeEl.textContent = 'Normal';
                    asymmetryBadgeEl.className = 'badge ms-2 bg-success';
                } else if (asymmetry < 20) {
                    asymmetryBadgeEl.textContent = 'Leve';
                    asymmetryBadgeEl.className = 'badge ms-2 bg-warning';
                } else {
                    asymmetryBadgeEl.textContent = 'Significativa';
                    asymmetryBadgeEl.className = 'badge ms-2 bg-danger';
                }
            }
            
            // Usar el mayor para clasificación general
            var maxROM = Math.max(finalData.left_max_rom, finalData.right_max_rom);
        } else {
            // Mostrar resultado unilateral
            unilateralResult.style.display = 'flex';
            bilateralResult.style.display = 'none';
            
            var maxROM = finalData.max_rom || finalData.rom_percentile_95 || 0;
            document.getElementById('finalROM').textContent = `${maxROM.toFixed(1)}°`;
            
            // Mostrar LADO en resultado unilateral
            // PRIORIDAD: finalData.side (del backend) sobre lastDetectedSide
            const sideToShow = (finalData.side && finalData.side !== 'Detectando...') 
                ? finalData.side 
                : (this.lastDetectedSide || 'unknown');
            const sideLabels = { 'left': 'Izquierdo', 'right': 'Derecho', 'izquierdo': 'Izquierdo', 'derecho': 'Derecho' };
            const sideDisplay = sideLabels[sideToShow] || sideToShow;
            const finalSideEl = document.getElementById('finalSide');
            if (finalSideEl) {
                finalSideEl.textContent = sideDisplay;
            }
        }
        
        // Clasificar ROM - USAR CLASIFICACIÓN DEL BACKEND SI EXISTE
        // El backend tiene lógica específica para cada ejercicio (ej: extensión de codo)
        // que el frontend no puede replicar correctamente con porcentajes simples
        let classification;
        if (finalData.classification) {
            // Usar clasificación del backend (más precisa)
            classification = this.getClassificationStyle(finalData.classification);
            console.log('[LiveAnalysis] Usando clasificación del backend:', finalData.classification);
        } else {
            // Fallback: calcular localmente (menos preciso para ejercicios especiales)
            classification = this.classifyROM(maxROM);
            console.log('[LiveAnalysis] Usando clasificación local (fallback):', classification.label);
        }
        const badgeElement = document.getElementById('romClassification');
        badgeElement.textContent = classification.label;
        badgeElement.className = 'result-value badge ' + classification.class;
        
        // =====================================================================
        // ⚠️ MOSTRAR ADVERTENCIA DE MEDICIÓN SOSPECHOSA
        // Si el backend marcó la medición como sospechosa, mostrar alerta
        // =====================================================================
        const suspiciousAlert = document.getElementById('suspiciousAlert');
        if (suspiciousAlert) {
            if (finalData.is_suspicious) {
                // Mostrar alerta
                suspiciousAlert.classList.remove('d-none');
                
                // Configurar severidad (warning o error)
                if (finalData.suspicious_severity === 'error') {
                    suspiciousAlert.classList.remove('alert-warning');
                    suspiciousAlert.classList.add('alert-danger');
                } else {
                    suspiciousAlert.classList.remove('alert-danger');
                    suspiciousAlert.classList.add('alert-warning');
                }
                
                // Llenar contenido
                const reasonEl = document.getElementById('suspiciousReason');
                const recommendationEl = document.getElementById('suspiciousRecommendation');
                const expectedRangeEl = document.getElementById('suspiciousExpectedRange');
                
                if (reasonEl) reasonEl.textContent = finalData.suspicious_reason || '';
                if (recommendationEl) recommendationEl.textContent = finalData.suspicious_recommendation || '';
                if (expectedRangeEl) {
                    expectedRangeEl.innerHTML = finalData.suspicious_expected_range 
                        ? `<em>${finalData.suspicious_expected_range}</em>` 
                        : '';
                }
                
                console.log('[LiveAnalysis] ⚠️ Medición sospechosa detectada:', {
                    reason: finalData.suspicious_reason,
                    severity: finalData.suspicious_severity
                });
            } else {
                // Ocultar alerta si no es sospechosa
                suspiciousAlert.classList.add('d-none');
            }
        }
        
        // Mostrar modal
        const modalElement = document.getElementById('resultsModal');
        const modal = new bootstrap.Modal(modalElement);
        
        // Agregar listener para limpiar cuando el modal se cierre (solo una vez)
        if (!modalElement.dataset.cleanupAdded) {
            modalElement.dataset.cleanupAdded = 'true';
            modalElement.addEventListener('hidden.bs.modal', () => {
                // Forzar limpieza del backdrop
                document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
                
                // 🧹 Limpiar indicador de pierna en el video (para hip abduction)
                this.clearSelectedLeg();
                
                console.log('[LiveAnalysis] Modal cerrado - backdrop y pierna limpiados');
            });
        }
        
        modal.show();
        
        console.log('[LiveAnalysis] Resultados mostrados:', finalData);
    }
    
    /**
     * 🦵 Maneja la finalización del análisis bilateral secuencial
     * 
     * Este método se llama cuando se completa el análisis de una pierna
     * en modo bilateral secuencial (hip abduction).
     * 
     * - Si es la primera pierna: guarda resultado y muestra modal de continuación
     * - Si es la segunda pierna: combina resultados y muestra resultado final bilateral
     */
    handleSequentialBilateralCompletion(result) {
        console.log('[Sequential] Completado - Fase:', this.sequentialPhase, 'Resultado:', result);
        console.log('[Sequential] Clasificación del backend:', result.classification, '| max_rom:', result.max_rom);
        
        const legLabels = { 'left': 'Izquierda', 'right': 'Derecha' };
        
        if (this.sequentialPhase === 1) {
            // PRIMERA PIERNA COMPLETADA
            console.log('[Sequential] Primera pierna completada:', this.sequentialFirstLeg);
            
            // IMPORTANTE: Usar clasificación del BACKEND (ya viene calculada con rom_standards)
            // Solo usar classifyROM como fallback si no hay clasificación del backend
            const backendClassification = result.classification;
            const romValue = result.max_rom || result.rom_percentile_95 || 0;
            const finalClassification = backendClassification || this.classifyROM(romValue).label;
            
            console.log('[Sequential] Fase 1 - Clasificación usada:', finalClassification, '(backend:', backendClassification, ')');
            
            // Guardar resultado de primera pierna
            this.sequentialFirstResult = {
                leg: this.sequentialFirstLeg,
                max_rom: romValue,
                classification: finalClassification
            };
            
            // Actualizar modal de continuación con datos
            document.getElementById('firstLegLabel').textContent = legLabels[this.sequentialFirstLeg] || this.sequentialFirstLeg;
            document.getElementById('firstLegROM').textContent = `${this.sequentialFirstResult.max_rom.toFixed(1)}°`;
            
            const classStyle = this.getClassificationStyle(this.sequentialFirstResult.classification);
            const firstLegClassEl = document.getElementById('firstLegClass');
            if (firstLegClassEl) {
                firstLegClassEl.textContent = this.sequentialFirstResult.classification;
                firstLegClassEl.className = 'badge ms-2 ' + classStyle.class;
            }
            
            document.getElementById('secondLegLabel').textContent = legLabels[this.sequentialSecondLeg] || this.sequentialSecondLeg;
            
            // Mostrar modal de continuación
            const modal = new bootstrap.Modal(document.getElementById('continueAnalysisModal'));
            modal.show();
            
        } else if (this.sequentialPhase === 2) {
            // SEGUNDA PIERNA COMPLETADA
            console.log('[Sequential] Segunda pierna completada:', this.sequentialSecondLeg);
            
            // IMPORTANTE: Usar clasificación del BACKEND (ya viene calculada con rom_standards)
            const backendClassification = result.classification;
            const romValue = result.max_rom || result.rom_percentile_95 || 0;
            const finalClassification = backendClassification || this.classifyROM(romValue).label;
            
            console.log('[Sequential] Fase 2 - Clasificación usada:', finalClassification, '(backend:', backendClassification, ')');
            
            // Guardar resultado de segunda pierna
            this.sequentialSecondResult = {
                leg: this.sequentialSecondLeg,
                max_rom: romValue,
                classification: finalClassification
            };
            
            // Resetear modo bilateral
            this.isSequentialBilateral = false;
            this.sequentialPhase = 0;
            
            // Construir resultado combinado bilateral
            const combinedResult = this.buildCombinedBilateralResult();
            
            // 🔊 Hablar resultado combinado usando el endpoint TTS
            this.speakBilateralResult(combinedResult);
            
            // Mostrar resultado final bilateral
            // (clearSelectedLeg se llamará cuando se cierre el modal)
            this.showResults(combinedResult);
        }
    }
    
    /**
     * 🔊 Llama al TTS para hablar el resultado bilateral combinado
     */
    async speakBilateralResult(combinedResult) {
        try {
            const response = await fetch('/api/tts/speak_result', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    rom_value: combinedResult.max_rom,
                    classification: combinedResult.classification,
                    is_bilateral: true,
                    left_rom: combinedResult.left_max_rom,
                    right_rom: combinedResult.right_max_rom
                })
            });
            
            if (!response.ok) {
                console.warn('[TTS] No se pudo hablar resultado bilateral');
            }
        } catch (error) {
            console.warn('[TTS] Error al hablar resultado:', error);
        }
    }
    
    /**
     * 🧹 Limpia el indicador de pierna seleccionada en el video
     * Se llama cuando termina el análisis bilateral para quitar el texto "Analizando: PIERNA X"
     */
    async clearSelectedLeg() {
        try {
            const response = await fetch('/api/session/set_leg', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    leg: 'both',  // Resetear a 'both' para que no muestre indicador
                    suppress_tts: true
                })
            });
            
            if (!response.ok) {
                console.warn('[clearSelectedLeg] No se pudo limpiar indicador de pierna');
            } else {
                console.log('[clearSelectedLeg] Indicador de pierna limpiado');
            }
        } catch (error) {
            console.warn('[clearSelectedLeg] Error:', error);
        }
    }
    
    /**
     * 🦵 Construye el resultado combinado de ambas piernas
     */
    buildCombinedBilateralResult() {
        const first = this.sequentialFirstResult;
        const second = this.sequentialSecondResult;
        
        // Determinar cuál es izquierda y cuál derecha
        let leftResult, rightResult;
        if (first.leg === 'left') {
            leftResult = first;
            rightResult = second;
        } else {
            leftResult = second;
            rightResult = first;
        }
        
        // Calcular asimetría
        const asymmetry = Math.abs(leftResult.max_rom - rightResult.max_rom);
        
        // ROM máximo general (el mayor de los dos)
        const maxROM = Math.max(leftResult.max_rom, rightResult.max_rom);
        
        // Clasificación general: usar las clasificaciones del BACKEND (más conservadora)
        // Prioridad de clasificaciones de más limitante a menos:
        // "Muy Limitado" > "Limitado" > "Funcional" > "Óptimo" > "Aumentado"
        const classificationPriority = {
            'muy limitado': 1,
            'limitado': 2,
            'funcional': 3,
            'óptimo': 4,
            'optimo': 4,
            'aumentado': 5
        };
        
        // Usar clasificaciones del backend (ya vienen de cada análisis individual)
        const leftPriority = classificationPriority[leftResult.classification.toLowerCase()] || 3;
        const rightPriority = classificationPriority[rightResult.classification.toLowerCase()] || 3;
        
        // La clasificación general es la MÁS CONSERVADORA (menor prioridad = más limitante)
        const generalClassification = leftPriority <= rightPriority 
            ? leftResult.classification 
            : rightResult.classification;
        
        console.log('[buildCombinedBilateralResult] Clasificaciones:', {
            left: leftResult.classification,
            right: rightResult.classification,
            general: generalClassification
        });
        
        return {
            is_bilateral: true,
            left_max_rom: leftResult.max_rom,
            right_max_rom: rightResult.max_rom,
            max_rom: maxROM,
            rom_percentile_95: maxROM,
            asymmetry: asymmetry,
            classification: generalClassification,
            left_classification: leftResult.classification,
            right_classification: rightResult.classification,
            // Datos adicionales para guardar
            side: 'bilateral',
            sequential_mode: true
        };
    }
    
    /**
     * Clasifica el ROM según rangos
     * 
     * Referencias bibliográficas:
     * - AAOS (American Academy of Orthopaedic Surgeons) - Joint Motion
     * - Beighton Scale - Criterios de hiperlaxitud articular
     * - Nordin & Frankel - Basic Biomechanics of the Musculoskeletal System
     * 
     * Clasificación:
     * - Muy Limitado: <50% del rango normal (rojo)
     * - Limitado: 50-69% del rango normal (naranja)
     * - Funcional: 70-89% del rango normal (celeste)
     * - Óptimo: 90-100% del rango normal (verde)
     * - Aumentado: >100% del rango normal - hiperlaxitud (amarillo dorado)
     * 
     * Justificación: Según AAOS, el rango normal representa el máximo
     * fisiológico. Superar este límite indica hiperlaxitud (Beighton Scale).
     */
    classifyROM(rom) {
        const maxNormal = this.config.max_angle || 150;
        const percentage = (rom / maxNormal) * 100;
        
        // Verificar hiperlaxitud (>100.5% - margen para precisión de punto flotante)
        // Según AAOS: superar el rango normal máximo = hiperlaxitud
        if (percentage > 100.5) {
            return { label: 'Aumentado', class: 'bg-increased' };  // Amarillo dorado para hiperlaxitud
        } else if (percentage >= 90) {
            return { label: 'Óptimo', class: 'bg-success' };       // Verde
        } else if (percentage >= 70) {
            return { label: 'Funcional', class: 'bg-info' };       // Celeste
        } else if (percentage >= 50) {
            return { label: 'Limitado', class: 'bg-warning' };     // Naranja
        } else {
            return { label: 'Muy Limitado', class: 'bg-danger' };  // Rojo
        }
    }
    
    /**
     * Convierte la clasificación del backend a objeto con label y clase CSS
     * Usado para mostrar el badge con el estilo correcto
     * 
     * @param {string} backendClassification - Clasificación del backend (ej: "Funcional", "Muy Limitado")
     * @returns {object} - { label: string, class: string }
     */
    getClassificationStyle(backendClassification) {
        // Normalizar el texto (remover acentos y convertir a minúsculas para comparación)
        const normalized = backendClassification.toLowerCase()
            .normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        
        // Mapeo de clasificaciones a estilos
        if (normalized.includes('optimo')) {
            return { label: backendClassification, class: 'bg-success' };
        } else if (normalized.includes('funcional')) {
            return { label: backendClassification, class: 'bg-info' };
        } else if (normalized.includes('muy limitado') || normalized.includes('muy_limitado')) {
            return { label: backendClassification, class: 'bg-danger' };
        } else if (normalized.includes('limitado')) {
            return { label: backendClassification, class: 'bg-warning' };
        } else if (normalized.includes('aumentado') || normalized.includes('hiperextension') || normalized.includes('hiperlaxitud')) {
            return { label: backendClassification, class: 'bg-increased' };
        } else {
            // Por defecto, usar el texto tal cual con estilo neutro
            return { label: backendClassification, class: 'bg-secondary' };
        }
    }

    /**
     * Guarda los resultados en el historial
     */
    async saveResults() {
        console.log('[LiveAnalysis] Guardando resultados...');
        
        // 🛡️ PROTECCIÓN contra doble guardado
        if (this.isSaving) {
            console.warn('[LiveAnalysis] Ya se está guardando, ignorando llamada duplicada');
            return;
        }
        this.isSaving = true;
        
        // Verificar que hay datos para guardar
        if (!this.lastFinalData) {
            console.warn('[LiveAnalysis] No hay datos para guardar');
            this.showToast('No hay resultados para guardar', 'warning');
            this.isSaving = false;
            return;
        }
        
        const finalData = this.lastFinalData;
        const isBilateral = finalData.is_bilateral === true;
        
        // Preparar datos para enviar
        const segment = this.config.segment_type || this.config.segment || this.config.joint_type || 'unknown';
        
        // Extraer exercise_type del exercise_key (ej: "flexion", "extension", "abduction")
        let exerciseType = this.config.exercise_key || 'unknown';
        
        // El LADO viene del resultado final (finalData.side) que es el más confiable
        // ya que se captura exactamente al momento de completar el análisis
        let side = 'right'; // default
        if (isBilateral) {
            side = 'bilateral';
        } else if (finalData.side && finalData.side !== 'Detectando...') {
            // PRIORIDAD 1: Usar el lado del resultado final (viene del backend)
            side = finalData.side;
        } else if (this.lastDetectedSide) {
            // PRIORIDAD 2: Fallback al último lado detectado durante polling
            side = this.lastDetectedSide;
        }
        
        // Usar clasificaciones del backend (ya vienen en finalData para bilateral secuencial)
        // Solo calcular localmente como fallback si no vienen
        let leftClassification = null;
        let rightClassification = null;
        let generalClassification = null;
        
        if (isBilateral && finalData.left_max_rom && finalData.right_max_rom) {
            // Preferir clasificaciones del backend/resultado combinado
            leftClassification = finalData.left_classification || this.classifyROM(finalData.left_max_rom).label;
            rightClassification = finalData.right_classification || this.classifyROM(finalData.right_max_rom).label;
            generalClassification = finalData.classification || this.classifyROM(
                Math.max(finalData.left_max_rom || 0, finalData.right_max_rom || 0)
            ).label;
        } else {
            generalClassification = finalData.classification || this.classifyROM(
                finalData.max_rom || finalData.rom_percentile_95 || 0
            ).label;
        }
        
        const saveData = {
            segment: segment,
            exercise_type: exerciseType,
            side: side,
            camera_view: this.config.camera_view || 'profile',
            rom_value: isBilateral 
                ? Math.max(finalData.left_max_rom || 0, finalData.right_max_rom || 0)
                : (finalData.max_rom || finalData.rom_percentile_95 || 0),
            left_rom: isBilateral ? finalData.left_max_rom : null,
            right_rom: isBilateral ? finalData.right_max_rom : null,
            left_classification: leftClassification,
            right_classification: rightClassification,
            classification: generalClassification,
            quality_score: finalData.quality_score || null,
            duration: finalData.duration || this.config.analysis_duration || 10,
            // 🎯 NUEVO: subject_id para análisis de sujeto (null para auto-análisis)
            subject_id: this.analysisSubjectId || null
        };
        
        console.log('[LiveAnalysis] Datos a guardar:', saveData);
        console.log('[LiveAnalysis] Side de finalData:', finalData.side);
        console.log('[LiveAnalysis] Side de polling (lastDetectedSide):', this.lastDetectedSide);
        console.log('[LiveAnalysis] Side USADO para guardar:', saveData.side);
        console.log('[LiveAnalysis] Subject ID:', saveData.subject_id, this.analysisSubjectId ? `(${this.analysisSubjectName})` : '(auto-análisis)');
        
        try {
            const response = await fetch('/api/analysis/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(saveData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('[LiveAnalysis] Guardado exitosamente:', result);
                
                // Mensaje diferente según tipo de análisis
                if (result.analysis_type === 'subject') {
                    this.showToast(`✅ Análisis de "${this.analysisSubjectName}" guardado correctamente`, 'success');
                    
                    // 🧹 Limpiar sesión de análisis de sujeto en el backend
                    try {
                        await fetch('/api/analysis/clear-subject', { method: 'POST' });
                        console.log('[LiveAnalysis] Sesión de sujeto limpiada en backend');
                    } catch (e) {
                        console.warn('[LiveAnalysis] No se pudo limpiar sesión de sujeto:', e);
                    }
                    
                    // Limpiar referencias locales
                    this.analysisSubjectId = null;
                    this.analysisSubjectName = null;
                } else {
                    this.showToast('✅ Auto-análisis guardado en historial', 'success');
                }
                
                // Limpiar datos para evitar doble guardado
                this.lastFinalData = null;
                
                // Cerrar modal Y su backdrop correctamente
                const modalElement = document.getElementById('resultsModal');
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                }
                
                // Forzar limpieza del backdrop después de un pequeño delay
                setTimeout(() => {
                    // Remover cualquier backdrop que haya quedado
                    document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                    // Restaurar scroll del body
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = '';
                    document.body.style.paddingRight = '';
                }, 300);
                
                // Recargar historial reciente si existe el panel
                this.loadRecentHistory();
            } else {
                console.error('[LiveAnalysis] Error al guardar:', result.error);
                this.showToast(`Error: ${result.error}`, 'danger');
            }
            
            // Resetear flag de guardado
            this.isSaving = false;
        } catch (error) {
            console.error('[LiveAnalysis] Error de conexión:', error);
            this.showToast('Error de conexión al guardar', 'danger');
            this.isSaving = false;
        }
    }
    
    /**
     * Muestra un toast de notificación
     * Incluye protección contra duplicados en ventana de 2 segundos
     */
    showToast(message, type = 'info') {
        // 🛡️ Protección contra toasts duplicados
        const now = Date.now();
        const key = `${message}_${type}`;
        if (!this._lastToasts) this._lastToasts = {};
        if (this._lastToasts[key] && (now - this._lastToasts[key]) < 2000) {
            console.log('[Toast] Duplicado ignorado:', message);
            return; // Ignorar si el mismo toast se mostró hace menos de 2 segundos
        }
        this._lastToasts[key] = now;
        
        // Crear contenedor de toasts si no existe
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            toastContainer.style.zIndex = '11000';
            document.body.appendChild(toastContainer);
        }
        
        // Crear toast
        const toastId = 'toast_' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastEl = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
        toast.show();
        
        // Eliminar del DOM después de ocultarse
        toastEl.addEventListener('hidden.bs.toast', () => {
            toastEl.remove();
        });
    }
    
    /**
     * Carga el historial reciente para este ejercicio
     * Si hay subject_id, carga historial del sujeto (rom_session)
     * Si no, carga historial del usuario (user_analysis_history)
     */
    async loadRecentHistory() {
        const historyPanel = document.getElementById('recentHistoryPanel');
        if (!historyPanel) return;
        
        const historyLoading = document.getElementById('historyLoading');
        const historyEmpty = document.getElementById('historyEmpty');
        const historyList = historyPanel.querySelector('.history-list');
        
        try {
            // Usar los MISMOS valores que en saveResults para que coincidan
            const segment = this.config.segment_type || this.config.segment || this.config.joint_type || 'unknown';
            const exerciseType = this.config.exercise_key || 'unknown';
            
            // 🎯 Construir URL con subject_id si es análisis de sujeto
            let url = `/api/analysis/recent?segment=${segment}&exercise_type=${exerciseType}&limit=10`;
            if (this.analysisSubjectId) {
                url += `&subject_id=${this.analysisSubjectId}`;
                console.log('[LoadHistory] Buscando historial de SUJETO:', { segment, exerciseType, subjectId: this.analysisSubjectId });
            } else {
                console.log('[LoadHistory] Buscando historial AUTO-ANÁLISIS:', { segment, exerciseType });
            }
            
            const response = await fetch(url);
            const result = await response.json();
            
            // Ocultar loading
            if (historyLoading) historyLoading.style.display = 'none';
            
            if (result.success && result.recent.length > 0) {
                if (historyEmpty) historyEmpty.style.display = 'none';
                
                historyList.innerHTML = result.recent.map(item => {
                    // Detectar si es bilateral (tiene left_rom y right_rom)
                    const isBilateral = item.left_rom !== null && item.right_rom !== null;
                    
                    if (isBilateral) {
                        // Calcular clasificación individual para cada lado
                        const leftClass = this.classifyROM(item.left_rom);
                        const rightClass = this.classifyROM(item.right_rom);
                        
                        return `
                            <div class="history-item py-2 border-bottom">
                                <small class="text-muted d-block mb-1">${this.formatDateBolivia(item.created_at)}</small>
                                <div class="d-flex justify-content-between align-items-center">
                                    <div class="d-flex flex-column">
                                        <div class="d-flex align-items-center gap-2 mb-1">
                                            <span style="color: #00d4ff; font-weight: bold;">Izq: ${item.left_rom.toFixed(1)}°</span>
                                            <span class="badge ${leftClass.class}" style="font-size: 0.7rem;">${leftClass.label}</span>
                                        </div>
                                        <div class="d-flex align-items-center gap-2">
                                            <span style="color: #ff00ff; font-weight: bold;">Der: ${item.right_rom.toFixed(1)}°</span>
                                            <span class="badge ${rightClass.class}" style="font-size: 0.7rem;">${rightClass.label}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    } else {
                        // Unilateral - mostrar como antes pero con lado correcto
                        return `
                            <div class="history-item d-flex justify-content-between align-items-center py-2 border-bottom">
                                <div class="d-flex flex-column">
                                    <small class="text-muted">${this.formatDateBolivia(item.created_at)}</small>
                                    <div>
                                        <span class="fw-bold text-primary">${item.rom_value.toFixed(1)}°</span>
                                        <span class="badge bg-secondary ms-1">${this.formatSide(item.side)}</span>
                                    </div>
                                </div>
                                <span class="badge ${this.getClassificationBadge(item.classification)}">${item.classification || 'N/A'}</span>
                            </div>
                        `;
                    }
                }).join('');
            } else {
                if (historyEmpty) historyEmpty.style.display = 'block';
            }
        } catch (error) {
            console.warn('[LiveAnalysis] Error al cargar historial:', error);
            if (historyLoading) historyLoading.style.display = 'none';
            if (historyEmpty) {
                historyEmpty.innerHTML = '<i class="bi bi-exclamation-circle"></i><small>Error al cargar</small>';
                historyEmpty.style.display = 'block';
            }
        }
    }
    
    /**
     * Formatea el lado para mostrar
     */
    formatSide(side) {
        const sides = {
            'left': 'Izq',
            'right': 'Der',
            'bilateral': 'Bilateral'
        };
        return sides[side] || side || 'N/A';
    }
    
    /**
     * Formatea fecha para mostrar (ya viene en hora Bolivia desde el servidor)
     */
    formatDateBolivia(dateString) {
        if (!dateString) return 'N/A';
        
        // La fecha ya viene en hora de Bolivia desde el servidor
        // Solo formateamos sin conversión de zona horaria
        const date = new Date(dateString);
        
        // Formatear directamente (la hora ya es correcta)
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = String(date.getFullYear()).slice(-2);
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${day}/${month}/${year}, ${hours}:${minutes}`;
    }
    
    /**
     * Obtiene clase de badge según clasificación
     * Colores consistentes con el sistema de clasificación ROM
     */
    getClassificationBadge(classification) {
        const badges = {
            'Aumentado': 'bg-increased',     // Amarillo dorado (hiperlaxitud)
            'Óptimo': 'bg-success',          // Verde
            'Funcional': 'bg-info',          // Celeste
            'Bueno': 'bg-info',              // Alias legacy
            'Limitado': 'bg-warning',        // Naranja
            'Muy Limitado': 'bg-danger',     // Rojo
            'Sin clasificar': 'bg-secondary'
        };
        return badges[classification] || 'bg-secondary';
    }
    
    /**
     * Muestra error en el video feed
     */
    showVideoError() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('hidden');
            overlay.innerHTML = `
                <i class="bi bi-exclamation-triangle text-danger" style="font-size: 3rem;"></i>
                <p class="mt-2 text-danger">Error al cargar el video</p>
                <small>Verifica que la cámara esté conectada y disponible</small>
                <button class="btn btn-primary mt-3" onclick="location.reload()">
                    <i class="bi bi-arrow-clockwise"></i> Recargar
                </button>
            `;
        }
    }
}

// ============================================================================
// INICIALIZACIÓN AL CARGAR LA PÁGINA
// ============================================================================

let liveAnalysisController = null;

document.addEventListener('DOMContentLoaded', () => {
    console.log('[LiveAnalysis] DOM cargado - Inicializando controller');
    
    // Verificar que existe la configuración
    if (typeof EXERCISE_CONFIG === 'undefined') {
        console.error('[LiveAnalysis] EXERCISE_CONFIG no está definido');
        alert('Error: Configuración del ejercicio no disponible');
        return;
    }
    
    // Crear controller
    liveAnalysisController = new LiveAnalysisController(EXERCISE_CONFIG);
    
    console.log('[LiveAnalysis] Sistema listo');
});

// ============================================================================
// FUNCIONES GLOBALES (llamadas desde HTML)
// ============================================================================

function startAnalysis() {
    if (liveAnalysisController) {
        liveAnalysisController.startAnalysis();
    }
}

function stopAnalysis() {
    if (liveAnalysisController) {
        liveAnalysisController.stopAnalysis(true);
    }
}

function resetROM() {
    if (liveAnalysisController) {
        liveAnalysisController.resetROM();
    }
}

function saveResults() {
    if (liveAnalysisController) {
        // Deshabilitar botón inmediatamente para evitar doble click
        const btn = document.querySelector('#resultsModal .btn-success');
        if (btn) {
            if (btn.disabled) return; // Ya está deshabilitado, ignorar
            btn.disabled = true;
            btn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> Guardando...';
        }
        liveAnalysisController.saveResults().finally(() => {
            // Restaurar botón después de completar
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="bi bi-save me-1"></i> Guardar en Historial';
            }
        });
    }
}

// ============================================================================
// 🦵 FUNCIONES PARA ANÁLISIS BILATERAL SECUENCIAL (Hip Abduction)
// ============================================================================

/**
 * Llamada cuando el usuario cancela la selección de pierna (botón X)
 */
function cancelLegSelection() {
    console.log('[LegSelection] Usuario canceló selección de pierna');
    
    if (!liveAnalysisController) return;
    
    // Resetear estado bilateral
    liveAnalysisController.isSequentialBilateral = false;
    liveAnalysisController.sequentialPhase = 0;
    liveAnalysisController.sequentialFirstLeg = null;
    liveAnalysisController.sequentialSecondLeg = null;
    liveAnalysisController.sequentialCurrentLeg = null;
    liveAnalysisController.sequentialFirstResult = null;
    liveAnalysisController.sequentialSecondResult = null;
    
    console.log('[LegSelection] Estado bilateral reseteado');
}

/**
 * Llamada cuando el usuario selecciona una pierna en el modal inicial
 */
function selectLegAndStart(leg) {
    console.log('[LegSelection] Pierna seleccionada:', leg);
    
    if (!liveAnalysisController) return;
    
    // Configurar estado bilateral
    liveAnalysisController.sequentialFirstLeg = leg;
    liveAnalysisController.sequentialSecondLeg = (leg === 'left') ? 'right' : 'left';
    liveAnalysisController.sequentialCurrentLeg = leg;
    liveAnalysisController.sequentialPhase = 1;  // Fase 1: primera pierna
    
    // Cerrar modal
    const modalEl = document.getElementById('legSelectionModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
        modal.hide();
    }
    
    // Iniciar análisis con la pierna seleccionada
    liveAnalysisController.startAnalysisWithLeg(leg);
}

/**
 * Continuar con la segunda pierna
 */
function continueWithSecondLeg() {
    console.log('[LegSelection] Continuando con segunda pierna');
    
    if (!liveAnalysisController) return;
    
    // Cerrar modal
    const modalEl = document.getElementById('continueAnalysisModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
        modal.hide();
    }
    
    // Actualizar fase
    liveAnalysisController.sequentialPhase = 2;
    liveAnalysisController.sequentialCurrentLeg = liveAnalysisController.sequentialSecondLeg;
    
    // Iniciar análisis de segunda pierna
    liveAnalysisController.startAnalysisWithLeg(liveAnalysisController.sequentialSecondLeg);
}

/**
 * Omitir segunda pierna y mostrar resultado solo de la primera
 */
function skipSecondLeg() {
    console.log('[LegSelection] Omitiendo segunda pierna');
    
    if (!liveAnalysisController) return;
    
    // Cerrar modal de continuación
    const modalEl = document.getElementById('continueAnalysisModal');
    const modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) {
        modal.hide();
    }
    
    // Resetear modo bilateral
    liveAnalysisController.isSequentialBilateral = false;
    liveAnalysisController.sequentialPhase = 0;
    
    // Mostrar resultado de la primera pierna como unilateral
    // (clearSelectedLeg se llamará cuando se cierre el modal de resultados)
    const firstResult = liveAnalysisController.sequentialFirstResult;
    if (firstResult) {
        // Convertir a formato unilateral
        const unilateralData = {
            ...firstResult,
            is_bilateral: false,
            max_rom: firstResult.max_rom || firstResult.rom_percentile_95,
            side: liveAnalysisController.sequentialFirstLeg
        };
        liveAnalysisController.showResults(unilateralData);
    }
}

// ============================================================================
// DROPDOWN DE NAVEGACIÓN DE EJERCICIOS
// ============================================================================

/**
 * Alterna la visibilidad del dropdown de ejercicios
 */
function toggleExerciseDropdown() {
    const btn = document.getElementById('exerciseDropdownBtn');
    const menu = document.getElementById('exerciseDropdownMenu');
    
    if (!btn || !menu) return;
    
    const isOpen = menu.classList.contains('show');
    
    if (isOpen) {
        menu.classList.remove('show');
        btn.classList.remove('open');
    } else {
        menu.classList.add('show');
        btn.classList.add('open');
    }
}

/**
 * Cambia al ejercicio seleccionado
 * Libera la cámara antes de navegar para evitar conflictos
 * @param {string} segmentKey - Clave del segmento (shoulder, elbow, etc.)
 * @param {string} exerciseKey - Clave del ejercicio (flexion, extension, etc.)
 */
async function changeExercise(segmentKey, exerciseKey) {
    // Cerrar el dropdown
    const btn = document.getElementById('exerciseDropdownBtn');
    const menu = document.getElementById('exerciseDropdownMenu');
    if (menu) menu.classList.remove('show');
    if (btn) btn.classList.remove('open');
    
    const newUrl = `/segments/${segmentKey}/exercises/${exerciseKey}`;
    console.log('[LiveAnalysis] Preparando cambio a:', newUrl);
    
    try {
        // 1. Detener el video feed inmediatamente
        const videoFeed = document.getElementById('videoFeed');
        if (videoFeed) {
            videoFeed.src = '';  // Cortar conexión del stream
            console.log('[LiveAnalysis] Video feed detenido');
        }
        
        // 2. Detener polling si está activo
        if (liveAnalysisController) {
            liveAnalysisController.stopDataPolling();
            liveAnalysisController.stopSessionPolling();
        }
        
        // 3. Liberar cámara explícitamente
        console.log('[LiveAnalysis] Liberando cámara...');
        await fetch('/api/camera/release', { method: 'POST' });
        
        // 4. Pequeña pausa para asegurar liberación
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // 5. Navegar al nuevo ejercicio
        console.log('[LiveAnalysis] Navegando a:', newUrl);
        window.location.href = newUrl;
        
    } catch (error) {
        console.error('[LiveAnalysis] Error al cambiar ejercicio:', error);
        // Intentar navegar de todos modos
        window.location.href = newUrl;
    }
}

/**
 * Navega de vuelta a la lista de ejercicios
 * Libera la cámara antes de navegar
 */
async function navigateBack() {
    const backUrl = (typeof EXERCISE_CONFIG !== 'undefined' && EXERCISE_CONFIG.back_url) 
        ? EXERCISE_CONFIG.back_url 
        : '/segments';
    
    console.log('[LiveAnalysis] Preparando navegación a:', backUrl);
    
    try {
        // 1. Detener el video feed
        const videoFeed = document.getElementById('videoFeed');
        if (videoFeed) {
            videoFeed.src = '';
        }
        
        // 2. Detener polling
        if (liveAnalysisController) {
            liveAnalysisController.stopDataPolling();
            liveAnalysisController.stopSessionPolling();
        }
        
        // 3. Liberar cámara
        await fetch('/api/camera/release', { method: 'POST' });
        
        // 4. Navegar
        await new Promise(resolve => setTimeout(resolve, 100));
        window.location.href = backUrl;
        
    } catch (error) {
        console.error('[LiveAnalysis] Error al volver:', error);
        window.location.href = backUrl;
    }
}

// Cerrar dropdown al hacer clic fuera
document.addEventListener('click', function(event) {
    const container = document.querySelector('.exercise-dropdown-container');
    const menu = document.getElementById('exerciseDropdownMenu');
    const btn = document.getElementById('exerciseDropdownBtn');
    
    if (container && menu && btn && !container.contains(event.target)) {
        menu.classList.remove('show');
        btn.classList.remove('open');
    }
});

// ============================================================================
// MODO PANTALLA COMPLETA
// ============================================================================

let isFullscreenMode = false;
let originalVideoParent = null;
let fullscreenOverlay = null;

// Crear el overlay dinámicamente al cargar la página
function createFullscreenOverlay() {
    if (fullscreenOverlay) return; // Ya existe
    
    fullscreenOverlay = document.createElement('div');
    fullscreenOverlay.id = 'fullscreenOverlay';
    fullscreenOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        width: 100vw;
        height: 100vh;
        background: #000;
        z-index: 9999;
        display: none;
        margin: 0;
        padding: 0;
        overflow: hidden;
    `;
    
    fullscreenOverlay.innerHTML = `
        <!-- Botón de cerrar (esquina superior derecha) -->
        <button class="fullscreen-close" onclick="toggleFullscreen()" style="
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(0, 0, 0, 0.6);
            border: 2px solid rgba(255, 255, 255, 0.3);
            color: white;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            font-size: 1.3rem;
            cursor: pointer;
            transition: all 0.3s ease;
            z-index: 10002;
            backdrop-filter: blur(5px);
        ">
            <i class="bi bi-x-lg"></i>
        </button>
        
        <!-- Contenedor del video - OCUPA TODA LA PANTALLA -->
        <div id="fullscreenVideoContainer" style="
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #000;
        ">
            <!-- El video y stateOverlay se moverán aquí dinámicamente -->
        </div>
        
        <!-- Métricas flotantes (esquina superior izquierda, compactas) -->
        <div class="fullscreen-metrics" style="
            position: absolute;
            top: 15px;
            left: 15px;
            display: flex;
            gap: 10px;
            z-index: 10001;
        ">
            <div class="metric-box" style="
                background: rgba(0, 0, 0, 0.7);
                padding: 10px 18px;
                border-radius: 12px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(102, 126, 234, 0.4);
                text-align: center;
            ">
                <div style="font-size: 0.7rem; color: rgba(255, 255, 255, 0.6); text-transform: uppercase; letter-spacing: 0.5px;">Ángulo</div>
                <div id="fullscreenCurrentAngle" style="font-size: 1.5rem; font-weight: 700; color: #00d4ff;">0°</div>
            </div>
            <div class="metric-box" style="
                background: rgba(0, 0, 0, 0.7);
                padding: 10px 18px;
                border-radius: 12px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(17, 153, 142, 0.4);
                text-align: center;
            ">
                <div style="font-size: 0.7rem; color: rgba(255, 255, 255, 0.6); text-transform: uppercase; letter-spacing: 0.5px;">ROM Máx</div>
                <div id="fullscreenMaxROM" style="font-size: 1.5rem; font-weight: 700; color: #4CAF50;">0°</div>
            </div>
            <div class="metric-box" style="
                background: rgba(0, 0, 0, 0.7);
                padding: 10px 18px;
                border-radius: 12px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 193, 7, 0.4);
                text-align: center;
            ">
                <div style="font-size: 0.7rem; color: rgba(255, 255, 255, 0.6); text-transform: uppercase; letter-spacing: 0.5px;">Estado</div>
                <div id="fullscreenPostureStatus" style="display: flex; align-items: center; gap: 5px; font-size: 0.9rem; color: #ffc107;">
                    <i class="bi bi-hourglass-split"></i>
                    <span>...</span>
                </div>
            </div>
        </div>
        
        <!-- Controles flotantes (parte inferior, compactos) -->
        <div class="fullscreen-controls" style="
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 12px;
            z-index: 10001;
            background: rgba(0, 0, 0, 0.7);
            padding: 12px 20px;
            border-radius: 40px;
            backdrop-filter: blur(10px);
        ">
            <button id="fullscreenStartBtn" class="btn btn-success" onclick="startAnalysis()" style="padding: 8px 16px;">
                <i class="bi bi-play-fill"></i> Iniciar
            </button>
            <button id="fullscreenStopBtn" class="btn btn-danger" onclick="stopAnalysis()" disabled style="padding: 8px 16px;">
                <i class="bi bi-stop-fill"></i> Detener
            </button>
            <button id="fullscreenResetBtn" class="btn btn-warning" onclick="resetROM()" style="padding: 8px 16px;">
                <i class="bi bi-arrow-clockwise"></i> Reset
            </button>
            <button id="fullscreenAudioBtn" class="btn btn-info" onclick="toggleAudio()" style="padding: 8px 16px;" title="Activar/Desactivar guía de voz">
                <i class="bi bi-volume-up-fill" id="fullscreenAudioIcon"></i> Audio
            </button>
        </div>
    `;
    
    // Agregar al body (fuera de cualquier contenedor)
    document.body.appendChild(fullscreenOverlay);
    console.log('[Fullscreen] Overlay creado y agregado al body');
}

function toggleFullscreen() {
    // Asegurarse de que el overlay existe
    if (!fullscreenOverlay) {
        createFullscreenOverlay();
    }
    
    const fullscreenContainer = document.getElementById('fullscreenVideoContainer');
    const videoElement = document.getElementById('videoFeed');
    const stateOverlay = document.getElementById('stateOverlay');
    const videoWrapper = document.getElementById('videoWrapper');
    
    isFullscreenMode = !isFullscreenMode;
    
    if (isFullscreenMode) {
        // Entrar en modo pantalla completa
        originalVideoParent = videoElement.parentElement;
        
        // MOVER el video al contenedor de pantalla completa
        fullscreenContainer.appendChild(videoElement);
        
        // MOVER también el stateOverlay si existe
        if (stateOverlay) {
            fullscreenContainer.appendChild(stateOverlay);
            // Ajustar estilos para pantalla completa
            stateOverlay.style.zIndex = '10000';
            stateOverlay.style.position = 'absolute';
            stateOverlay.style.top = '0';
            stateOverlay.style.left = '0';
            stateOverlay.style.right = '0';
            stateOverlay.style.bottom = '0';
        }
        
        // Ajustar estilos del video para que OCUPE TODA LA PANTALLA
        videoElement.style.width = '100%';
        videoElement.style.height = '100%';
        videoElement.style.maxWidth = '100vw';
        videoElement.style.maxHeight = '100vh';
        videoElement.style.objectFit = 'contain';  // Mantiene proporción, llena el espacio
        videoElement.style.borderRadius = '0';
        videoElement.style.boxShadow = 'none';
        
        // Mostrar overlay de pantalla completa
        fullscreenOverlay.style.display = 'block';
        
        // Bloquear scroll del body
        document.body.style.overflow = 'hidden';
        
        // Sincronizar estados de botones
        syncButtonStates();
        
        // Actualizar métricas fullscreen
        updateFullscreenMetrics();
        
        console.log('[Fullscreen] Modo pantalla completa activado');
    } else {
        // Salir de modo pantalla completa
        if (originalVideoParent && videoWrapper) {
            // Restaurar estilos originales del video
            videoElement.style.maxWidth = '';
            videoElement.style.maxHeight = '';
            videoElement.style.width = '';
            videoElement.style.height = '';
            videoElement.style.objectFit = '';
            videoElement.style.borderRadius = '';
            videoElement.style.boxShadow = '';
            
            // DEVOLVER el video a su contenedor original (videoWrapper)
            videoWrapper.appendChild(videoElement);
            
            // DEVOLVER también el stateOverlay
            if (stateOverlay) {
                videoWrapper.appendChild(stateOverlay);
                // Restaurar estilos originales
                stateOverlay.style.zIndex = '100';
            }
        }
        
        // Ocultar overlay de pantalla completa
        fullscreenOverlay.style.display = 'none';
        
        // Restaurar scroll del body
        document.body.style.overflow = '';
        
        console.log('[Fullscreen] Modo pantalla completa desactivado');
    }
}

function syncButtonStates() {
    // Sincronizar estado de botones entre vista normal y fullscreen
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const resetBtn = document.getElementById('resetBtn');
    
    const fsStartBtn = document.getElementById('fullscreenStartBtn');
    const fsStopBtn = document.getElementById('fullscreenStopBtn');
    const fsResetBtn = document.getElementById('fullscreenResetBtn');
    
    fsStartBtn.disabled = startBtn.disabled;
    fsStopBtn.disabled = stopBtn.disabled;
    fsResetBtn.disabled = resetBtn.disabled;
}

function updateFullscreenMetrics() {
    // Copiar valores actuales a las métricas de pantalla completa
    const currentAngle = document.getElementById('currentAngle').textContent;
    const maxROM = document.getElementById('maxROM').textContent;
    const postureStatus = document.getElementById('postureStatus').innerHTML;
    
    document.getElementById('fullscreenCurrentAngle').textContent = currentAngle;
    document.getElementById('fullscreenMaxROM').textContent = maxROM;
    document.getElementById('fullscreenPostureStatus').innerHTML = postureStatus;
}

// Tecla ESC para salir de pantalla completa
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isFullscreenMode) {
        toggleFullscreen();
    }
});


// ============================================================================
// ⚙️ CONFIGURACIÓN DE CÁMARA
// ============================================================================

let cameraConfigModal = null;
let originalCameraConfig = null;  // Guardar config original al abrir modal

/**
 * Abre el modal de configuración de cámara
 */
async function openCameraConfig() {
    console.log('[CameraConfig] Abriendo modal de configuración');
    
    // Inicializar modal si no existe
    if (!cameraConfigModal) {
        const modalEl = document.getElementById('cameraConfigModal');
        if (modalEl) {
            cameraConfigModal = new bootstrap.Modal(modalEl);
            
            // Listener para cuando se cierra el modal (cancelar)
            modalEl.addEventListener('hidden.bs.modal', () => {
                // Restaurar valores originales si se cerró sin guardar
                if (originalCameraConfig) {
                    restoreOriginalConfig();
                }
            });
        } else {
            console.error('[CameraConfig] Modal no encontrado');
            return;
        }
    }
    
    // Cargar configuración actual
    await loadCameraConfig();
    
    // Guardar copia de la configuración original
    originalCameraConfig = {
        camera_index: document.getElementById('cameraSelect')?.value,
        resolution: document.getElementById('resolutionSelect')?.value,
        jpeg_quality: document.getElementById('jpegQualitySlider')?.value
    };
    
    // Configurar listener del slider
    const slider = document.getElementById('jpegQualitySlider');
    const valueDisplay = document.getElementById('jpegQualityValue');
    if (slider && valueDisplay) {
        slider.oninput = () => {
            valueDisplay.textContent = slider.value;
        };
    }
    
    // Mostrar modal
    cameraConfigModal.show();
}

/**
 * Restaura la configuración original (cuando se cancela)
 */
function restoreOriginalConfig() {
    if (!originalCameraConfig) return;
    
    console.log('[CameraConfig] Restaurando configuración original');
    
    const cameraSelect = document.getElementById('cameraSelect');
    const resolutionSelect = document.getElementById('resolutionSelect');
    const slider = document.getElementById('jpegQualitySlider');
    const valueDisplay = document.getElementById('jpegQualityValue');
    
    if (cameraSelect && originalCameraConfig.camera_index !== undefined) {
        cameraSelect.value = originalCameraConfig.camera_index;
    }
    if (resolutionSelect && originalCameraConfig.resolution) {
        resolutionSelect.value = originalCameraConfig.resolution;
    }
    if (slider && valueDisplay && originalCameraConfig.jpeg_quality) {
        slider.value = originalCameraConfig.jpeg_quality;
        valueDisplay.textContent = originalCameraConfig.jpeg_quality;
    }
    
    // Limpiar referencia
    originalCameraConfig = null;
}

/**
 * Carga la configuración actual de cámara
 */
async function loadCameraConfig() {
    try {
        const response = await fetch('/api/camera/config');
        const data = await response.json();
        
        if (data.success) {
            const config = data.config;
            
            // Actualizar selector de resolución
            const resolutionSelect = document.getElementById('resolutionSelect');
            if (resolutionSelect) {
                resolutionSelect.value = `${config.resolution.width}x${config.resolution.height}`;
            }
            
            // Actualizar slider de calidad
            const slider = document.getElementById('jpegQualitySlider');
            const valueDisplay = document.getElementById('jpegQualityValue');
            if (slider && valueDisplay) {
                slider.value = config.jpeg_quality;
                valueDisplay.textContent = config.jpeg_quality;
            }
            
            // Mostrar info actual
            const infoEl = document.getElementById('currentConfigInfo');
            if (infoEl) {
                infoEl.textContent = `Cámara ${config.camera_index} | ${config.resolution.width}x${config.resolution.height} | JPEG ${config.jpeg_quality}%`;
            }
            
            // Cargar lista de cámaras (usará caché si hay stream activo)
            await loadAvailableCameras(config.camera_index);
            
            // Mostrar/ocultar warning de sesión activa
            const warningEl = document.getElementById('configSessionWarning');
            const cameraSelectEl = document.getElementById('cameraSelect');
            const resolutionSelectEl = document.getElementById('resolutionSelect');
            
            if (data.session_active) {
                warningEl?.classList.remove('d-none');
                if (cameraSelectEl) cameraSelectEl.disabled = true;
                if (resolutionSelectEl) resolutionSelectEl.disabled = true;
            } else {
                warningEl?.classList.add('d-none');
                if (cameraSelectEl) cameraSelectEl.disabled = false;
                if (resolutionSelectEl) resolutionSelectEl.disabled = false;
            }
            
            console.log('[CameraConfig] Configuración cargada:', config);
        }
    } catch (error) {
        console.error('[CameraConfig] Error al cargar configuración:', error);
    }
}

/**
 * Carga la lista de cámaras disponibles (usa caché del servidor)
 */
async function loadAvailableCameras(currentIndex = 0) {
    try {
        const response = await fetch('/api/camera/list');
        const data = await response.json();
        
        if (data.success && data.cameras.length > 0) {
            const cameraSelect = document.getElementById('cameraSelect');
            if (cameraSelect) {
                cameraSelect.innerHTML = '';
                
                data.cameras.forEach(camera => {
                    const option = document.createElement('option');
                    option.value = camera.index;
                    option.textContent = `${camera.name} - ${camera.resolution}`;
                    cameraSelect.appendChild(option);
                });
                
                // Seleccionar la cámara actual
                cameraSelect.value = data.current !== undefined ? data.current : currentIndex;
            }
            
            // Mostrar indicador si es lista cacheada
            if (data.cached) {
                console.log('[CameraConfig] Lista de cámaras desde caché');
            }
            
            // Mostrar warning si la cámara está en uso
            if (data.camera_in_use) {
                console.log('[CameraConfig] Cámara en uso - lista limitada');
            }
            
            console.log('[CameraConfig] Cámaras cargadas:', data.cameras);
        } else {
            console.warn('[CameraConfig] No se encontraron cámaras');
        }
    } catch (error) {
        console.error('[CameraConfig] Error al cargar cámaras:', error);
    }
}

/**
 * Guarda la configuración de cámara
 */
async function saveCameraConfig() {
    const cameraIndex = parseInt(document.getElementById('cameraSelect').value);
    const resolutionValue = document.getElementById('resolutionSelect').value;
    const jpegQuality = parseInt(document.getElementById('jpegQualitySlider').value);
    
    // Parsear resolución
    const [width, height] = resolutionValue.split('x').map(Number);
    
    const configData = {
        camera_index: cameraIndex,
        resolution: { width, height },
        jpeg_quality: jpegQuality
    };
    
    console.log('[CameraConfig] Guardando configuración:', configData);
    
    // Verificar si hay cambios que requieren recarga
    const needsReload = originalCameraConfig && (
        originalCameraConfig.camera_index != cameraIndex ||
        originalCameraConfig.resolution != resolutionValue
    );
    
    // Si necesita recarga, PRIMERO liberar la cámara
    if (needsReload) {
        console.log('[CameraConfig] Cambio de cámara/resolución detectado - liberando cámara primero...');
        try {
            // Detener el video feed cambiando el src
            const videoFeed = document.getElementById('videoFeed');
            if (videoFeed) {
                videoFeed.src = '';  // Detener stream
            }
            
            // Liberar cámara en el servidor
            const releaseResponse = await fetch('/api/camera/release', { method: 'POST' });
            const releaseData = await releaseResponse.json();
            console.log('[CameraConfig] Cámara liberada:', releaseData);
            
            // Pequeña pausa para asegurar que se liberó
            await new Promise(resolve => setTimeout(resolve, 300));
        } catch (e) {
            console.warn('[CameraConfig] Error al liberar cámara (continuando):', e);
        }
    }
    
    try {
        const response = await fetch('/api/camera/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('[CameraConfig] Configuración guardada:', data);
            
            // Limpiar config original (se guardó exitosamente)
            originalCameraConfig = null;
            
            // Cerrar modal
            cameraConfigModal?.hide();
            
            // Mostrar mensaje de éxito
            showToast('Configuración guardada', 'success');
            
            // Si cambió cámara o resolución, recargar página para aplicar
            if (needsReload || (data.changes && data.changes.some(c => c.includes('camera_index') || c.includes('resolution')))) {
                showToast('Recargando para aplicar cambios...', 'info');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } else {
            console.error('[CameraConfig] Error:', data.error);
            showToast(data.error || 'Error al guardar', 'error');
            
            // Si falló y habíamos detenido el video, recargamos para restaurar
            if (needsReload) {
                setTimeout(() => window.location.reload(), 1500);
            }
        }
    } catch (error) {
        console.error('[CameraConfig] Error de red:', error);
        showToast('Error de conexión', 'error');
        
        // Si hay error y habíamos detenido el video, recargamos
        if (needsReload) {
            setTimeout(() => window.location.reload(), 1500);
        }
    }
}

/**
 * Muestra un toast de notificación
 */
function showToast(message, type = 'info') {
    // Crear contenedor si no existe
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
        document.body.appendChild(container);
    }
    
    // Crear toast
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8';
    toast.style.cssText = `
        background: ${bgColor};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease;
    `;
    toast.innerHTML = `<i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info-circle'} me-2"></i>${message}`;
    
    container.appendChild(toast);
    
    // Auto-remover después de 3 segundos
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Estilos de animación para toasts
if (!document.getElementById('toastStyles')) {
    const style = document.createElement('style');
    style.id = 'toastStyles';
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
}

// ============================================================================
// CONTROL DE AUDIO (TTS)
// ============================================================================

let audioEnabled = true; // Estado local del audio

/**
 * Alterna el estado del audio (TTS)
 * Llama al backend y actualiza la UI
 */
async function toggleAudio() {
    try {
        const response = await fetch('/api/tts/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
            const data = await response.json();
            audioEnabled = data.voice_enabled;
            updateAudioButtonState(audioEnabled);
            
            // Guardar preferencia en localStorage
            localStorage.setItem('biotrack_audio_enabled', audioEnabled.toString());
            
            console.log(`🔊 Audio ${audioEnabled ? 'activado' : 'desactivado'}`);
            showToast(`Audio ${audioEnabled ? 'activado' : 'desactivado'}`, audioEnabled ? 'success' : 'info');
        } else {
            console.error('[Audio] Error en toggle:', response.status);
            showToast('Error al cambiar estado del audio', 'error');
        }
    } catch (error) {
        console.error('[Audio] Error:', error);
        showToast('Error de conexión', 'error');
    }
}

/**
 * Actualiza el estado visual de los botones de audio (normal y fullscreen)
 * @param {boolean} enabled - Si el audio está habilitado
 */
function updateAudioButtonState(enabled) {
    // Botón normal
    const audioIcon = document.getElementById('audioIcon');
    const audioBtn = document.getElementById('audioBtn');
    
    // Botón fullscreen
    const fullscreenAudioIcon = document.getElementById('fullscreenAudioIcon');
    const fullscreenAudioBtn = document.getElementById('fullscreenAudioBtn');
    
    if (enabled) {
        // Audio activado
        if (audioIcon) audioIcon.className = 'bi bi-volume-up-fill';
        if (audioBtn) audioBtn.classList.remove('btn-secondary');
        if (audioBtn) audioBtn.classList.add('btn-info');
        
        if (fullscreenAudioIcon) fullscreenAudioIcon.className = 'bi bi-volume-up-fill';
        if (fullscreenAudioBtn) fullscreenAudioBtn.classList.remove('btn-secondary');
        if (fullscreenAudioBtn) fullscreenAudioBtn.classList.add('btn-info');
    } else {
        // Audio desactivado
        if (audioIcon) audioIcon.className = 'bi bi-volume-mute-fill';
        if (audioBtn) audioBtn.classList.remove('btn-info');
        if (audioBtn) audioBtn.classList.add('btn-secondary');
        
        if (fullscreenAudioIcon) fullscreenAudioIcon.className = 'bi bi-volume-mute-fill';
        if (fullscreenAudioBtn) fullscreenAudioBtn.classList.remove('btn-info');
        if (fullscreenAudioBtn) fullscreenAudioBtn.classList.add('btn-secondary');
    }
}

/**
 * Inicializa el estado del audio al cargar la página
 * Sincroniza con el backend y/o localStorage
 */
async function initAudioState() {
    try {
        // Primero intentar obtener del backend
        const response = await fetch('/api/tts/status');
        if (response.ok) {
            const data = await response.json();
            // El backend usa 'enabled', el toggle devuelve 'voice_enabled'
            audioEnabled = data.enabled !== undefined ? data.enabled : data.voice_enabled;
            updateAudioButtonState(audioEnabled);
            console.log(`🔊 [Audio] Estado inicial: ${audioEnabled ? 'activado' : 'desactivado'}`);
        }
    } catch (error) {
        // Si falla, usar localStorage como fallback
        const stored = localStorage.getItem('biotrack_audio_enabled');
        if (stored !== null) {
            audioEnabled = stored === 'true';
            updateAudioButtonState(audioEnabled);
        }
        console.log('[Audio] Usando estado de localStorage:', audioEnabled);
    }
}

// Inicializar estado del audio cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    initAudioState();
});
