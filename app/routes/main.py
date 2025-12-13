"""
🏠 BLUEPRINT PRINCIPAL - BIOTRACK
==================================
Rutas principales de la aplicación

RUTAS:
- /dashboard: Dashboard del usuario
- /profile: Perfil del usuario
- /subjects: Gestión de sujetos
- /sessions: Historial de sesiones
- /users: Gestión de usuarios (admin)

Autor: BIOTRACK Team
Fecha: 2025-11-14
"""

from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, session, current_app
)
from app.routes.auth import login_required, admin_required
from hardware.camera_manager import camera_manager, check_camera_availability

# Importar módulos de control de altura de cámara
from hardware import (
    get_segment_info_for_ui,
    get_effective_height,
    has_temporary_height
)

# Crear blueprint
main_bp = Blueprint('main', __name__)


# ============================================================================
# DASHBOARD
# ============================================================================

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Dashboard principal del usuario
    Redirige al dashboard específico según el rol
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    # Redirigir según rol
    if user_role == 'admin':
        # Dashboard de administrador con estadísticas globales
        global_stats = db_manager.get_admin_global_statistics()
        
        return render_template(
            'admin/dashboard.html',
            stats=global_stats
        )
    else:
        # Dashboard de estudiante
        stats = db_manager.get_user_statistics(user_id)
        
        # Obtener sesiones recientes
        recent_sessions = db_manager.get_sessions_by_user(user_id)
        recent_sessions = recent_sessions[:5] if recent_sessions else []
        
        return render_template(
            'user/dashboard.html',
            stats=stats,
            recent_sessions=recent_sessions
        )


# ============================================================================
# PERFIL
# ============================================================================

@main_bp.route('/profile')
@login_required
def profile():
    """
    Perfil del usuario actual
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    user = db_manager.get_user_by_id(session.get('user_id'))
    
    return render_template('profile.html', user=user)


# ============================================================================
# SUJETOS DE ESTUDIO - CRUD COMPLETO
# ============================================================================
# Permisos según rol:
# - Admin: Ver todos, crear, editar todos, eliminar todos
# - Student: Ver solo los suyos, crear (privados), editar solo los suyos, eliminar solo los suyos

@main_bp.route('/subjects')
@login_required
def subjects():
    """
    Lista de sujetos de estudio
    - Admin: Ve todos los sujetos con información del creador
    - Student: Ve solo los sujetos que él creó
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    # Si es admin, ver todos con info del creador; si es student, solo los suyos
    if user_role == 'admin':
        subjects_list = db_manager.get_all_subjects_with_creator()
    else:
        subjects_list = db_manager.get_subjects_by_user(user_id)
    
    return render_template(
        'subjects/list.html', 
        subjects=subjects_list,
        is_admin=(user_role == 'admin')
    )


@main_bp.route('/subjects/new', methods=['GET', 'POST'])
@login_required
def subjects_new():
    """
    Crear nuevo sujeto de estudio
    - Admin y Student pueden crear sujetos
    - Los sujetos creados por estudiantes son privados (solo ellos los ven)
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            gender = request.form.get('gender') or None
            height = request.form.get('height')
            activity_level = request.form.get('activity_level') or None
            notes = request.form.get('notes', '').strip() or None
            date_of_birth = request.form.get('date_of_birth') or None
            
            # Validaciones básicas
            if not first_name or not last_name:
                flash('El nombre y apellido son obligatorios', 'danger')
                return render_template('subjects/form.html', subject=None, is_edit=False)
            
            # Convertir altura a float si se proporcionó
            if height:
                try:
                    height = float(height)
                    if height < 50 or height > 250:
                        flash('La altura debe estar entre 50 y 250 cm', 'danger')
                        return render_template('subjects/form.html', subject=None, is_edit=False)
                except ValueError:
                    flash('La altura debe ser un número válido', 'danger')
                    return render_template('subjects/form.html', subject=None, is_edit=False)
            else:
                height = None
            
            # Convertir fecha si se proporcionó
            if date_of_birth:
                from datetime import datetime
                try:
                    date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d')
                except ValueError:
                    date_of_birth = None
            
            # Generar código automático
            subject_code = db_manager.generate_subject_code()
            
            # Crear sujeto
            db_manager.create_subject(
                subject_code=subject_code,
                first_name=first_name,
                last_name=last_name,
                created_by=user_id,
                gender=gender,
                height=height,
                activity_level=activity_level,
                notes=notes,
                date_of_birth=date_of_birth
            )
            
            flash(f'Sujeto "{first_name} {last_name}" creado exitosamente con código {subject_code}', 'success')
            return redirect(url_for('main.subjects'))
            
        except Exception as e:
            current_app.logger.error(f"Error creando sujeto: {e}")
            flash('Error al crear el sujeto. Inténtalo de nuevo.', 'danger')
            return render_template('subjects/form.html', subject=None, is_edit=False)
    
    # GET - Mostrar formulario vacío
    return render_template('subjects/form.html', subject=None, is_edit=False)


@main_bp.route('/subjects/<int:subject_id>')
@login_required
def subjects_view(subject_id):
    """
    Ver detalles de un sujeto
    - Admin: Puede ver cualquier sujeto
    - Student: Solo puede ver los suyos
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    # Verificar permisos
    if not db_manager.can_user_access_subject(user_id, subject_id, user_role):
        flash('No tienes permiso para ver este sujeto', 'danger')
        return redirect(url_for('main.subjects'))
    
    # Obtener sujeto
    subject = db_manager.get_subject_by_id_safe(subject_id)
    
    if not subject:
        flash('Sujeto no encontrado', 'warning')
        return redirect(url_for('main.subjects'))
    
    # Obtener sesiones ROM del sujeto
    sessions_list = db_manager.get_sessions_by_subject(subject_id) if hasattr(db_manager, 'get_sessions_by_subject') else []
    
    return render_template(
        'subjects/view.html', 
        subject=subject,
        sessions=sessions_list,
        is_admin=(user_role == 'admin')
    )


