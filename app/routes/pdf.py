"""
📄 RUTAS DE GENERACIÓN DE PDF - BIOTRACK
=========================================
Endpoints para generar reportes PDF

Autor: BIOTRACK Team
Fecha: 2025-12-08
"""

from flask import Blueprint, request, send_file, jsonify, session, current_app
from app.routes.auth import login_required, admin_required
from datetime import datetime
import os

pdf_bp = Blueprint('pdf', __name__, url_prefix='/pdf')


@pdf_bp.route('/analysis/<int:analysis_id>')
@login_required
def download_analysis_report(analysis_id):
    """
    Genera y descarga el reporte PDF de un análisis específico
    """
    try:
        from app.services.pdf_service import get_pdf_generator
        
        pdf_gen = get_pdf_generator()
        if not pdf_gen:
            return jsonify({'error': 'Generador de PDF no disponible. Instale: pip install reportlab'}), 500
        
        db_manager = current_app.config.get('DB_MANAGER')
        user_id = session.get('user_id')
        user_role = session.get('role')
        
        # Buscar el análisis (puede ser rom_session o user_analysis_history)
        # Primero intentar rom_session
        analysis = db_manager.get_session_by_id(analysis_id)
        is_subject_analysis = True
        
        if not analysis:
            # Intentar user_analysis_history
            analysis = db_manager.get_user_analysis_by_id(analysis_id)
            is_subject_analysis = False
        
        if not analysis:
            return jsonify({'error': 'Análisis no encontrado'}), 404
        
        # Verificar permisos
        analysis_user_id = analysis.get('user_id') if isinstance(analysis, dict) else analysis.user_id
        if user_role != 'admin' and analysis_user_id != user_id:
            return jsonify({'error': 'No tienes permiso para ver este análisis'}), 403
        
        # Obtener datos del usuario
        user_data = db_manager.get_user_by_id(analysis_user_id)
        user_dict = {
            'username': user_data.username,
            'full_name': user_data.full_name,
            'student_id': user_data.student_id,
            'program': user_data.program
        } if user_data else None
        
        # Obtener datos del sujeto si es análisis de sujeto
        subject_data = None
        if is_subject_analysis:
            subject_id = analysis.get('subject_id') if isinstance(analysis, dict) else analysis.subject_id
            if subject_id:
                subject = db_manager.get_subject_by_id(subject_id)
                if subject:
                    subject_data = {
                        'subject_code': subject.subject_code,
                        'first_name': subject.first_name,
                        'last_name': subject.last_name,
                        'gender': subject.gender,
                        'age': subject.age if hasattr(subject, 'age') else None
                    }
        
        # Convertir análisis a diccionario
        if not isinstance(analysis, dict):
            analysis_dict = {
                'segment': analysis.segment,
                'exercise_name': analysis.exercise_name if hasattr(analysis, 'exercise_name') else analysis.exercise,
                'side': analysis.side,
                'rom_value': analysis.rom_value if hasattr(analysis, 'rom_value') else analysis.rom_max,
                'rom_max': analysis.rom_max if hasattr(analysis, 'rom_max') else None,
                'rom_min': analysis.rom_min if hasattr(analysis, 'rom_min') else None,
                'rom_avg': analysis.rom_avg if hasattr(analysis, 'rom_avg') else None,
                'quality_score': analysis.quality_score if hasattr(analysis, 'quality_score') else analysis.quality,
                'created_at': analysis.created_at if hasattr(analysis, 'created_at') else analysis.analysis_date,
                'notes': analysis.notes if hasattr(analysis, 'notes') else None
            }
        else:
            analysis_dict = analysis
        
        # Generar PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"analisis_{analysis_id}_{timestamp}.pdf"
        
        filepath = pdf_gen.generate_analysis_report(
            analysis_data=analysis_dict,
            user_data=user_dict,
            subject_data=subject_data,
            filename=filename
        )
        
        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except ImportError as e:
        return jsonify({'error': f'Librería no disponible: {str(e)}. Ejecute: pip install reportlab'}), 500
    except Exception as e:
        current_app.logger.error(f"Error generando PDF de análisis: {e}")
        return jsonify({'error': f'Error al generar el reporte: {str(e)}'}), 500


