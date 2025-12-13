-- ============================================================================
-- MIGRACIÓN: Agregar tabla user_analysis_history
-- ============================================================================
-- Fecha: 2025-11-29
-- Descripción: Tabla simplificada para historial de análisis propios del usuario
-- Uso: Cuando el estudiante se analiza a sí mismo (no a un sujeto externo)
-- ============================================================================

-- Crear tabla user_analysis_history
CREATE TABLE IF NOT EXISTS user_analysis_history (
    -- Identificación
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Usuario que realizó el análisis (se analiza a sí mismo)
    user_id INTEGER NOT NULL,
    
    -- Configuración del Análisis
    segment VARCHAR(50) NOT NULL,
        -- 'ankle', 'knee', 'hip', 'shoulder', 'elbow'
    exercise_type VARCHAR(50) NOT NULL,
        -- 'flexion', 'extension', 'abduction', etc.
    camera_view VARCHAR(20),
        -- 'lateral', 'frontal', 'profile'
    side VARCHAR(20),
        -- 'left', 'right', 'bilateral'
    
    -- Resultados del Análisis
    rom_value FLOAT NOT NULL,
        -- ROM máximo alcanzado (grados) - valor principal
    left_rom FLOAT,
        -- ROM lado izquierdo (para análisis bilateral)
    right_rom FLOAT,
        -- ROM lado derecho (para análisis bilateral)
    quality_score FLOAT,
        -- Calidad de la medición (0-100)
    classification VARCHAR(50),
        -- 'Óptimo', 'Funcional', 'Limitado', 'Muy Limitado'
    
    -- Metadatos
    duration FLOAT,
        -- Duración del análisis en segundos
    samples_collected INTEGER,
        -- Número de muestras recolectadas
    plateau_detected BOOLEAN DEFAULT 0,
        -- Si se detectó meseta
    
    -- Auditoría
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Relaciones
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    
    -- Validaciones
    CHECK (segment IN ('ankle', 'knee', 'hip', 'shoulder', 'elbow')),
    CHECK (camera_view IN ('lateral', 'frontal', 'profile', 'posterior') OR camera_view IS NULL),
    CHECK (side IN ('left', 'right', 'bilateral') OR side IS NULL),
    CHECK (rom_value >= 0 AND rom_value <= 360),
    CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100))
);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_user_analysis_user ON user_analysis_history(user_id);
CREATE INDEX IF NOT EXISTS idx_user_analysis_segment ON user_analysis_history(segment);
CREATE INDEX IF NOT EXISTS idx_user_analysis_exercise ON user_analysis_history(exercise_type);
CREATE INDEX IF NOT EXISTS idx_user_analysis_date ON user_analysis_history(created_at);
CREATE INDEX IF NOT EXISTS idx_user_analysis_segment_exercise ON user_analysis_history(segment, exercise_type);