@main_bp.route('/subjects/<int:subject_id>/edit', methods=['GET', 'POST'])
@login_required
def subjects_edit(subject_id):
    """
    Editar un sujeto existente
    - Admin: Puede editar cualquier sujeto
    - Student: Solo puede editar los suyos
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    # Verificar permisos
    if not db_manager.can_user_modify_subject(user_id, subject_id, user_role):
        flash('No tienes permiso para editar este sujeto', 'danger')
        return redirect(url_for('main.subjects'))
    
    # Obtener sujeto
    subject = db_manager.get_subject_by_id_safe(subject_id)
    
    if not subject:
        flash('Sujeto no encontrado', 'warning')
        return redirect(url_for('main.subjects'))
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            gender = request.form.get('gender') or None
            height = request.form.get('height')
            activity_level = request.form.get('activity_level') or None
            notes = request.form.get('notes', '').strip() or None
            date_of_birth = request.form.get('date_of_birth') or None
            
            # Validaciones básicas
            if not first_name or not last_name:
                flash('El nombre y apellido son obligatorios', 'danger')
                return render_template('subjects/form.html', subject=subject, is_edit=True)
            
            # Convertir altura a float si se proporcionó
            if height:
                try:
                    height = float(height)
                    if height < 50 or height > 250:
                        flash('La altura debe estar entre 50 y 250 cm', 'danger')
                        return render_template('subjects/form.html', subject=subject, is_edit=True)
                except ValueError:
                    flash('La altura debe ser un número válido', 'danger')
                    return render_template('subjects/form.html', subject=subject, is_edit=True)
            else:
                height = None
            
            # Convertir fecha si se proporcionó
            if date_of_birth:
                from datetime import datetime
                try:
                    date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d')
                except ValueError:
                    date_of_birth = None
            
            # Actualizar sujeto
            db_manager.update_subject(
                subject_id=subject_id,
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                height=height,
                activity_level=activity_level,
                notes=notes,
                date_of_birth=date_of_birth
            )
            
            flash(f'Sujeto "{first_name} {last_name}" actualizado exitosamente', 'success')
            return redirect(url_for('main.subjects_view', subject_id=subject_id))
            
        except Exception as e:
            current_app.logger.error(f"Error actualizando sujeto: {e}")
            flash('Error al actualizar el sujeto. Inténtalo de nuevo.', 'danger')
            return render_template('subjects/form.html', subject=subject, is_edit=True)
    
    # GET - Mostrar formulario con datos
    return render_template('subjects/form.html', subject=subject, is_edit=True)


@main_bp.route('/subjects/<int:subject_id>/delete', methods=['POST'])
@login_required
def subjects_delete(subject_id):
    """
    Eliminar un sujeto
    - Admin: Puede eliminar cualquier sujeto
    - Student: Solo puede eliminar los suyos
    ADVERTENCIA: Esto eliminará también todas las sesiones ROM asociadas
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    user_id = session.get('user_id')
    user_role = session.get('role')
    
    # Verificar permisos
    if not db_manager.can_user_modify_subject(user_id, subject_id, user_role):
        flash('No tienes permiso para eliminar este sujeto', 'danger')
        return redirect(url_for('main.subjects'))
    
    # Obtener sujeto para mostrar nombre en mensaje
    subject = db_manager.get_subject_by_id_safe(subject_id)
    
    if not subject:
        flash('Sujeto no encontrado', 'warning')
        return redirect(url_for('main.subjects'))
    
    try:
        # Eliminar sujeto (las sesiones se eliminarán en cascada)
        if db_manager.delete_subject(subject_id):
            flash(f'Sujeto "{subject["full_name"]}" eliminado exitosamente', 'success')
        else:
            flash('Error al eliminar el sujeto', 'danger')
    except Exception as e:
        current_app.logger.error(f"Error eliminando sujeto: {e}")
        flash('Error al eliminar el sujeto. Puede tener sesiones asociadas.', 'danger')
    
    return redirect(url_for('main.subjects'))


# ============================================================================
# SESIONES / HISTORIAL
# ============================================================================