@pdf_bp.route('/history')
@login_required
def download_history_report():
    """
    Genera y descarga el reporte PDF del historial de análisis del usuario
    """
    try:
        from app.services.pdf_service import get_pdf_generator
        
        pdf_gen = get_pdf_generator()
        if not pdf_gen:
            return jsonify({'error': 'Generador de PDF no disponible. Instale: pip install reportlab'}), 500
        
        db_manager = current_app.config.get('DB_MANAGER')
        user_id = session.get('user_id')
        
        # Obtener filtros opcionales
        segment = request.args.get('segment')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        
        # Obtener análisis
        analyses = db_manager.get_user_analysis_history_filtered(
            user_id=user_id,
            segment=segment if segment else None,
            date_from=from_date if from_date else None,
            date_to=to_date if to_date else None
        )
        
        # Obtener datos del usuario
        user = db_manager.get_user_by_id(user_id)
        user_dict = {
            'username': user.username,
            'full_name': user.full_name,
            'student_id': user.student_id,
            'program': user.program
        } if user else {'username': 'Usuario'}
        
        # Generar PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"historial_{user_dict['username']}_{timestamp}.pdf"
        
        filepath = pdf_gen.generate_history_report(
            analyses=analyses,
            user_data=user_dict,
            title="Mi Historial de Análisis",
            filename=filename
        )
        
        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except ImportError as e:
        return jsonify({'error': f'Librería no disponible: {str(e)}'}), 500
    except Exception as e:
        current_app.logger.error(f"Error generando PDF de historial: {e}")
        return jsonify({'error': f'Error al generar el reporte: {str(e)}'}), 500


@pdf_bp.route('/subject/<int:subject_id>')
@login_required
def download_subject_report(subject_id):
    """
    Genera y descarga el reporte PDF de un sujeto con todas sus evaluaciones
    """
    try:
        from app.services.pdf_service import get_pdf_generator
        
        pdf_gen = get_pdf_generator()
        if not pdf_gen:
            return jsonify({'error': 'Generador de PDF no disponible. Instale: pip install reportlab'}), 500
        
        db_manager = current_app.config.get('DB_MANAGER')
        user_id = session.get('user_id')
        user_role = session.get('role')
        
        # Obtener sujeto
        subject = db_manager.get_subject_by_id(subject_id)
        if not subject:
            return jsonify({'error': 'Sujeto no encontrado'}), 404
        
        # Verificar permisos
        if user_role != 'admin' and subject.created_by != user_id:
            return jsonify({'error': 'No tienes permiso para ver este sujeto'}), 403
        
        subject_dict = {
            'subject_code': subject.subject_code,
            'first_name': subject.first_name,
            'last_name': subject.last_name,
            'gender': subject.gender,
            'age': subject.age if hasattr(subject, 'age') else None,
            'height': subject.height if hasattr(subject, 'height') else None,
            'weight': subject.weight if hasattr(subject, 'weight') else None
        }
        
        # Obtener sesiones del sujeto
        sessions = db_manager.get_sessions_by_subject(subject_id)
        
        # Convertir sesiones a diccionarios
        sessions_list = []
        for s in sessions:
            sessions_list.append({
                'segment': s.segment,
                'exercise_name': s.exercise_name,
                'side': s.side,
                'rom_value': s.rom_value,
                'quality_score': s.quality_score,
                'created_at': s.created_at
            })
        
        # Obtener datos del usuario evaluador
        user = db_manager.get_user_by_id(user_id)
        user_dict = {
            'username': user.username,
            'full_name': user.full_name
        } if user else None
        
        # Generar PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"sujeto_{subject.subject_code}_{timestamp}.pdf"
        
        filepath = pdf_gen.generate_subject_report(
            subject_data=subject_dict,
            sessions=sessions_list,
            user_data=user_dict,
            filename=filename
        )
        
        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except ImportError as e:
        return jsonify({'error': f'Librería no disponible: {str(e)}'}), 500
    except Exception as e:
        current_app.logger.error(f"Error generando PDF de sujeto: {e}")
        return jsonify({'error': f'Error al generar el reporte: {str(e)}'}), 500


@pdf_bp.route('/user/<int:target_user_id>/history')
@admin_required
def download_user_history_report(target_user_id):
    """
    [ADMIN] Genera y descarga el reporte PDF del historial de un usuario específico
    """
    try:
        from app.services.pdf_service import get_pdf_generator
        
        pdf_gen = get_pdf_generator()
        if not pdf_gen:
            return jsonify({'error': 'Generador de PDF no disponible'}), 500
        
        db_manager = current_app.config.get('DB_MANAGER')
        
        # Obtener usuario objetivo
        target_user = db_manager.get_user_by_id(target_user_id)
        if not target_user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        user_dict = {
            'username': target_user.username,
            'full_name': target_user.full_name,
            'student_id': target_user.student_id,
            'program': target_user.program
        }
        
        # Obtener todos los análisis del usuario (auto-análisis)
        analyses = db_manager.get_user_analysis_history_filtered(user_id=target_user_id)
        
        # Generar PDF
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"historial_{target_user.username}_{timestamp}.pdf"
        
        filepath = pdf_gen.generate_history_report(
            analyses=analyses,
            user_data=user_dict,
            title=f"Historial de {target_user.full_name or target_user.username}",
            filename=filename
        )
        
        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        current_app.logger.error(f"Error generando PDF: {e}")
        return jsonify({'error': str(e)}), 500
