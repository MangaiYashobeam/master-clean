#!/usr/bin/env python3
"""
🗄️ DATABASE MANAGER - GESTOR DE BASE DE DATOS CON SQLAlchemy
==============================================================
Módulo de gestión de base de datos para BIOTRACK usando SQLAlchemy ORM.
Se conecta a la base de datos existente en database/biotrack.db

CARACTERÍSTICAS:
- SQLAlchemy ORM con modelos para todas las tablas
- Métodos CRUD para User, Subject, ROMSession, AngleMeasurement, SystemLog
- Autenticación de usuarios con Werkzeug
- Consultas específicas del negocio educativo
- Context managers para conexiones seguras
- Sin columna weight en Subject (solo height)

Autor: BIOTRACK Team
Fecha: 2025-11-14
"""

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator
from contextlib import contextmanager

# Zona horaria de Bolivia (UTC-4)
BOLIVIA_TZ = timezone(timedelta(hours=-4))

def get_bolivia_time():
    """Retorna la hora actual en zona horaria de Bolivia (UTC-4)"""
    return datetime.now(BOLIVIA_TZ).replace(tzinfo=None)

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, 
    DateTime, Text, ForeignKey, CheckConstraint, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from werkzeug.security import check_password_hash, generate_password_hash

# ============================================================================
# BASE DE DATOS Y ENGINE
# ============================================================================

Base = declarative_base()


# ============================================================================
# MODELOS ORM (Mapeo de Tablas Existentes)
# ============================================================================

class User(Base):
    """
    Modelo de Usuario (Administradores y Estudiantes)
    Tabla: user
    """
    __tablename__ = 'user'
    
    # Identificación
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Información Personal
    full_name = Column(String(150), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    
    # Información Académica
    role = Column(String(20), nullable=False, default='student')
    student_id = Column(String(50))
    program = Column(String(100))
    semester = Column(Integer)
    
    # Datos Antropométricos (Drillis & Contini)
    height = Column(Float)  # Altura en cm (necesaria para cálculos)
    
    # Estado y Auditoría
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, ForeignKey('user.id'))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relaciones
    subjects = relationship('Subject', back_populates='creator', foreign_keys='Subject.created_by')
    rom_sessions = relationship('ROMSession', back_populates='user', foreign_keys='ROMSession.user_id')
    system_logs = relationship('SystemLog', back_populates='user', foreign_keys='SystemLog.user_id')
    
    # Constraints
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'student')", name='check_role'),
        CheckConstraint("is_active IN (0, 1)", name='check_is_active'),
        CheckConstraint("semester IS NULL OR (semester >= 1 AND semester <= 12)", name='check_semester'),
        CheckConstraint("height IS NULL OR (height >= 50 AND height <= 250)", name='check_height'),
    )
    
    def set_password(self, password: str):
        """Establece el hash de la contraseña"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verifica la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self) -> dict:
        """Convierte el usuario a diccionario"""
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'student_id': self.student_id,
            'program': self.program,
            'semester': self.semester,
            'height': self.height,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Subject(Base):
    """
    Modelo de Sujeto de Estudio
    Tabla: subject
    NOTA: Sin columna weight (solo height)
    """
    __tablename__ = 'subject'
    
    # Identificación
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_code = Column(String(50), unique=True, nullable=False)
    
    # Información Personal
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(DateTime)
    gender = Column(String(10))
    
    # Información Física (SIN weight)
    height = Column(Float)  # Solo altura en cm
    
    # Información Adicional
    activity_level = Column(String(50))
    notes = Column(Text)
    
    # Auditoría
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    creator = relationship('User', back_populates='subjects', foreign_keys=[created_by])
    rom_sessions = relationship('ROMSession', back_populates='subject', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        CheckConstraint("gender IN ('M', 'F', 'Other') OR gender IS NULL", name='check_gender'),
        CheckConstraint("height IS NULL OR (height >= 50 AND height <= 250)", name='check_subject_height'),
        CheckConstraint("activity_level IN ('sedentary', 'light', 'moderate', 'active', 'very_active') OR activity_level IS NULL", name='check_activity_level'),
    )
    
    @property
    def full_name(self) -> str:
        """Nombre completo del sujeto"""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self) -> dict:
        """Convierte el sujeto a diccionario"""
        return {
            'id': self.id,
            'subject_code': self.subject_code,
            'full_name': self.full_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'height': self.height,
            'activity_level': self.activity_level,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<Subject(id={self.id}, code='{self.subject_code}', name='{self.full_name}')>"


class ROMSession(Base):
    """
    Modelo de Sesión de Análisis ROM
    Tabla: rom_session
    """
    __tablename__ = 'rom_session'
    
    # Identificación
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Relaciones
    subject_id = Column(Integer, ForeignKey('subject.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Configuración del Análisis
    segment = Column(String(50), nullable=False)
    exercise_type = Column(String(50), nullable=False)
    camera_view = Column(String(20))
    side = Column(String(20))
    
    # Resultados del Análisis
    max_angle = Column(Float)
    min_angle = Column(Float)
    rom_value = Column(Float)
    repetitions = Column(Integer, default=0)
    duration = Column(Float)
    quality_score = Column(Float)
    
    # Información Adicional
    notes = Column(Text)
    video_path = Column(String(500))
    
    # Auditoría
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relaciones
    subject = relationship('Subject', back_populates='rom_sessions')
    user = relationship('User', back_populates='rom_sessions', foreign_keys=[user_id])
    angle_measurements = relationship('AngleMeasurement', back_populates='session', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        CheckConstraint("segment IN ('ankle', 'knee', 'hip', 'shoulder', 'elbow')", name='check_segment'),
        CheckConstraint("camera_view IN ('lateral', 'frontal', 'posterior') OR camera_view IS NULL", name='check_camera_view'),
        CheckConstraint("side IN ('left', 'right', 'bilateral') OR side IS NULL", name='check_side'),
        CheckConstraint("max_angle IS NULL OR (max_angle >= 0 AND max_angle <= 360)", name='check_max_angle'),
        CheckConstraint("min_angle IS NULL OR (min_angle >= 0 AND min_angle <= 360)", name='check_min_angle'),
        CheckConstraint("rom_value IS NULL OR (rom_value >= 0 AND rom_value <= 360)", name='check_rom_value'),
        CheckConstraint("quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)", name='check_quality_score'),
    )
    
    def to_dict(self) -> dict:
        """Convierte la sesión a diccionario"""
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'user_id': self.user_id,
            'segment': self.segment,
            'exercise_type': self.exercise_type,
            'camera_view': self.camera_view,
            'side': self.side,
            'max_angle': self.max_angle,
            'min_angle': self.min_angle,
            'rom_value': self.rom_value,
            'repetitions': self.repetitions,
            'duration': self.duration,
            'quality_score': self.quality_score,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<ROMSession(id={self.id}, segment='{self.segment}', rom={self.rom_value})>"


class AngleMeasurement(Base):
    """
    Modelo de Medición de Ángulo Frame-by-Frame
    Tabla: angle_measurement
    """
    __tablename__ = 'angle_measurement'
    
    # Identificación
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('rom_session.id'), nullable=False)
    
    # Datos de la Medición
    timestamp = Column(Float, nullable=False)
    frame_number = Column(Integer, nullable=False)
    angle_value = Column(Float, nullable=False)
    confidence = Column(Float)
    landmarks_json = Column(Text)
    
    # Relaciones
    session = relationship('ROMSession', back_populates='angle_measurements')
    
    # Constraints
    __table_args__ = (
        CheckConstraint("angle_value >= 0 AND angle_value <= 360", name='check_angle_value'),
        CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name='check_confidence'),
    )
    
    def to_dict(self) -> dict:
        """Convierte la medición a diccionario"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'timestamp': self.timestamp,
            'frame_number': self.frame_number,
            'angle_value': self.angle_value,
            'confidence': self.confidence
        }
    
    def __repr__(self):
        return f"<AngleMeasurement(id={self.id}, frame={self.frame_number}, angle={self.angle_value})>"