@main_bp.route('/history')
@login_required
def history():
    """
    Historial de auto-análisis del usuario (user_analysis_history)
    Con filtros por segmento, ejercicio y fecha
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    user_id = session.get('user_id')
    
    # Obtener parámetros de filtro
    segment = request.args.get('segment', '').strip() or None
    exercise = request.args.get('exercise', '').strip() or None
    date_from = request.args.get('date_from', '').strip() or None
    date_to = request.args.get('date_to', '').strip() or None
    
    # Obtener historial filtrado
    analyses = db_manager.get_user_analysis_history_filtered(
        user_id=user_id,
        segment=segment,
        exercise_type=exercise,
        date_from=date_from,
        date_to=date_to,
        limit=100
    )
    
    # Contar total
    total_count = db_manager.count_user_analysis_history(
        user_id=user_id,
        segment=segment,
        exercise_type=exercise,
        date_from=date_from,
        date_to=date_to
    )
    
    # Obtener estadísticas generales (sin filtros)
    stats = db_manager.get_user_analysis_stats(user_id)
    
    # Preparar filtros para el template
    filters = {
        'segment': segment,
        'exercise': exercise,
        'date_from': date_from,
        'date_to': date_to
    }
    
    return render_template(
        'history/self_analysis.html',
        analyses=analyses,
        total_count=total_count,
        stats=stats,
        filters=filters
    )


@main_bp.route('/sessions')
@login_required
def sessions():
    """
    Historial de sesiones ROM del usuario (rom_session - análisis de sujetos)
    NOTA: Este endpoint muestra análisis hechos A sujetos, no auto-análisis.
    Para auto-análisis usar /history
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    user_id = session.get('user_id')
    
    sessions_list = db_manager.get_sessions_by_user(user_id)
    
    return render_template('history/list.html', sessions=sessions_list)


# ============================================================================
# SEGMENTOS BIOMECÁNICOS
# ============================================================================

@main_bp.route('/segments')
@login_required
def segments():
    """
    Página de selección de segmentos biomecánicos
    
    Query params opcionales:
        subject_id: ID del sujeto a analizar (si viene de la sección de sujetos)
    """
    # Capturar subject_id si viene como query param (análisis de sujeto)
    subject_id = request.args.get('subject_id', type=int)
    subject_info = None
    
    if subject_id:
        db_manager = current_app.config.get('DB_MANAGER')
        user_id = session.get('user_id')
        user_role = session.get('role')
        
        # Verificar que el usuario puede acceder a este sujeto
        if db_manager.can_user_access_subject(user_id, subject_id, user_role):
            subject_info = db_manager.get_subject_by_id_safe(subject_id)
            # Guardar en sesión Flask para que persista durante la navegación
            session['analysis_subject_id'] = subject_id
            session['analysis_subject_name'] = subject_info.get('full_name') if subject_info else None
        else:
            flash('No tienes permiso para analizar este sujeto', 'danger')
            return redirect(url_for('main.subjects'))
    else:
        # Limpiar sesión si es auto-análisis (viene del dashboard directo)
        session.pop('analysis_subject_id', None)
        session.pop('analysis_subject_name', None)
    
    return render_template(
        'components/segments.html',
        subject_id=subject_id,
        subject_info=subject_info
    )


@main_bp.route('/segments/<segment_type>/exercises')
@login_required
def segment_exercises(segment_type):
    """
    Página de selección de ejercicios para un segmento específico
    """
    
    # Configuración de segmentos
    segments_config = {
        'shoulder': {
            'name': 'Hombro',
            'description': 'Flexión, extensión, abducción y rotación glenohumeral',
            'icon': 'shoulder_1.png',
            'exercises': [
                {
                    'key': 'flexion',
                    'name': 'Flexión de Hombro',
                    'view': 'Lateral',
                    'view_icon': 'person-standing',
                    'difficulty': 'easy',
                    'difficulty_label': 'Fácil',
                    'rom_range': '0° - 180°',
                    'repetitions': '3-5',
                    'speed': 'Lenta y controlada',
                    'instructions': 'Levanta el brazo hacia adelante hasta alcanzar la máxima altura posible, manteniendo el codo extendido.',
                    'has_video': True,
                    'duration': '15',
                    'warning': None
                },
                {
                    'key': 'extension',
                    'name': 'Extensión de Hombro',
                    'view': 'Lateral',
                    'view_icon': 'person-standing',
                    'difficulty': 'easy',
                    'difficulty_label': 'Fácil',
                    'rom_range': '0° - 60°',
                    'repetitions': '3-5',
                    'speed': 'Lenta y controlada',
                    'instructions': 'Lleva el brazo hacia atrás desde la posición neutra, manteniendo el codo extendido y el torso erguido.',
                    'has_video': True,
                    'duration': '12',
                    'warning': 'No fuerces el movimiento más allá de tu rango cómodo'
                },
                {
                    'key': 'abduction',
                    'name': 'Abducción de Hombro',
                    'view': 'Frontal',
                    'view_icon': 'diagram-3',
                    'difficulty': 'easy',
                    'difficulty_label': 'Fácil',
                    'rom_range': '0° - 180°',
                    'repetitions': '3-5',
                    'speed': 'Lenta y controlada',
                    'instructions': 'Levanta el brazo lateralmente desde la posición neutra hasta alcanzar la vertical.',
                    'has_video': True,
                    'duration': '15',
                    'warning': None
                }
            ]
        },
        'elbow': {
            'name': 'Codo',
            'description': 'Flexión y extensión del codo',
            'icon': 'elbow_1.png',
            'exercises': [
                {
                    'key': 'flexion',
                    'name': 'Flexión de Codo',
                    'view': 'Lateral',
                    'view_icon': 'person-standing',
                    'difficulty': 'easy',
                    'difficulty_label': 'Fácil',
                    'rom_range': '0° - 150°',
                    'repetitions': '3-5',
                    'speed': 'Moderada',
                    'instructions': 'Flexiona el codo llevando la mano hacia el hombro, manteniendo el brazo estable.',
                    'has_video': True,
                    'duration': '10',
                    'warning': None
                },
                {
                    'key': 'extension',
                    'name': 'Extensión de Codo',
                    'view': 'Lateral',
                    'view_icon': 'person-standing',
                    'difficulty': 'easy',
                    'difficulty_label': 'Fácil',
                    'rom_range': '0° - 10°',
                    'repetitions': '3-5',
                    'speed': 'Lenta',
                    'instructions': 'Extiende el brazo completamente. El sistema detectará hiperextensión si la hay.',
                    'has_video': True,
                    'duration': '10',
                    'warning': 'Hiperextensión hasta -10° es normal en algunas personas'
                }
            ]
        },
        'hip': {
            'name': 'Cadera',
            'description': 'Flexión, extensión y abducción de cadera',
            'icon': 'hips_1.png',
            'exercises': [
                {
                    'key': 'flexion',
                    'name': 'Flexión de Cadera',
                    'view': 'Lateral',
                    'view_icon': 'person-standing',
                    'difficulty': 'medium',
                    'difficulty_label': 'Medio',
                    'rom_range': '0° - 135°',
                    'repetitions': '3-5',
                    'speed': 'Lenta',
                    'instructions': 'Levanta la rodilla hacia el pecho manteniendo la espalda recta y el equilibrio.',
                    'has_video': True,
                    'duration': '12',
                    'warning': 'Mantén el equilibrio apoyándote si es necesario'
                },
                {
                    'key': 'extension',
                    'name': 'Extensión de Cadera',
                    'view': 'Lateral',
                    'view_icon': 'person-standing',
                    'difficulty': 'medium',
                    'difficulty_label': 'Medio',
                    'rom_range': '0° - 30°',
                    'repetitions': '3-5',
                    'speed': 'Lenta',
                    'instructions': 'Lleva la pierna hacia atrás manteniendo la rodilla extendida y el torso recto.',
                    'has_video': True,
                    'duration': '12',
                    'warning': 'No arquees la espalda, mantén el abdomen firme'
                },
                {
                    'key': 'abduction',
                    'name': 'Abducción de Cadera',
                    'view': 'Frontal',
                    'view_icon': 'diagram-3',
                    'difficulty': 'medium',
                    'difficulty_label': 'Medio',
                    'rom_range': '0° - 45°',
                    'repetitions': '3-5',
                    'speed': 'Lenta',
                    'instructions': 'Separa la pierna lateralmente manteniendo el cuerpo estable y la rodilla extendida.',
                    'has_video': True,
                    'duration': '12',
                    'warning': 'Usa apoyo para mantener el equilibrio'
                }
            ]
        },
        'knee': {
            'name': 'Rodilla',
            'description': 'Flexión y extensión de la articulación tibiofemoral',
            'icon': 'knee_1.png',
            'exercises': [
                {
                    'key': 'flexion',
                    'name': 'Flexión de Rodilla',
                    'view': 'Lateral',
                    'view_icon': 'person-standing',
                    'difficulty': 'easy',
                    'difficulty_label': 'Fácil',
                    'rom_range': '0° - 150°',
                    'repetitions': '3-5',
                    'speed': 'Moderada',
                    'instructions': 'Flexiona la rodilla llevando el talón hacia los glúteos mientras mantienes el equilibrio.',
                    'has_video': True,
                    'duration': '14',
                    'warning': 'Apóyate si sientes inestabilidad'
                },
                {
                    'key': 'extension',
                    'name': 'Extensión Terminal de Rodilla',
                    'view': 'Lateral',
                    'view_icon': 'person-standing',
                    'difficulty': 'easy',
                    'difficulty_label': 'Fácil',
                    'rom_range': '0° - 10°',
                    'repetitions': '3-5',
                    'speed': 'Lenta',
                    'instructions': 'Extiende completamente la rodilla desde una posición ligeramente flexionada.',
                    'has_video': True,
                    'duration': '14',
                    'warning': 'Evita la hiperextensión forzada'
                }
            ]
        },
        'ankle': {
            'name': 'Tobillo',
            'description': 'Dorsiflexión y plantiflexión (vista lateral)',
            'icon': 'ankle_1.png',
            'exercises': [
                {
                    'key': 'dorsiflexion',
                    'name': 'Dorsiflexión de Tobillo',
                    'view': 'Lateral',
                    'view_icon': 'person-standing',
                    'difficulty': 'easy',
                    'difficulty_label': 'Fácil',
                    'rom_range': '0° - 20°',
                    'repetitions': '5-8',
                    'speed': 'Lenta',
                    'instructions': 'Flexiona el pie hacia arriba llevando los dedos hacia la espinilla.',
                    'has_video': True,
                    'duration': '8',
                    'warning': None
                },
                {
                    'key': 'plantarflexion',
                    'name': 'Plantiflexión de Tobillo',
                    'view': 'Lateral',
                    'view_icon': 'person-standing',
                    'difficulty': 'easy',
                    'difficulty_label': 'Fácil',
                    'rom_range': '0° - 50°',
                    'repetitions': '5-8',
                    'speed': 'Lenta',
                    'instructions': 'Extiende el pie hacia abajo como si te pusieras de puntillas.',
                    'has_video': True,
                    'duration': '8',
                    'warning': None
                }
            ]
        }
    }
    
    # Validar que el segmento existe
    if segment_type not in segments_config:
        flash('Segmento no encontrado', 'danger')
        return redirect(url_for('main.segments'))
    
    segment = segments_config[segment_type]
    
    # ========================================================================
    # CÁLCULO DE ALTURA DE CÁMARA (Drillis-Contini)
    # ========================================================================
    
    # Obtener altura del usuario desde BD (método optimizado)
    db_manager = current_app.config.get('DB_MANAGER')
    db_height_cm = db_manager.get_user_height(session.get('user_id')) or 170.0
    
    # Obtener altura efectiva (puede haber una temporal en sesión)
    user_height_cm, is_height_temporary = get_effective_height(db_height_cm)
    
    # Calcular altura de cámara para este segmento
    camera_height_info = get_segment_info_for_ui(segment_type, user_height_cm)
    
    return render_template(
        'components/exercise_selector.html',
        segment_type=segment_type,
        segment_name=segment['name'],
        segment_description=segment['description'],
        segment_icon=segment['icon'],
        exercises=segment['exercises'],
        # Datos para control de altura de cámara
        user_height_cm=user_height_cm,
        is_height_temporary=is_height_temporary,
        camera_height_info=camera_height_info,
        # Datos de sujeto (si hay uno en sesión)
        subject_id=session.get('analysis_subject_id'),
        subject_name=session.get('analysis_subject_name')
    )