class SystemLog(Base):
    """
    Modelo de Log del Sistema
    Tabla: system_log
    """
    __tablename__ = 'system_log'
    
    # Identificación
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Información del Evento
    user_id = Column(Integer, ForeignKey('user.id'))
    action = Column(String(100), nullable=False)
    details = Column(Text)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relaciones
    user = relationship('User', back_populates='system_logs', foreign_keys=[user_id])
    
    def to_dict(self) -> dict:
        """Convierte el log a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'details': self.details,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, action='{self.action}')>"


class UserAnalysisHistory(Base):
    """
    Modelo de Historial de Análisis del Usuario
    Tabla: user_analysis_history
    
    Para cuando el usuario se analiza a sí mismo (no a un sujeto externo)
    """
    __tablename__ = 'user_analysis_history'
    
    # Identificación
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Configuración del Análisis
    segment = Column(String(50), nullable=False)
    exercise_type = Column(String(50), nullable=False)
    camera_view = Column(String(20))
    side = Column(String(20))
    
    # Resultados del Análisis
    rom_value = Column(Float, nullable=False)
    left_rom = Column(Float)
    right_rom = Column(Float)
    quality_score = Column(Float)
    classification = Column(String(50))
    
    # Metadatos
    duration = Column(Float)
    samples_collected = Column(Integer)
    plateau_detected = Column(Boolean, default=False)
    
    # Auditoría - Usa hora de Bolivia (UTC-4)
    created_at = Column(DateTime, nullable=False, default=get_bolivia_time)
    
    # Relaciones
    user = relationship('User', backref='analysis_history')
    
    def to_dict(self) -> dict:
        """Convierte a diccionario"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'segment': self.segment,
            'exercise_type': self.exercise_type,
            'camera_view': self.camera_view,
            'side': self.side,
            'rom_value': round(self.rom_value, 1) if self.rom_value else 0,
            'left_rom': round(self.left_rom, 1) if self.left_rom else None,
            'right_rom': round(self.right_rom, 1) if self.right_rom else None,
            'quality_score': round(self.quality_score, 1) if self.quality_score else None,
            'classification': self.classification,
            'duration': round(self.duration, 1) if self.duration else None,
            'samples_collected': self.samples_collected,
            'plateau_detected': self.plateau_detected,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # Campos formateados para display
            'date': self.created_at.strftime('%d/%m/%Y') if self.created_at else None,
            'time': self.created_at.strftime('%H:%M') if self.created_at else None
        }
    
    def __repr__(self):
        return f"<UserAnalysisHistory(id={self.id}, segment='{self.segment}', rom={self.rom_value})>"


# ============================================================================
# DATABASE MANAGER CLASS
# ============================================================================