# ============================================================================
# ANÁLISIS EN VIVO (NUEVO)
# ============================================================================

@main_bp.route('/segments/<segment_type>/exercises/<exercise_key>')
@login_required
def live_analysis(segment_type, exercise_key):
    """
    Página de análisis en vivo para ejercicios específicos
    
    URL ejemplos:
    - /segments/shoulder/exercises/flexion (Vista perfil)
    - /segments/shoulder/exercises/abduction (Vista frontal)
    - /segments/elbow/exercises/flexion
    - /segments/hip/exercises/flexion
    - /segments/knee/exercises/flexion
    - /segments/ankle/exercises/dorsiflexion
    
    El subject_id se obtiene de la sesión Flask (si hay uno activo)
    """
    
    # Obtener datos de sujeto de la sesión (si existe)
    analysis_subject_id = session.get('analysis_subject_id')
    analysis_subject_name = session.get('analysis_subject_name')
    
    # Verificar disponibilidad de cámara ANTES de renderizar
    available, message = check_camera_availability()
    if not available:
        flash(message, 'warning')
        return redirect(url_for('main.segment_exercises', segment_type=segment_type))
    
    # Configuración completa de ejercicios
    exercises_db = {
        'shoulder': {
            'flexion': {
                'name': 'Flexión de Hombro',
                'description': 'Movimiento del brazo hacia adelante y arriba desde posición neutra',
                'camera_view': 'profile',
                'camera_view_label': 'Perfil',
                'min_angle': 0,
                'max_angle': 180,
                'analyzer_type': 'shoulder_profile',
                'analyzer_class': 'ShoulderProfileAnalyzer',
                'instructions': [
                    'Colócate de PERFIL a la cámara (lado derecho o izquierdo)',
                    'Brazo relajado junto al cuerpo (posición inicial 0°)',
                    'Levanta el brazo hacia ADELANTE lentamente',
                    'Alcanza la máxima altura posible (objetivo: 180°)',
                    'Mantén la posición máxima 2-3 segundos',
                    'Evita inclinar el tronco hacia adelante'
                ],
                'setup': [
                    'Cámara a altura del pecho',
                    'Distancia: 2-3 metros',
                    'Fondo despejado y buena iluminación',
                    'Ropa ajustada que permita ver contorno del brazo'
                ]
            },
            'extension': {
                'name': 'Extensión de Hombro',
                'description': 'Movimiento del brazo hacia atrás desde posición neutra',
                'camera_view': 'profile',
                'camera_view_label': 'Perfil',
                'min_angle': 0,
                'max_angle': 50,
                'analyzer_type': 'shoulder_profile',
                'analyzer_class': 'ShoulderProfileAnalyzer',
                'instructions': [
                    'Colócate de PERFIL a la cámara (lado derecho o izquierdo)',
                    'Brazo relajado junto al cuerpo (posición inicial 0°)',
                    'Lleva el brazo hacia ATRÁS lentamente',
                    'Alcanza la máxima extensión posible (objetivo: 40-50°)',
                    'Mantén la posición máxima 2-3 segundos',
                    'Evita inclinar el tronco hacia adelante o arquear la espalda'
                ],
                'setup': [
                    'Cámara a altura del pecho',
                    'Distancia: 2-3 metros',
                    'Fondo despejado y buena iluminación',
                    'Ropa ajustada que permita ver contorno del brazo'
                ]
            },
            'abduction': {
                'name': 'Abducción de Hombro',
                'description': 'Movimiento bilateral de los brazos hacia los lados',
                'camera_view': 'frontal',
                'camera_view_label': 'Frontal',
                'min_angle': 0,
                'max_angle': 180,
                'analyzer_type': 'shoulder_frontal',
                'analyzer_class': 'ShoulderFrontalAnalyzer',
                'instructions': [
                    'Colócate de FRENTE a la cámara',
                    'Brazos relajados a los lados del cuerpo (0°)',
                    'Levanta AMBOS brazos SIMULTÁNEAMENTE hacia los lados',
                    'Alcanza la máxima altura (objetivo: 180° sobre la cabeza)',
                    'Mantén simetría entre ambos brazos',
                    'Mantén la posición máxima 2-3 segundos'
                ],
                'setup': [
                    'Cámara a altura del pecho',
                    'Distancia: 2-3 metros',
                    'Centrado en el frame',
                    'Fondo despejado y buena iluminación'
                ]
            }
        },
        # Placeholders para otros segmentos (implementar después)
        'elbow': {
            'flexion': {
                'name': 'Flexión de Codo',
                'description': 'Movimiento de cierre del antebrazo hacia el brazo',
                'camera_view': 'profile',
                'camera_view_label': 'Perfil',
                'min_angle': 0,
                'max_angle': 150,
                'analyzer_type': 'elbow_profile',
                'analyzer_class': 'ElbowProfileAnalyzer',
                'instructions': [
                    'Colócate de PERFIL a la cámara',
                    'Brazo extendido junto al cuerpo (0°)',
                    'Flexiona el codo acercando la mano al hombro',
                    'Alcanza la flexión máxima (objetivo: 150°)',
                    'Mantén el hombro estable (no lo muevas)'
                ],
                'setup': [
                    'Cámara a altura del pecho',
                    'Distancia: 2 metros',
                    'Fondo despejado'
                ]
            },
            'extension': {
                'name': 'Extensión de Codo',
                'description': 'Capacidad de extender el brazo completamente (enderezar)',
                'camera_view': 'profile',
                'camera_view_label': 'Perfil',
                'min_angle': 0,    # Extensión completa = 0°
                'max_angle': 10,   # Déficit máximo aceptable
                'analyzer_type': 'elbow_profile',
                'analyzer_class': 'ElbowProfileAnalyzer',
                'instructions': [
                    'Colócate de PERFIL a la cámara',
                    'Comienza con el codo ligeramente flexionado',
                    'Extiende el brazo completamente (intenta que quede recto)',
                    'Objetivo: alcanzar 0° (extensión completa)',
                    'Si pasas de recto (hiperextensión), el sistema lo detectará'
                ],
                'setup': [
                    'Cámara a altura del pecho',
                    'Distancia: 2 metros',
                    'Fondo despejado'
                ]
            }
        },
        # ====== CADERA ======
        'hip': {
            'flexion': {
                'name': 'Flexión de Cadera',
                'description': 'Movimiento de elevación de la pierna hacia adelante',
                'camera_view': 'profile',
                'camera_view_label': 'Perfil',
                'min_angle': 0,
                'max_angle': 135,
                'analyzer_type': 'hip_profile',
                'analyzer_class': 'HipProfileAnalyzer',
                'instructions': [
                    'Colócate de PERFIL a la cámara',
                    'Pierna extendida en posición neutra (0°)',
                    'Levanta la rodilla hacia el pecho',
                    'Alcanza la flexión máxima (objetivo: 135°)',
                    'Mantén la espalda recta'
                ],
                'setup': [
                    'Cámara a altura de la cadera',
                    'Distancia: 2-3 metros',
                    'Usa apoyo si necesitas equilibrio'
                ]
            },
            'extension': {
                'name': 'Extensión de Cadera',
                'description': 'Movimiento de la pierna hacia atrás',
                'camera_view': 'profile',
                'camera_view_label': 'Perfil',
                'min_angle': 0,
                'max_angle': 30,
                'analyzer_type': 'hip_profile',
                'analyzer_class': 'HipProfileAnalyzer',
                'instructions': [
                    'Colócate de PERFIL a la cámara',
                    'Pierna en posición neutra (0°)',
                    'Lleva la pierna hacia atrás sin doblar la rodilla',
                    'Alcanza la extensión máxima (objetivo: 30°)',
                    'Mantén el torso recto, no arquees la espalda'
                ],
                'setup': [
                    'Cámara a altura de la cadera',
                    'Distancia: 2-3 metros',
                    'Usa apoyo frontal para equilibrio'
                ]
            },
            'abduction': {
                'name': 'Abducción de Cadera',
                'description': 'Movimiento de separación lateral de la pierna',
                'camera_view': 'frontal',
                'camera_view_label': 'Frontal',
                'min_angle': 0,
                'max_angle': 45,
                'analyzer_type': 'hip_frontal',
                'analyzer_class': 'HipFrontalAnalyzer',
                'instructions': [
                    'Colócate de FRENTE a la cámara',
                    'Pierna en posición neutra (0°)',
                    'Separa la pierna lateralmente manteniendo la rodilla extendida',
                    'Alcanza la abducción máxima (objetivo: 45°)',
                    'Mantén la pelvis estable'
                ],
                'setup': [
                    'Cámara a altura de la cadera',
                    'Distancia: 2-3 metros',
                    'Usa apoyo lateral para equilibrio'
                ]
            }
        },
        # ====== RODILLA ======
        'knee': {
            'flexion': {
                'name': 'Flexión de Rodilla',
                'description': 'Movimiento de flexión llevando el talón hacia el glúteo',
                'camera_view': 'profile',
                'camera_view_label': 'Perfil',
                'min_angle': 0,
                'max_angle': 150,
                'analyzer_type': 'knee_profile',
                'analyzer_class': 'KneeProfileAnalyzer',
                'instructions': [
                    'Colócate de PERFIL a la cámara',
                    'Pierna extendida en posición neutra (0°)',
                    'Flexiona la rodilla llevando el talón hacia el glúteo',
                    'Alcanza la flexión máxima (objetivo: 135-150°)',
                    'Mantén la cadera estable, no la muevas hacia atrás'
                ],
                'setup': [
                    'Cámara a altura de la rodilla/cadera',
                    'Distancia: 2-3 metros',
                    'Usa apoyo para equilibrio si es necesario'
                ]
            },
            'extension': {
                'name': 'Extensión Terminal de Rodilla',
                'description': 'Capacidad de extender completamente la rodilla (enderezar)',
                'camera_view': 'profile',
                'camera_view_label': 'Perfil',
                'min_angle': 0,    # Extensión completa = 0°
                'max_angle': 10,   # Déficit máximo aceptable
                'analyzer_type': 'knee_profile',
                'analyzer_class': 'KneeProfileAnalyzer',
                'instructions': [
                    'Colócate de PERFIL a la cámara',
                    'Comienza con la rodilla ligeramente flexionada',
                    'Extiende la pierna completamente (intenta que quede recta)',
                    'Objetivo: alcanzar 0° (extensión completa)',
                    'La hiperextensión será detectada automáticamente'
                ],
                'setup': [
                    'Cámara a altura de la rodilla',
                    'Distancia: 2 metros',
                    'Fondo despejado'
                ]
            }
        },
        # ====== TOBILLO ======
        'ankle': {
            'dorsiflexion': {
                'name': 'Dorsiflexión de Tobillo',
                'description': 'Movimiento del pie hacia arriba, acercando los dedos a la espinilla',
                'camera_view': 'profile',
                'camera_view_label': 'Perfil',
                'min_angle': 0,
                'max_angle': 20,
                'analyzer_type': 'ankle_profile',
                'analyzer_class': 'AnkleProfileAnalyzer',
                'instructions': [
                    'Colócate de PERFIL a la cámara',
                    'Pie en posición neutra (90° respecto a la pierna)',
                    'Flexiona el pie hacia arriba llevando los dedos hacia la espinilla',
                    'Alcanza la dorsiflexión máxima (objetivo: 20°)',
                    'Mantén la rodilla estable'
                ],
                'setup': [
                    'Cámara a altura del tobillo/pie',
                    'Distancia: 2 metros',
                    'Asegura que el pie sea visible completamente'
                ]
            },
            'plantarflexion': {
                'name': 'Plantiflexión de Tobillo',
                'description': 'Movimiento del pie hacia abajo, como ponerse de puntillas',
                'camera_view': 'profile',
                'camera_view_label': 'Perfil',
                'min_angle': 0,
                'max_angle': 50,
                'analyzer_type': 'ankle_profile',
                'analyzer_class': 'AnkleProfileAnalyzer',
                'instructions': [
                    'Colócate de PERFIL a la cámara',
                    'Pie en posición neutra (90° respecto a la pierna)',
                    'Extiende el pie hacia abajo como si te pusieras de puntillas',
                    'Alcanza la plantiflexión máxima (objetivo: 50°)',
                    'Mantén la rodilla estable'
                ],
                'setup': [
                    'Cámara a altura del tobillo/pie',
                    'Distancia: 2 metros',
                    'Asegura que el pie sea visible completamente'
                ]
            }
        }
    }
    
    # Validar que exista el segmento
    if segment_type not in exercises_db:
        flash(f'Segmento "{segment_type}" no encontrado', 'error')
        return redirect(url_for('main.segments'))
    
    # Validar que exista el ejercicio
    if exercise_key not in exercises_db[segment_type]:
        flash(f'Ejercicio "{exercise_key}" no encontrado en {segment_type}', 'error')
        return redirect(url_for('main.segment_exercises', segment_type=segment_type))
    
    # Obtener configuración del ejercicio
    exercise = exercises_db[segment_type][exercise_key]
    
    # Obtener información de clasificación ROM (con manejo de errores)
    rom_info = None
    try:
        from app.utils.rom_standards import get_exercise_rom_info
        rom_info = get_exercise_rom_info(segment_type, exercise_key)
    except Exception as e:
        print(f"⚠️ No se pudo cargar ROM info para {segment_type}/{exercise_key}: {e}")
    
    # Guardar en sesión para uso en video_feed
    session['current_segment'] = segment_type
    session['current_exercise'] = exercise_key
    session['analyzer_type'] = exercise['analyzer_type']
    
    # Obtener camera_index de la sesión (default 0)
    camera_index = session.get('camera_index', 0)
    
    # Log para debug
    print(f"\n🎯 LIVE_ANALYSIS RENDER: camera_index={camera_index}, session['camera_index']={session.get('camera_index', 'NO SET')}\n")
    
    # Preparar lista de todos los ejercicios para el dropdown de navegación
    all_exercises_menu = []
    segment_names = {
        'shoulder': 'Hombro',
        'elbow': 'Codo',
        'hip': 'Cadera',
        'knee': 'Rodilla',
        'ankle': 'Tobillo'
    }
    for seg_key, seg_exercises in exercises_db.items():
        segment_info = {
            'key': seg_key,
            'name': segment_names.get(seg_key, seg_key.capitalize()),
            'exercises': []
        }
        for ex_key, ex_data in seg_exercises.items():
            segment_info['exercises'].append({
                'key': ex_key,
                'name': ex_data['name'],
                'view': ex_data['camera_view_label'],
                'is_current': (seg_key == segment_type and ex_key == exercise_key)
            })
        all_exercises_menu.append(segment_info)
    
    return render_template(
        'measurement/live_analysis.html',
        segment_type=segment_type,
        exercise_key=exercise_key,
        exercise_name=exercise['name'],
        exercise_description=exercise['description'],
        camera_view=exercise['camera_view'],
        camera_view_label=exercise['camera_view_label'],
        min_angle=exercise['min_angle'],
        max_angle=exercise['max_angle'],
        instructions=exercise['instructions'],
        setup=exercise['setup'],
        rom_info=rom_info,  # Nueva información de clasificación
        camera_index=camera_index,  # Índice de cámara actual
        all_exercises_menu=all_exercises_menu,  # Menú de todos los ejercicios
        # Datos de sujeto (si hay análisis de sujeto activo)
        analysis_subject_id=analysis_subject_id,
        analysis_subject_name=analysis_subject_name
    )


# ============================================================================
# GESTIÓN DE USUARIOS (Admin)
# ============================================================================

@main_bp.route('/users')
@admin_required
def users():
    """
    Lista de usuarios con paginación y filtros (solo administrador)
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    
    # Obtener parámetros de filtro
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', 'all')
    status_filter = request.args.get('status', 'all')
    
    # Obtener usuarios paginados con estadísticas
    users_data = db_manager.get_users_paginated(
        page=page,
        per_page=10,
        search=search if search else None,
        role_filter=role_filter,
        status_filter=status_filter
    )
    
    return render_template(
        'admin/users.html',
        users=users_data,
        search=search,
        role_filter=role_filter,
        status_filter=status_filter
    )


@main_bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    """
    Vista detallada de un usuario (solo administrador)
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    
    # Obtener detalles completos del usuario
    user_data = db_manager.get_user_detail_for_admin(user_id)
    
    if not user_data:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('main.users'))
    
    return render_template(
        'admin/user_detail.html',
        user=user_data['user'],
        subjects=user_data['subjects'],
        subject_analyses=user_data['subject_analyses'],
        self_analyses=user_data['self_analyses'],
        stats=user_data['stats']
    )


@main_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """
    Activa/desactiva un usuario (solo administrador)
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    
    # No permitir desactivarse a sí mismo
    if user_id == session.get('user_id'):
        flash('No puedes desactivar tu propia cuenta', 'warning')
        return redirect(url_for('main.users'))
    
    result = db_manager.toggle_user_status(user_id)
    
    if result:
        status_text = 'activado' if result['is_active'] else 'desactivado'
        flash(f"Usuario '{result['username']}' {status_text} correctamente", 'success')
    else:
        flash('Usuario no encontrado', 'error')
    
    return redirect(url_for('main.users'))


@main_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """
    Editar información de un usuario (solo administrador)
    """
    
    db_manager = current_app.config.get('DB_MANAGER')
    
    user = db_manager.get_user_by_id(user_id)
    
    if not user:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('main.users'))
    
    if request.method == 'POST':
        # Obtener datos del formulario
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        student_id = request.form.get('student_id', '').strip()
        program = request.form.get('program', '').strip()
        role = request.form.get('role', user.role)
        
        # Actualizar usuario
        updated_user = db_manager.update_user(
            user_id,
            full_name=full_name if full_name else None,
            email=email if email else None,
            student_id=student_id if student_id else None,
            program=program if program else None,
            role=role
        )
        
        if updated_user:
            flash(f"Usuario '{updated_user.username}' actualizado correctamente", 'success')
            return redirect(url_for('main.user_detail', user_id=user_id))
        else:
            flash('Error al actualizar el usuario', 'error')
    
    return render_template(
        'admin/edit_user.html',
        user=user
    )