class DatabaseManager:
    """
    Gestor de Base de Datos con SQLAlchemy
    
    Proporciona métodos para:
    - Conexión a la BD existente
    - Operaciones CRUD para todas las tablas
    - Autenticación de usuarios
    - Consultas específicas del negocio
    - Context managers para sesiones seguras
    """
    
    def __init__(self, db_path: str = 'database/biotrack.db'):
        """
        Inicializa el gestor de base de datos
        
        Args:
            db_path: Ruta a la base de datos SQLite
        """
        self.db_path = db_path
        
        # Verificar que la BD existe
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Base de datos no encontrada: {db_path}")
        
        # Crear engine
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        
        # Crear sesión
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager para sesiones de BD
        
        Uso:
            with db_manager.get_session() as session:
                user = session.query(User).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # ========================================================================
    # MÉTODOS DE AUTENTICACIÓN
    # ========================================================================
    
    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """
        Autentica un usuario
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            
        Returns:
            Diccionario con datos del usuario si las credenciales son correctas, None en caso contrario
        """
        with self.get_session() as session:
            user = session.query(User).filter_by(username=username).first()
            
            if user and user.check_password(password):
                # Actualizar last_login
                user.last_login = datetime.utcnow()
                session.commit()
                
                # Retornar datos del usuario como diccionario para evitar DetachedInstanceError
                return {
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'role': user.role,
                    'email': user.email,
                    'is_active': user.is_active
                }
            
            return None
    
    def update_last_login(self, user_id: int):
        """Actualiza la fecha de último login"""
        with self.get_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
    
    # ========================================================================
    # MÉTODOS CRUD - USER
    # ========================================================================
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene un usuario por ID"""
        with self.get_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                # Forzar carga de todos los atributos antes de cerrar sesión
                session.expunge(user)
                from sqlalchemy.orm import make_transient
                make_transient(user)
            return user
    
    def get_user_height(self, user_id: int) -> Optional[float]:
        """
        Obtiene la altura del usuario por ID.
        Método optimizado que solo obtiene el campo height.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Altura en cm o None si no existe el usuario o no tiene altura
        """
        with self.get_session() as session:
            result = session.query(User.height).filter_by(id=user_id).first()
            return result[0] if result else None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Obtiene un usuario por username"""
        with self.get_session() as session:
            return session.query(User).filter_by(username=username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por email"""
        with self.get_session() as session:
            return session.query(User).filter_by(email=email).first()
    
    def create_user(self, username: str, password: str, full_name: str, email: str,
                   role: str = 'student', **kwargs) -> User:
        """
        Crea un nuevo usuario
        
        Args:
            username: Nombre de usuario único
            password: Contraseña (se hasheará)
            full_name: Nombre completo
            email: Email único
            role: 'admin' o 'student'
            **kwargs: Campos opcionales (student_id, program, semester, height, created_by)
        
        Returns:
            Usuario creado
        """
        with self.get_session() as session:
            user = User(
                username=username,
                full_name=full_name,
                email=email,
                role=role,
                **kwargs
            )
            user.set_password(password)
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            return user
    
    def get_all_users(self, role: Optional[str] = None, active_only: bool = True) -> List[User]:
        """
        Obtiene todos los usuarios
        
        Args:
            role: Filtrar por rol ('admin', 'student', None para todos)
            active_only: Solo usuarios activos
        
        Returns:
            Lista de usuarios
        """
        with self.get_session() as session:
            query = session.query(User)
            
            if role:
                query = query.filter_by(role=role)
            
            if active_only:
                query = query.filter_by(is_active=True)
            
            return query.all()
    
    def get_students(self, active_only: bool = True) -> List[User]:
        """Obtiene todos los estudiantes"""
        return self.get_all_users(role='student', active_only=active_only)
    
    def get_users_paginated(
        self, 
        page: int = 1, 
        per_page: int = 10, 
        search: str = None,
        role_filter: str = None,
        status_filter: str = None
    ) -> Dict[str, Any]:
        """
        Obtiene usuarios con paginación y filtros
        
        Args:
            page: Número de página
            per_page: Usuarios por página
            search: Búsqueda por username, full_name, email
            role_filter: Filtrar por rol ('admin', 'student', 'all')
            status_filter: Filtrar por estado ('active', 'inactive', 'all')
        
        Returns:
            Diccionario con items, page, pages, total, has_prev, has_next
        """
        with self.get_session() as session:
            query = session.query(User)
            
            # Aplicar filtros
            if search:
                search_term = f'%{search}%'
                query = query.filter(
                    (User.username.ilike(search_term)) |
                    (User.full_name.ilike(search_term)) |
                    (User.email.ilike(search_term)) |
                    (User.student_id.ilike(search_term))
                )
            
            if role_filter and role_filter != 'all':
                query = query.filter(User.role == role_filter)
            
            if status_filter == 'active':
                query = query.filter(User.is_active == True)
            elif status_filter == 'inactive':
                query = query.filter(User.is_active == False)
            
            # Contar total
            total = query.count()
            
            # Calcular páginas
            pages = (total + per_page - 1) // per_page if total > 0 else 1
            page = max(1, min(page, pages))
            
            # Obtener usuarios de la página actual
            users = query.order_by(User.created_at.desc())\
                        .offset((page - 1) * per_page)\
                        .limit(per_page)\
                        .all()
            
            # Convertir a diccionarios con estadísticas adicionales
            users_with_stats = []
            for user in users:
                # Contar sujetos del usuario
                subjects_count = session.query(func.count(Subject.id))\
                    .filter(Subject.created_by == user.id).scalar() or 0
                
                # Contar análisis de sujetos (rom_session)
                sessions_count = session.query(func.count(ROMSession.id))\
                    .filter(ROMSession.user_id == user.id).scalar() or 0
                
                # Contar auto-análisis (user_analysis_history)
                self_analyses = session.query(func.count(UserAnalysisHistory.id))\
                    .filter(UserAnalysisHistory.user_id == user.id).scalar() or 0
                
                users_with_stats.append({
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'email': user.email,
                    'student_id': user.student_id,
                    'program': user.program,
                    'role': user.role,
                    'is_active': user.is_active,
                    'last_login': user.last_login,
                    'created_at': user.created_at,
                    'birth_date': user.birth_date,
                    'subjects_count': subjects_count,
                    'sessions_count': sessions_count,
                    'self_analyses_count': self_analyses,
                    'total_analyses': sessions_count + self_analyses
                })
            
            return {
                'items': users_with_stats,
                'page': page,
                'pages': pages,
                'total': total,
                'per_page': per_page,
                'has_prev': page > 1,
                'has_next': page < pages,
                'prev_num': page - 1 if page > 1 else None,
                'next_num': page + 1 if page < pages else None
            }
    
    def get_user_detail_for_admin(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene detalles completos de un usuario para vista admin
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Diccionario con toda la info del usuario, sujetos, análisis, estadísticas
        """
        with self.get_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return None
            
            # Obtener sujetos del usuario
            subjects = session.query(Subject).filter_by(created_by=user_id).all()
            subjects_list = [{
                'id': s.id,
                'subject_code': s.subject_code,
                'full_name': f"{s.first_name} {s.last_name}",
                'gender': s.gender,
                'sessions_count': session.query(func.count(ROMSession.id)).filter_by(subject_id=s.id).scalar() or 0,
                'created_at': s.created_at
            } for s in subjects]
            
            # Obtener análisis de sujetos (últimos 20)
            subject_analyses = session.query(ROMSession)\
                .filter(ROMSession.user_id == user_id)\
                .order_by(ROMSession.created_at.desc())\
                .limit(20).all()
            
            subject_analyses_list = [{
                'id': a.id,
                'subject_name': f"{a.subject.first_name} {a.subject.last_name}" if a.subject else 'N/A',
                'segment': a.segment,
                'exercise': a.exercise_name,
                'side': a.side,
                'rom_value': a.rom_value,
                'quality_score': a.quality_score,
                'created_at': a.created_at
            } for a in subject_analyses]
            
            # Obtener auto-análisis (últimos 20)
            self_analyses = session.query(UserAnalysisHistory)\
                .filter(UserAnalysisHistory.user_id == user_id)\
                .order_by(UserAnalysisHistory.analysis_date.desc())\
                .limit(20).all()
            
            self_analyses_list = [{
                'id': a.id,
                'segment': a.segment,
                'exercise': a.exercise_name,
                'side': a.side,
                'rom_max': a.rom_max,
                'quality': a.quality,
                'analysis_date': a.analysis_date
            } for a in self_analyses]
            
            # Estadísticas del usuario
            total_subjects = len(subjects)
            total_subject_analyses = session.query(func.count(ROMSession.id))\
                .filter(ROMSession.user_id == user_id).scalar() or 0
            total_self_analyses = session.query(func.count(UserAnalysisHistory.id))\
                .filter(UserAnalysisHistory.user_id == user_id).scalar() or 0
            
            avg_quality = session.query(func.avg(ROMSession.quality_score))\
                .filter(ROMSession.user_id == user_id).scalar()
            
            # Análisis por segmento
            segment_stats = session.query(
                UserAnalysisHistory.segment,
                func.count(UserAnalysisHistory.id).label('count')
            ).filter(UserAnalysisHistory.user_id == user_id)\
             .group_by(UserAnalysisHistory.segment).all()
            
            segment_names = {
                'shoulder': 'Hombro',
                'elbow': 'Codo',
                'hip': 'Cadera',
                'knee': 'Rodilla',
                'ankle': 'Tobillo'
            }
            
            segment_breakdown = [{
                'key': s.segment,
                'name': segment_names.get(s.segment, s.segment),
                'count': s.count
            } for s in segment_stats]
            
            return {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'email': user.email,
                    'student_id': user.student_id,
                    'program': user.program,
                    'role': user.role,
                    'is_active': user.is_active,
                    'last_login': user.last_login,
                    'created_at': user.created_at,
                    'birth_date': user.birth_date
                },
                'subjects': subjects_list,
                'subject_analyses': subject_analyses_list,
                'self_analyses': self_analyses_list,
                'stats': {
                    'total_subjects': total_subjects,
                    'total_subject_analyses': total_subject_analyses,
                    'total_self_analyses': total_self_analyses,
                    'total_analyses': total_subject_analyses + total_self_analyses,
                    'avg_quality': round(avg_quality, 2) if avg_quality else 0,
                    'segment_breakdown': segment_breakdown
                }
            }
    
    def toggle_user_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Cambia el estado activo/inactivo de un usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Diccionario con nuevo estado o None si no existe
        """
        with self.get_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return None
            
            user.is_active = not user.is_active
            session.commit()
            
            return {
                'id': user.id,
                'username': user.username,
                'is_active': user.is_active,
                'status': 'active' if user.is_active else 'inactive'
            }
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Actualiza un usuario"""
        with self.get_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                session.commit()
                session.refresh(user)
            
            return user
    
    def delete_user(self, user_id: int) -> bool:
        """Elimina (desactiva) un usuario"""
        with self.get_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            
            if user:
                user.is_active = False
                session.commit()
                return True
            
            return False
    
    # ========================================================================
    # MÉTODOS CRUD - SUBJECT
    # ========================================================================
    
    def create_subject(self, subject_code: str, first_name: str, last_name: str,
                      created_by: int, **kwargs) -> Subject:
        """
        Crea un nuevo sujeto de estudio
        
        Args:
            subject_code: Código único (ej: SUJ-2024-0001)
            first_name: Nombre
            last_name: Apellido
            created_by: ID del usuario que crea el sujeto
            **kwargs: Campos opcionales (date_of_birth, gender, height, activity_level, notes)
        
        Returns:
            Sujeto creado
        """
        with self.get_session() as session:
            subject = Subject(
                subject_code=subject_code,
                first_name=first_name,
                last_name=last_name,
                created_by=created_by,
                **kwargs
            )
            
            session.add(subject)
            session.commit()
            session.refresh(subject)
            
            return subject
    
    def get_subject_by_id(self, subject_id: int) -> Optional[Subject]:
        """Obtiene un sujeto por ID"""
        with self.get_session() as session:
            return session.query(Subject).filter_by(id=subject_id).first()
    
    def get_subject_by_code(self, subject_code: str) -> Optional[Subject]:
        """Obtiene un sujeto por código"""
        with self.get_session() as session:
            return session.query(Subject).filter_by(subject_code=subject_code).first()
    
    def get_subjects_by_user(self, user_id: int) -> List[dict]:
        """
        Obtiene todos los sujetos creados por un usuario
        
        Args:
            user_id: ID del usuario creador
            
        Returns:
            Lista de diccionarios con datos de los sujetos
        """
        with self.get_session() as session:
            subjects = session.query(Subject).filter_by(created_by=user_id).order_by(Subject.created_at.desc()).all()
            return [s.to_dict() for s in subjects]
    
    def get_all_subjects(self) -> List[dict]:
        """
        Obtiene todos los sujetos (para admin)
        
        Returns:
            Lista de diccionarios con datos de los sujetos
        """
        with self.get_session() as session:
            subjects = session.query(Subject).order_by(Subject.created_at.desc()).all()
            return [s.to_dict() for s in subjects]
    
    def get_all_subjects_with_creator(self) -> List[dict]:
        """
        Obtiene todos los sujetos con información del creador (para admin)
        
        Returns:
            Lista de diccionarios con datos de los sujetos y su creador
        """
        with self.get_session() as session:
            subjects = session.query(Subject).order_by(Subject.created_at.desc()).all()
            result = []
            for s in subjects:
                subject_dict = s.to_dict()
                # Agregar info del creador
                if s.creator:
                    subject_dict['creator_name'] = s.creator.full_name
                    subject_dict['creator_username'] = s.creator.username
                else:
                    subject_dict['creator_name'] = 'Desconocido'
                    subject_dict['creator_username'] = None
                result.append(subject_dict)
            return result
    
    def get_subject_by_id_safe(self, subject_id: int) -> Optional[dict]:
        """
        Obtiene un sujeto por ID (retorna diccionario)
        
        Args:
            subject_id: ID del sujeto
            
        Returns:
            Diccionario con datos del sujeto o None
        """
        with self.get_session() as session:
            subject = session.query(Subject).filter_by(id=subject_id).first()
            if subject:
                subject_dict = subject.to_dict()
                subject_dict['created_by'] = subject.created_by
                if subject.creator:
                    subject_dict['creator_name'] = subject.creator.full_name
                return subject_dict
            return None
    
    def generate_subject_code(self) -> str:
        """
        Genera un código único para un nuevo sujeto
        Formato: SUJ-YYYY-NNNN
        
        Returns:
            Código único para el sujeto
        """
        import datetime
        year = datetime.datetime.now().year
        
        with self.get_session() as session:
            # Buscar el último código del año actual
            last_subject = session.query(Subject).filter(
                Subject.subject_code.like(f'SUJ-{year}-%')
            ).order_by(Subject.subject_code.desc()).first()
            
            if last_subject:
                # Extraer el número y sumar 1
                try:
                    last_num = int(last_subject.subject_code.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            return f"SUJ-{year}-{new_num:04d}"
    
    def can_user_access_subject(self, user_id: int, subject_id: int, user_role: str) -> bool:
        """
        Verifica si un usuario puede acceder a un sujeto
        
        Args:
            user_id: ID del usuario
            subject_id: ID del sujeto
            user_role: Rol del usuario ('admin' o 'student')
            
        Returns:
            True si tiene acceso, False si no
        """
        if user_role == 'admin':
            return True
        
        with self.get_session() as session:
            subject = session.query(Subject).filter_by(id=subject_id).first()
            if subject:
                return subject.created_by == user_id
            return False
    
    def can_user_modify_subject(self, user_id: int, subject_id: int, user_role: str) -> bool:
        """
        Verifica si un usuario puede modificar/eliminar un sujeto
        Admin puede modificar todos, estudiantes solo los suyos
        
        Args:
            user_id: ID del usuario
            subject_id: ID del sujeto
            user_role: Rol del usuario
            
        Returns:
            True si puede modificar, False si no
        """
        return self.can_user_access_subject(user_id, subject_id, user_role)
    
    def get_subjects_count_by_user(self, user_id: int) -> int:
        """
        Cuenta los sujetos creados por un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Número de sujetos
        """
        with self.get_session() as session:
            return session.query(Subject).filter_by(created_by=user_id).count()
    
    def get_total_subjects_count(self) -> int:
        """
        Cuenta el total de sujetos en el sistema
        
        Returns:
            Número total de sujetos
        """
        with self.get_session() as session:
            return session.query(Subject).count()
    
    def update_subject(self, subject_id: int, **kwargs) -> Optional[Subject]:
        """Actualiza un sujeto"""
        with self.get_session() as session:
            subject = session.query(Subject).filter_by(id=subject_id).first()
            
            if subject:
                for key, value in kwargs.items():
                    if hasattr(subject, key):
                        setattr(subject, key, value)
                
                subject.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(subject)
            
            return subject
    
    def delete_subject(self, subject_id: int) -> bool:
        """Elimina un sujeto (y sus sesiones en cascada)"""
        with self.get_session() as session:
            subject = session.query(Subject).filter_by(id=subject_id).first()
            
            if subject:
                session.delete(subject)
                session.commit()
                return True
            
            return False
    
    # ========================================================================
    # MÉTODOS CRUD - ROM SESSION
    # ========================================================================
    
    def create_rom_session(self, subject_id: int, user_id: int, segment: str,
                          exercise_type: str, **kwargs) -> dict:
        """
        Crea una nueva sesión de análisis ROM
        
        Args:
            subject_id: ID del sujeto analizado
            user_id: ID del estudiante que realiza el análisis
            segment: Segmento corporal ('ankle', 'knee', 'hip', 'shoulder', 'elbow')
            exercise_type: Tipo de movimiento
            **kwargs: Campos opcionales (camera_view, side, max_angle, etc.)
        
        Returns:
            Diccionario con datos de la sesión ROM creada
        """
        with self.get_session() as session:
            rom_session = ROMSession(
                subject_id=subject_id,
                user_id=user_id,
                segment=segment,
                exercise_type=exercise_type,
                **kwargs
            )
            
            session.add(rom_session)
            session.commit()
            session.refresh(rom_session)
            
            # Retornar diccionario para evitar "detached instance" error
            return rom_session.to_dict()
    
    def get_rom_session_by_id(self, session_id: int) -> Optional[ROMSession]:
        """Obtiene una sesión ROM por ID"""
        with self.get_session() as session:
            return session.query(ROMSession).filter_by(id=session_id).first()
    
    def get_sessions_by_user(self, user_id: int) -> List[dict]:
        """
        Obtiene todas las sesiones de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de diccionarios con datos de las sesiones
        """
        with self.get_session() as session:
            sessions = session.query(ROMSession).filter_by(user_id=user_id).order_by(ROMSession.created_at.desc()).all()
            return [s.to_dict() for s in sessions]
    
    def get_sessions_by_subject(self, subject_id: int) -> List[dict]:
        """
        Obtiene todas las sesiones de un sujeto
        
        Args:
            subject_id: ID del sujeto
            
        Returns:
            Lista de diccionarios con datos de las sesiones
        """
        with self.get_session() as session:
            sessions = session.query(ROMSession).filter_by(subject_id=subject_id).order_by(ROMSession.created_at.desc()).all()
            return [s.to_dict() for s in sessions]
    
    def get_sessions_by_segment(self, segment: str) -> List[ROMSession]:
        """Obtiene sesiones por segmento corporal"""
        with self.get_session() as session:
            return session.query(ROMSession).filter_by(segment=segment).all()
    
    def update_rom_session(self, session_id: int, **kwargs) -> Optional[ROMSession]:
        """Actualiza una sesión ROM"""
        with self.get_session() as session:
            rom_session = session.query(ROMSession).filter_by(id=session_id).first()
            
            if rom_session:
                for key, value in kwargs.items():
                    if hasattr(rom_session, key):
                        setattr(rom_session, key, value)
                
                session.commit()
                session.refresh(rom_session)
            
            return rom_session
    
    def delete_rom_session(self, session_id: int) -> bool:
        """Elimina una sesión ROM"""
        with self.get_session() as session:
            rom_session = session.query(ROMSession).filter_by(id=session_id).first()
            
            if rom_session:
                session.delete(rom_session)
                session.commit()
                return True
            
            return False
    
    # ========================================================================
    # MÉTODOS CRUD - ANGLE MEASUREMENT
    # ========================================================================
    
    def add_angle_measurement(self, session_id: int, timestamp: float, frame_number: int,
                             angle_value: float, confidence: Optional[float] = None,
                             landmarks_json: Optional[str] = None) -> AngleMeasurement:
        """Agrega una medición de ángulo a una sesión"""
        with self.get_session() as session:
            measurement = AngleMeasurement(
                session_id=session_id,
                timestamp=timestamp,
                frame_number=frame_number,
                angle_value=angle_value,
                confidence=confidence,
                landmarks_json=landmarks_json
            )
            
            session.add(measurement)
            session.commit()
            session.refresh(measurement)
            
            return measurement
    
    def get_measurements_by_session(self, session_id: int) -> List[AngleMeasurement]:
        """Obtiene todas las mediciones de una sesión"""
        with self.get_session() as session:
            return session.query(AngleMeasurement).filter_by(session_id=session_id).order_by(AngleMeasurement.frame_number).all()
    
    # ========================================================================
    # MÉTODOS CRUD - SYSTEM LOG
    # ========================================================================
    
    def log_action(self, action: str, user_id: Optional[int] = None,
                  details: Optional[str] = None, ip_address: Optional[str] = None) -> SystemLog:
        """
        Registra una acción en el sistema
        
        Args:
            action: Tipo de acción ('login', 'logout', 'create_subject', etc.)
            user_id: ID del usuario (None para eventos del sistema)
            details: Detalles adicionales
            ip_address: IP del cliente
        
        Returns:
            Log creado
        """
        with self.get_session() as session:
            log = SystemLog(
                action=action,
                user_id=user_id,
                details=details,
                ip_address=ip_address
            )
            
            session.add(log)
            session.commit()
            session.refresh(log)
            
            return log
    
    def get_logs_by_user(self, user_id: int, limit: int = 100) -> List[SystemLog]:
        """Obtiene los logs de un usuario"""
        with self.get_session() as session:
            return session.query(SystemLog).filter_by(user_id=user_id).order_by(SystemLog.timestamp.desc()).limit(limit).all()
    
    def get_recent_logs(self, limit: int = 100) -> List[SystemLog]:
        """Obtiene los logs más recientes del sistema"""
        with self.get_session() as session:
            return session.query(SystemLog).order_by(SystemLog.timestamp.desc()).limit(limit).all()
    
    # ========================================================================
    # MÉTODOS ESTADÍSTICOS Y DE NEGOCIO
    # ========================================================================
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene estadísticas de un usuario estudiante
        
        Returns:
            Diccionario con estadísticas (sujetos registrados, sesiones, avg quality, etc.)
        """
        with self.get_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return {}
            
            subjects_count = session.query(func.count(Subject.id)).filter_by(created_by=user_id).scalar()
            sessions_count = session.query(func.count(ROMSession.id)).filter_by(user_id=user_id).scalar()
            avg_quality = session.query(func.avg(ROMSession.quality_score)).filter_by(user_id=user_id).scalar()
            
            last_session = session.query(ROMSession).filter_by(user_id=user_id).order_by(ROMSession.created_at.desc()).first()
            
            return {
                'user_id': user_id,
                'full_name': user.full_name,
                'student_id': user.student_id,
                'program': user.program,
                'subjects_registered': subjects_count or 0,
                'sessions_performed': sessions_count or 0,
                'avg_quality_score': round(avg_quality, 2) if avg_quality else 0,
                'last_activity': last_session.created_at.isoformat() if last_session else None
            }
    
    def get_segment_statistics(self, segment: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de un segmento corporal
        
        Args:
            segment: 'ankle', 'knee', 'hip', 'shoulder', 'elbow'
        
        Returns:
            Estadísticas del segmento
        """
        with self.get_session() as session:
            sessions = session.query(ROMSession).filter_by(segment=segment).filter(ROMSession.rom_value.isnot(None)).all()
            
            if not sessions:
                return {'segment': segment, 'total_sessions': 0}
            
            rom_values = [s.rom_value for s in sessions]
            
            return {
                'segment': segment,
                'total_sessions': len(sessions),
                'avg_rom': round(sum(rom_values) / len(rom_values), 2),
                'min_rom': min(rom_values),
                'max_rom': max(rom_values)
            }
    
    def search_subjects(self, query: str) -> List[Subject]:
        """
        Busca sujetos por nombre o código
        
        Args:
            query: Texto a buscar
        
        Returns:
            Lista de sujetos que coinciden
        """
        with self.get_session() as session:
            return session.query(Subject).filter(
                (Subject.first_name.like(f'%{query}%')) |
                (Subject.last_name.like(f'%{query}%')) |
                (Subject.subject_code.like(f'%{query}%'))
            ).all()
    
    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================
    
    def test_connection(self) -> bool:
        """Verifica la conexión a la base de datos"""
        try:
            with self.get_session() as session:
                session.query(User).first()
            return True
        except Exception as e:
            print(f"Error de conexión: {e}")
            return False
    
    # ========================================================================
    # MÉTODOS CRUD - USER ANALYSIS HISTORY
    # ========================================================================
    
    def save_analysis_to_history(
        self,
        user_id: int,
        data: Dict[str, Any]
    ) -> UserAnalysisHistory:
        """
        Guarda un análisis del usuario en el historial.
        
        Args:
            user_id: ID del usuario
            data: Diccionario con los datos del análisis
                - segment: Segmento corporal
                - exercise_type: Tipo de ejercicio
                - rom_value: Valor ROM principal
                - camera_view: Vista de cámara (profile/frontal)
                - side: Lado (left/right/bilateral)
                - left_rom: ROM lado izquierdo (para bilateral)
                - right_rom: ROM lado derecho (para bilateral)
                - quality_score: Calidad de medición (0-100)
                - classification: Clasificación del resultado
                - duration: Duración del análisis
                - notes: Notas opcionales
        
        Returns:
            Registro creado o diccionario con el ID
        """
        with self.get_session() as session:
            analysis = UserAnalysisHistory(
                user_id=user_id,
                segment=data.get('segment', ''),
                exercise_type=data.get('exercise_type', ''),
                rom_value=data.get('rom_value', 0),
                camera_view=data.get('camera_view'),
                side=data.get('side'),
                left_rom=data.get('left_rom'),
                right_rom=data.get('right_rom'),
                quality_score=data.get('quality_score'),
                classification=data.get('classification'),
                duration=data.get('duration')
            )
            
            session.add(analysis)
            session.commit()
            
            # Obtener el ID antes de cerrar la sesión
            analysis_id = analysis.id
            
            # Retornar diccionario en lugar del objeto (evita error de sesión)
            return {'id': analysis_id, 'success': True}
    
    def save_user_analysis(
        self,
        user_id: int,
        segment: str,
        exercise_type: str,
        rom_value: float,
        camera_view: str = None,
        side: str = None,
        left_rom: float = None,
        right_rom: float = None,
        quality_score: float = None,
        classification: str = None,
        duration: float = None,
        samples_collected: int = None,
        plateau_detected: bool = False
    ) -> UserAnalysisHistory:
        """
        Guarda un análisis del usuario en el historial.
        
        Args:
            user_id: ID del usuario
            segment: Segmento corporal
            exercise_type: Tipo de ejercicio
            rom_value: Valor ROM principal
            camera_view: Vista de cámara (profile/frontal)
            side: Lado (left/right/bilateral)
            left_rom: ROM lado izquierdo (para bilateral)
            right_rom: ROM lado derecho (para bilateral)
            quality_score: Calidad de medición (0-100)
            classification: Clasificación del resultado
            duration: Duración del análisis
            samples_collected: Muestras recolectadas
            plateau_detected: Si se detectó meseta
        
        Returns:
            Registro creado
        """
        with self.get_session() as session:
            analysis = UserAnalysisHistory(
                user_id=user_id,
                segment=segment,
                exercise_type=exercise_type,
                rom_value=rom_value,
                camera_view=camera_view,
                side=side,
                left_rom=left_rom,
                right_rom=right_rom,
                quality_score=quality_score,
                classification=classification,
                duration=duration,
                samples_collected=samples_collected,
                plateau_detected=plateau_detected
            )
            
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            
            return analysis
    
    def get_user_analysis_history(
        self,
        user_id: int,
        segment: str = None,
        exercise_type: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de análisis de un usuario.
        
        Args:
            user_id: ID del usuario
            segment: Filtrar por segmento (opcional)
            exercise_type: Filtrar por ejercicio (opcional)
            limit: Máximo de registros a retornar
        
        Returns:
            Lista de análisis como diccionarios
        """
        with self.get_session() as session:
            query = session.query(UserAnalysisHistory).filter_by(user_id=user_id)
            
            if segment:
                query = query.filter_by(segment=segment)
            
            if exercise_type:
                query = query.filter_by(exercise_type=exercise_type)
            
            records = query.order_by(UserAnalysisHistory.created_at.desc()).limit(limit).all()
            
            return [record.to_dict() for record in records]
    
    def get_user_analysis_history_filtered(
        self,
        user_id: int,
        segment: str = None,
        exercise_type: str = None,
        date_from: str = None,
        date_to: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de análisis de un usuario con filtros avanzados.
        
        Args:
            user_id: ID del usuario
            segment: Filtrar por segmento (opcional)
            exercise_type: Filtrar por ejercicio (opcional)
            date_from: Fecha desde (formato YYYY-MM-DD) (opcional)
            date_to: Fecha hasta (formato YYYY-MM-DD) (opcional)
            limit: Máximo de registros a retornar
        
        Returns:
            Lista de análisis como diccionarios
        """
        with self.get_session() as session:
            query = session.query(UserAnalysisHistory).filter_by(user_id=user_id)
            
            if segment:
                query = query.filter_by(segment=segment)
            
            if exercise_type:
                query = query.filter_by(exercise_type=exercise_type)
            
            if date_from:
                try:
                    from datetime import datetime
                    date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
                    query = query.filter(UserAnalysisHistory.created_at >= date_from_dt)
                except ValueError:
                    pass
            
            if date_to:
                try:
                    from datetime import datetime, timedelta
                    date_to_dt = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                    query = query.filter(UserAnalysisHistory.created_at < date_to_dt)
                except ValueError:
                    pass
            
            records = query.order_by(UserAnalysisHistory.created_at.desc()).limit(limit).all()
            
            return [record.to_dict() for record in records]
    
    def count_user_analysis_history(
        self,
        user_id: int,
        segment: str = None,
        exercise_type: str = None,
        date_from: str = None,
        date_to: str = None
    ) -> int:
        """
        Cuenta el total de análisis de un usuario con filtros.
        
        Args:
            user_id: ID del usuario
            segment: Filtrar por segmento (opcional)
            exercise_type: Filtrar por ejercicio (opcional)
            date_from: Fecha desde (formato YYYY-MM-DD) (opcional)
            date_to: Fecha hasta (formato YYYY-MM-DD) (opcional)
        
        Returns:
            Número total de análisis
        """
        with self.get_session() as session:
            query = session.query(func.count(UserAnalysisHistory.id)).filter_by(user_id=user_id)
            
            if segment:
                query = query.filter(UserAnalysisHistory.segment == segment)
            
            if exercise_type:
                query = query.filter(UserAnalysisHistory.exercise_type == exercise_type)
            
            if date_from:
                try:
                    from datetime import datetime
                    date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
                    query = query.filter(UserAnalysisHistory.created_at >= date_from_dt)
                except ValueError:
                    pass
            
            if date_to:
                try:
                    from datetime import datetime, timedelta
                    date_to_dt = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                    query = query.filter(UserAnalysisHistory.created_at < date_to_dt)
                except ValueError:
                    pass
            
            return query.scalar() or 0
    
    def get_session_by_id(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene una sesión ROM por ID como diccionario.
        Alias de get_rom_session_by_id pero retorna diccionario.
        
        Args:
            session_id: ID de la sesión ROM
        
        Returns:
            Diccionario con datos de la sesión o None si no existe
        """
        with self.get_session() as session:
            rom_session = session.query(ROMSession).filter_by(id=session_id).first()
            if rom_session:
                return rom_session.to_dict()
            return None
    
    def get_user_analysis_by_id(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un análisis de usuario por ID.
        
        Args:
            analysis_id: ID del análisis en user_analysis_history
        
        Returns:
            Diccionario con datos del análisis o None si no existe
        """
        with self.get_session() as session:
            analysis = session.query(UserAnalysisHistory).filter_by(id=analysis_id).first()
            if analysis:
                return analysis.to_dict()
            return None
    
    def get_recent_history_for_exercise(
        self,
        user_id: int,
        segment: str,
        exercise_type: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el historial reciente para un ejercicio específico.
        
        Args:
            user_id: ID del usuario
            segment: Segmento corporal
            exercise_type: Tipo de ejercicio
            limit: Cantidad máxima de registros
        
        Returns:
            Lista de análisis recientes como diccionarios
        """
        with self.get_session() as session:
            records = session.query(UserAnalysisHistory).filter_by(
                user_id=user_id,
                segment=segment,
                exercise_type=exercise_type
            ).order_by(
                UserAnalysisHistory.created_at.desc()
            ).limit(limit).all()
            
            return [record.to_dict() for record in records]
    
    def get_recent_sessions_for_subject(
        self,
        subject_id: int,
        segment: str,
        exercise_type: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Obtiene las sesiones ROM recientes de un sujeto para un ejercicio específico.
        Se usa para mostrar el historial en la interfaz de análisis cuando se analiza un sujeto.
        
        Args:
            subject_id: ID del sujeto
            segment: Segmento corporal
            exercise_type: Tipo de ejercicio
            limit: Cantidad máxima de registros
        
        Returns:
            Lista de sesiones ROM como diccionarios
        """
        with self.get_session() as session:
            records = session.query(ROMSession).filter_by(
                subject_id=subject_id,
                segment=segment,
                exercise_type=exercise_type
            ).order_by(
                ROMSession.created_at.desc()
            ).limit(limit).all()
            
            return [record.to_dict() for record in records]
    
    def get_user_analysis_stats(self, user_id: int, segment: str = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas de análisis de un usuario.
        
        Args:
            user_id: ID del usuario
            segment: Filtrar por segmento (opcional)
        
        Returns:
            Estadísticas de análisis
        """
        with self.get_session() as session:
            query = session.query(UserAnalysisHistory).filter_by(user_id=user_id)
            
            if segment:
                query = query.filter_by(segment=segment)
            
            records = query.all()
            
            if not records:
                return {
                    'total_analyses': 0,
                    'avg_rom': 0,
                    'max_rom': 0,
                    'last_analysis': None
                }
            
            rom_values = [r.rom_value for r in records if r.rom_value]
            
            return {
                'total_analyses': len(records),
                'avg_rom': round(sum(rom_values) / len(rom_values), 1) if rom_values else 0,
                'max_rom': round(max(rom_values), 1) if rom_values else 0,
                'last_analysis': records[0].created_at.isoformat() if records else None
            }
    
    def get_admin_global_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas globales del sistema para el dashboard del admin.
        
        Returns:
            Diccionario con estadísticas globales:
            - Contadores generales (usuarios, sujetos, sesiones)
            - Estadísticas por segmento
            - Actividad reciente
            - Top estudiantes
        """
        with self.get_session() as session:
            # ====== CONTADORES GENERALES ======
            total_users = session.query(func.count(User.id)).scalar() or 0
            total_students = session.query(func.count(User.id)).filter_by(role='student', is_active=True).scalar() or 0
            total_admins = session.query(func.count(User.id)).filter_by(role='admin', is_active=True).scalar() or 0
            total_subjects = session.query(func.count(Subject.id)).scalar() or 0
            
            # Sesiones ROM (análisis de sujetos)
            total_rom_sessions = session.query(func.count(ROMSession.id)).scalar() or 0
            
            # Auto-análisis
            total_self_analyses = session.query(func.count(UserAnalysisHistory.id)).scalar() or 0
            
            # Total combinado
            total_analyses = total_rom_sessions + total_self_analyses
            
            # ====== ESTADÍSTICAS POR SEGMENTO ======
            segments = ['shoulder', 'elbow', 'hip', 'knee', 'ankle']
            segment_names = {
                'shoulder': 'Hombro',
                'elbow': 'Codo', 
                'hip': 'Cadera',
                'knee': 'Rodilla',
                'ankle': 'Tobillo'
            }
            
            segment_stats = []
            for seg in segments:
                # Contar de ambas tablas
                rom_count = session.query(func.count(ROMSession.id)).filter_by(segment=seg).scalar() or 0
                self_count = session.query(func.count(UserAnalysisHistory.id)).filter_by(segment=seg).scalar() or 0
                total_seg = rom_count + self_count
                
                # Calcular porcentaje
                percentage = round((total_seg / total_analyses * 100), 1) if total_analyses > 0 else 0
                
                segment_stats.append({
                    'key': seg,
                    'name': segment_names[seg],
                    'count': total_seg,
                    'percentage': percentage
                })
            
            # Ordenar por cantidad (mayor a menor)
            segment_stats.sort(key=lambda x: x['count'], reverse=True)
            
            # ====== ESTADÍSTICAS POR EJERCICIO ======
            exercise_names = {
                'flexion': 'Flexión',
                'extension': 'Extensión',
                'abduction': 'Abducción',
                'adduction': 'Aducción',
                'internal_rotation': 'Rot. Interna',
                'external_rotation': 'Rot. Externa'
            }
            
            exercise_stats = []
            for ex_key, ex_name in exercise_names.items():
                rom_count = session.query(func.count(ROMSession.id)).filter_by(exercise_type=ex_key).scalar() or 0
                self_count = session.query(func.count(UserAnalysisHistory.id)).filter_by(exercise_type=ex_key).scalar() or 0
                total_ex = rom_count + self_count
                
                if total_ex > 0:
                    percentage = round((total_ex / total_analyses * 100), 1) if total_analyses > 0 else 0
                    exercise_stats.append({
                        'key': ex_key,
                        'name': ex_name,
                        'count': total_ex,
                        'percentage': percentage
                    })
            
            exercise_stats.sort(key=lambda x: x['count'], reverse=True)
            
            # ====== TOP ESTUDIANTES (por actividad) ======
            top_students = []
            students = session.query(User).filter_by(role='student', is_active=True).all()
            
            for student in students:
                rom_count = session.query(func.count(ROMSession.id)).filter_by(user_id=student.id).scalar() or 0
                self_count = session.query(func.count(UserAnalysisHistory.id)).filter_by(user_id=student.id).scalar() or 0
                subjects_count = session.query(func.count(Subject.id)).filter_by(created_by=student.id).scalar() or 0
                
                total_activity = rom_count + self_count
                
                if total_activity > 0:
                    top_students.append({
                        'id': student.id,
                        'name': student.full_name,
                        'username': student.username,
                        'analyses': total_activity,
                        'subjects': subjects_count,
                        'last_login': student.last_login.isoformat() if student.last_login else None
                    })
            
            # Ordenar por actividad
            top_students.sort(key=lambda x: x['analyses'], reverse=True)
            top_students = top_students[:10]  # Top 10
            
            # ====== ACTIVIDAD RECIENTE (últimos 7 días) ======
            from datetime import datetime, timedelta
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            recent_rom = session.query(func.count(ROMSession.id)).filter(
                ROMSession.created_at >= seven_days_ago
            ).scalar() or 0
            
            recent_self = session.query(func.count(UserAnalysisHistory.id)).filter(
                UserAnalysisHistory.created_at >= seven_days_ago
            ).scalar() or 0
            
            recent_subjects = session.query(func.count(Subject.id)).filter(
                Subject.created_at >= seven_days_ago
            ).scalar() or 0
            
            # ====== ÚLTIMA ACTIVIDAD ======
            last_rom = session.query(ROMSession).order_by(ROMSession.created_at.desc()).first()
            last_self = session.query(UserAnalysisHistory).order_by(UserAnalysisHistory.created_at.desc()).first()
            
            last_activity = None
            if last_rom and last_self:
                last_activity = max(last_rom.created_at, last_self.created_at).isoformat()
            elif last_rom:
                last_activity = last_rom.created_at.isoformat()
            elif last_self:
                last_activity = last_self.created_at.isoformat()
            
            return {
                # Contadores principales
                'total_users': total_users,
                'total_students': total_students,
                'total_admins': total_admins,
                'total_subjects': total_subjects,
                'total_analyses': total_analyses,
                'total_rom_sessions': total_rom_sessions,
                'total_self_analyses': total_self_analyses,
                
                # Por segmento y ejercicio
                'segment_stats': segment_stats,
                'exercise_stats': exercise_stats,
                
                # Top estudiantes
                'top_students': top_students,
                
                # Actividad reciente (7 días)
                'recent_analyses': recent_rom + recent_self,
                'recent_subjects': recent_subjects,
                
                # Última actividad
                'last_activity': last_activity
            }
    
    def get_all_students_with_stats(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los estudiantes con sus estadísticas para el admin.
        
        Returns:
            Lista de estudiantes con estadísticas
        """
        with self.get_session() as session:
            students = session.query(User).filter_by(role='student').order_by(User.created_at.desc()).all()
            
            result = []
            for student in students:
                rom_count = session.query(func.count(ROMSession.id)).filter_by(user_id=student.id).scalar() or 0
                self_count = session.query(func.count(UserAnalysisHistory.id)).filter_by(user_id=student.id).scalar() or 0
                subjects_count = session.query(func.count(Subject.id)).filter_by(created_by=student.id).scalar() or 0
                
                result.append({
                    'id': student.id,
                    'username': student.username,
                    'full_name': student.full_name,
                    'email': student.email,
                    'student_id': student.student_id,
                    'program': student.program,
                    'semester': student.semester,
                    'is_active': student.is_active,
                    'created_at': student.created_at.isoformat() if student.created_at else None,
                    'last_login': student.last_login.isoformat() if student.last_login else None,
                    'total_analyses': rom_count + self_count,
                    'rom_sessions': rom_count,
                    'self_analyses': self_count,
                    'subjects_count': subjects_count
                })
            
            return result
    
    def get_database_info(self) -> Dict[str, Any]:
        """Obtiene información general de la base de datos"""
        with self.get_session() as session:
            return {
                'total_users': session.query(func.count(User.id)).scalar(),
                'total_students': session.query(func.count(User.id)).filter_by(role='student').scalar(),
                'total_subjects': session.query(func.count(Subject.id)).scalar(),
                'total_sessions': session.query(func.count(ROMSession.id)).scalar(),
                'total_measurements': session.query(func.count(AngleMeasurement.id)).scalar(),
                'total_logs': session.query(func.count(SystemLog.id)).scalar()
            }


# ============================================================================
# SINGLETON INSTANCE (Opcional - para uso global)
# ============================================================================

# Instancia global del database manager (se puede importar en otros módulos)
# from database.database_manager import db_manager
# user = db_manager.get_user_by_id(1)

_db_manager_instance = None

def get_db_manager(db_path: str = 'database/biotrack.db') -> DatabaseManager:
    """Obtiene la instancia singleton del DatabaseManager"""
    global _db_manager_instance
    
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager(db_path)
    
    return _db_manager_instance


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == '__main__':
    # Inicializar database manager
    db_manager = DatabaseManager('database/biotrack.db')
    
    # Test de conexión
    if db_manager.test_connection():
        print("✅ Conexión a base de datos exitosa")
        
        # Obtener información
        info = db_manager.get_database_info()
        print(f"\n📊 Información de la Base de Datos:")
        print(f"   • Usuarios: {info['total_users']}")
        print(f"   • Estudiantes: {info['total_students']}")
        print(f"   • Sujetos: {info['total_subjects']}")
        print(f"   • Sesiones ROM: {info['total_sessions']}")
        print(f"   • Mediciones: {info['total_measurements']}")
        print(f"   • Logs: {info['total_logs']}")
        
        # Listar usuarios
        users = db_manager.get_all_users()
        print(f"\n👥 Usuarios en el sistema:")
        for user in users:
            print(f"   • {user.username} ({user.role}) - {user.full_name}")
    else:
        print("❌ Error de conexión a la base de datos")
