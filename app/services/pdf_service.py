"""
📄 SERVICIO DE GENERACIÓN DE PDF - BIOTRACK
=============================================
Genera reportes PDF profesionales con logos de Univalle y BIOTRACK

Autor: BIOTRACK Team
Fecha: 2025-12-08
"""

import os
import io
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
        Image, PageBreak, HRFlowable
    )
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️ ReportLab no instalado. Ejecute: pip install reportlab")


class PDFReportGenerator:
    """
    Generador de reportes PDF para BIOTRACK
    Incluye logos de Universidad del Valle y BIOTRACK
    """
    
    # Colores corporativos
    COLORS = {
        'primary': colors.HexColor('#00D4FF'),      # Cyan BIOTRACK
        'secondary': colors.HexColor('#00FF88'),    # Verde BIOTRACK
        'dark': colors.HexColor('#1a1a2e'),         # Fondo oscuro
        'text': colors.HexColor('#333333'),         # Texto principal
        'light_gray': colors.HexColor('#f5f5f5'),   # Fondo claro
        'border': colors.HexColor('#e0e0e0'),       # Bordes
        'success': colors.HexColor('#28a745'),      # Verde éxito
        'warning': colors.HexColor('#ffc107'),      # Amarillo advertencia
        'danger': colors.HexColor('#dc3545'),       # Rojo peligro
    }
    
    # Nombres de segmentos en español
    SEGMENT_NAMES = {
        'shoulder': 'Hombro',
        'elbow': 'Codo',
        'hip': 'Cadera',
        'knee': 'Rodilla',
        'ankle': 'Tobillo'
    }
    
    # Rangos de referencia ROM (grados)
    ROM_REFERENCES = {
        'shoulder': {'flexion': 180, 'extension': 60, 'abduction': 180},
        'elbow': {'flexion': 150, 'extension': 0},
        'hip': {'flexion': 120, 'extension': 30, 'abduction': 45},
        'knee': {'flexion': 135, 'extension': 0},
        'ankle': {'dorsiflexion': 20, 'plantarflexion': 50}
    }
    
    def __init__(self, output_dir: str = None):
        """
        Inicializa el generador de PDF
        
        Args:
            output_dir: Directorio de salida para los PDFs
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab no está instalado. Ejecute: pip install reportlab")
        
        # Directorio base de la aplicación
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.static_dir = os.path.join(self.base_dir, 'static')
        self.images_dir = os.path.join(self.static_dir, 'images')
        
        # Directorio de salida
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = os.path.join(
                os.path.dirname(self.base_dir), 'instance', 'exports'
            )
        
        # Crear directorio si no existe
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Rutas de logos
        self.logo_biotrack = os.path.join(self.images_dir, 'logo.png')
        self.logo_univalle = os.path.join(self.images_dir, 'logo univalle.png')
        
        # Estilos
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura estilos personalizados para el PDF"""
        
        # Título principal
        self.styles.add(ParagraphStyle(
            name='MainTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.COLORS['primary'],
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        ))
        
        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.COLORS['text'],
            alignment=TA_CENTER,
            spaceAfter=12,
            fontName='Helvetica'
        ))
        
        # Encabezado de sección
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.COLORS['primary'],
            spaceBefore=20,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            borderColor=self.COLORS['primary'],
            borderWidth=1,
            borderPadding=5
        ))
        
        # Texto normal
        self.styles.add(ParagraphStyle(
            name='NormalText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.COLORS['text'],
            alignment=TA_JUSTIFY,
            spaceAfter=6
        ))
        
        # Texto pequeño
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER
        ))
        
        # Valor destacado
        self.styles.add(ParagraphStyle(
            name='HighlightValue',
            parent=self.styles['Normal'],
            fontSize=18,
            textColor=self.COLORS['primary'],
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
    
    def _create_header(self, title: str, subtitle: str = None) -> List:
        """
        Crea el encabezado del documento con logos
        
        Args:
            title: Título del reporte
            subtitle: Subtítulo opcional
        
        Returns:
            Lista de elementos para el encabezado
        """
        elements = []
        
        # Tabla con logos y título
        header_data = []
        
        # Logo Univalle (izquierda)
        if os.path.exists(self.logo_univalle):
            logo_univalle = Image(self.logo_univalle, width=1.2*inch, height=1.2*inch)
        else:
            logo_univalle = Paragraph("UNIVALLE", self.styles['NormalText'])
        
        # Logo BIOTRACK (derecha)
        if os.path.exists(self.logo_biotrack):
            logo_biotrack = Image(self.logo_biotrack, width=1.2*inch, height=1.2*inch)
        else:
            logo_biotrack = Paragraph("BIOTRACK", self.styles['NormalText'])
        
        # Título central
        title_content = [
            Paragraph(title, self.styles['MainTitle']),
        ]
        if subtitle:
            title_content.append(Paragraph(subtitle, self.styles['SubTitle']))
        
        header_data.append([logo_univalle, title_content, logo_biotrack])
        
        header_table = Table(header_data, colWidths=[1.5*inch, 4.5*inch, 1.5*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(header_table)
        
        # Línea institucional
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "Universidad del Valle - Carrera Biomédica - Materia Biomecánica",
            self.styles['SmallText']
        ))
        elements.append(Spacer(1, 5))
        
        # Línea separadora
        elements.append(HRFlowable(
            width="100%",
            thickness=2,
            color=self.COLORS['primary'],
            spaceBefore=5,
            spaceAfter=15
        ))
        
        return elements
    
    def _create_footer(self, canvas_obj, doc):
        """
        Crea el pie de página
        """
        canvas_obj.saveState()
        
        # Línea
        canvas_obj.setStrokeColor(self.COLORS['border'])
        canvas_obj.line(50, 50, letter[0] - 50, 50)
        
        # Texto del pie
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.gray)
        
        # Fecha y hora
        now = datetime.now()
        date_str = now.strftime('%d/%m/%Y %H:%M')
        canvas_obj.drawString(50, 35, f"Generado: {date_str}")
        
        # Número de página
        page_num = canvas_obj.getPageNumber()
        canvas_obj.drawRightString(letter[0] - 50, 35, f"Página {page_num}")
        
        # Centro: BIOTRACK
        canvas_obj.drawCentredString(letter[0] / 2, 35, "BIOTRACK - Sistema de Análisis Biomecánico")
        
        canvas_obj.restoreState()
    
    def _get_quality_color(self, quality: float) -> colors.Color:
        """Retorna el color según la calidad"""
        if quality >= 80:
            return self.COLORS['success']
        elif quality >= 60:
            return self.COLORS['warning']
        else:
            return self.COLORS['danger']
    
    def _create_info_table(self, data: Dict[str, str], title: str = None) -> List:
        """
        Crea una tabla de información
        
        Args:
            data: Diccionario con datos clave-valor
            title: Título opcional de la sección
        
        Returns:
            Lista de elementos
        """
        elements = []
        
        if title:
            elements.append(Paragraph(f"📋 {title}", self.styles['SectionHeader']))
        
        table_data = []
        for key, value in data.items():
            table_data.append([
                Paragraph(f"<b>{key}:</b>", self.styles['NormalText']),
                Paragraph(str(value), self.styles['NormalText'])
            ])
        
        table = Table(table_data, colWidths=[2*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.COLORS['light_gray']),
            ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['border']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 15))
        
        return elements
    
    def generate_analysis_report(
        self,
        analysis_data: Dict[str, Any],
        user_data: Dict[str, Any] = None,
        subject_data: Dict[str, Any] = None,
        filename: str = None
    ) -> str:
        """
        Genera un reporte PDF de un análisis ROM
        
        Args:
            analysis_data: Datos del análisis (segment, exercise, rom_value, etc.)
            user_data: Datos del usuario que realizó el análisis
            subject_data: Datos del sujeto analizado (si aplica)
            filename: Nombre del archivo (opcional)
        
        Returns:
            Ruta del archivo PDF generado
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"reporte_analisis_{timestamp}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Crear documento
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=70
        )
        
        elements = []
        
        # Encabezado
        segment_name = self.SEGMENT_NAMES.get(
            analysis_data.get('segment', ''), 
            analysis_data.get('segment', 'N/A')
        )
        elements.extend(self._create_header(
            "Reporte de Análisis ROM",
            f"{segment_name} - {analysis_data.get('exercise_name', analysis_data.get('exercise', 'N/A'))}"
        ))
        
        # Información del análisis
        analysis_info = {
            'Segmento': segment_name,
            'Ejercicio': analysis_data.get('exercise_name', analysis_data.get('exercise', 'N/A')),
            'Lado': 'Izquierdo' if analysis_data.get('side') == 'left' else 'Derecho' if analysis_data.get('side') == 'right' else 'N/A',
            'Fecha': analysis_data.get('created_at', analysis_data.get('analysis_date', datetime.now())).strftime('%d/%m/%Y %H:%M') if hasattr(analysis_data.get('created_at', analysis_data.get('analysis_date')), 'strftime') else str(analysis_data.get('created_at', analysis_data.get('analysis_date', 'N/A')))
        }
        elements.extend(self._create_info_table(analysis_info, "Información del Análisis"))
        
        # Información del usuario
        if user_data:
            user_info = {
                'Usuario': user_data.get('username', 'N/A'),
                'Nombre': user_data.get('full_name', 'N/A'),
                'CI': user_data.get('student_id', 'N/A'),
                'Programa': user_data.get('program', 'N/A')
            }
            elements.extend(self._create_info_table(user_info, "Información del Evaluador"))
        
        # Información del sujeto
        if subject_data:
            subject_info = {
                'Código': subject_data.get('subject_code', 'N/A'),
                'Nombre': f"{subject_data.get('first_name', '')} {subject_data.get('last_name', '')}".strip() or 'N/A',
                'Género': 'Masculino' if subject_data.get('gender') == 'M' else 'Femenino' if subject_data.get('gender') == 'F' else 'N/A',
                'Edad': f"{subject_data.get('age', 'N/A')} años" if subject_data.get('age') else 'N/A'
            }
            elements.extend(self._create_info_table(subject_info, "Información del Sujeto"))
        
        # Resultados del análisis
        elements.append(Paragraph("📊 Resultados del Análisis", self.styles['SectionHeader']))
        
        rom_value = analysis_data.get('rom_value', analysis_data.get('rom_max', 0))
        quality = analysis_data.get('quality_score', analysis_data.get('quality', 0))
        
        # Tabla de resultados
        results_data = [
            ['Parámetro', 'Valor', 'Referencia'],
            [
                'ROM Máximo',
                f"{rom_value:.1f}°" if rom_value else 'N/A',
                self._get_reference_rom(analysis_data.get('segment'), analysis_data.get('exercise_name', analysis_data.get('exercise')))
            ],
            [
                'Calidad del Análisis',
                f"{quality:.0f}%" if quality else 'N/A',
                '≥80% Óptimo'
            ]
        ]
        
        # ROM mínimo si existe
        if analysis_data.get('rom_min'):
            results_data.append([
                'ROM Mínimo',
                f"{analysis_data['rom_min']:.1f}°",
                '-'
            ])
        
        # ROM promedio si existe
        if analysis_data.get('rom_avg'):
            results_data.append([
                'ROM Promedio',
                f"{analysis_data['rom_avg']:.1f}°",
                '-'
            ])
        
        results_table = Table(results_data, colWidths=[2*inch, 2*inch, 2.5*inch])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), self.COLORS['light_gray']),
            ('GRID', (0, 0), (-1, -1), 1, self.COLORS['border']),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(results_table)
        elements.append(Spacer(1, 20))
        
        # Interpretación
        elements.append(Paragraph("📝 Interpretación", self.styles['SectionHeader']))
        
        interpretation = self._generate_interpretation(analysis_data)
        elements.append(Paragraph(interpretation, self.styles['NormalText']))
        
        # Notas adicionales
        if analysis_data.get('notes'):
            elements.append(Spacer(1, 15))
            elements.append(Paragraph("📌 Notas", self.styles['SectionHeader']))
            elements.append(Paragraph(analysis_data['notes'], self.styles['NormalText']))
        
        # Construir PDF
        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        
        return filepath
    
    def generate_history_report(
        self,
        analyses: List[Dict[str, Any]],
        user_data: Dict[str, Any],
        title: str = "Historial de Análisis",
        filename: str = None
    ) -> str:
        """
        Genera un reporte PDF del historial de análisis
        
        Args:
            analyses: Lista de análisis
            user_data: Datos del usuario
            title: Título del reporte
            filename: Nombre del archivo (opcional)
        
        Returns:
            Ruta del archivo PDF generado
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"historial_{user_data.get('username', 'usuario')}_{timestamp}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=70
        )
        
        elements = []
        
        # Encabezado
        elements.extend(self._create_header(title, f"Usuario: {user_data.get('full_name', user_data.get('username', 'N/A'))}"))
        
        # Info del usuario
        user_info = {
            'Usuario': user_data.get('username', 'N/A'),
            'Nombre': user_data.get('full_name', 'N/A'),
            'Total de Análisis': str(len(analyses)),
            'Fecha del Reporte': datetime.now().strftime('%d/%m/%Y %H:%M')
        }
        elements.extend(self._create_info_table(user_info, "Información General"))
        
        # Resumen por segmento
        elements.append(Paragraph("📊 Resumen por Segmento", self.styles['SectionHeader']))
        
        segment_summary = {}
        for analysis in analyses:
            seg = analysis.get('segment', 'unknown')
            if seg not in segment_summary:
                segment_summary[seg] = {'count': 0, 'total_rom': 0}
            segment_summary[seg]['count'] += 1
            rom = analysis.get('rom_value', analysis.get('rom_max', 0)) or 0
            segment_summary[seg]['total_rom'] += rom
        
        summary_data = [['Segmento', 'Cantidad', 'ROM Promedio']]
        for seg, data in segment_summary.items():
            avg_rom = data['total_rom'] / data['count'] if data['count'] > 0 else 0
            summary_data.append([
                self.SEGMENT_NAMES.get(seg, seg),
                str(data['count']),
                f"{avg_rom:.1f}°"
            ])
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, self.COLORS['border']),
            ('BACKGROUND', (0, 1), (-1, -1), self.COLORS['light_gray']),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Listado de análisis
        elements.append(Paragraph("📋 Detalle de Análisis", self.styles['SectionHeader']))
        
        if analyses:
            detail_data = [['Fecha', 'Segmento', 'Ejercicio', 'Lado', 'ROM', 'Calidad']]
            
            for analysis in analyses[:50]:  # Limitar a 50 registros
                date_val = analysis.get('created_at', analysis.get('analysis_date'))
                date_str = date_val.strftime('%d/%m/%y') if hasattr(date_val, 'strftime') else str(date_val)[:10]
                
                detail_data.append([
                    date_str,
                    self.SEGMENT_NAMES.get(analysis.get('segment', ''), analysis.get('segment', '')),
                    analysis.get('exercise_name', analysis.get('exercise', ''))[:20],
                    'Izq' if analysis.get('side') == 'left' else 'Der' if analysis.get('side') == 'right' else '-',
                    f"{analysis.get('rom_value', analysis.get('rom_max', 0)) or 0:.1f}°",
                    f"{analysis.get('quality_score', analysis.get('quality', 0)) or 0:.0f}%"
                ])
            
            detail_table = Table(detail_data, colWidths=[0.9*inch, 1.1*inch, 1.8*inch, 0.6*inch, 0.8*inch, 0.9*inch])
            detail_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['dark']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['border']),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['light_gray']]),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(detail_table)
            
            if len(analyses) > 50:
                elements.append(Spacer(1, 10))
                elements.append(Paragraph(
                    f"<i>Mostrando 50 de {len(analyses)} registros</i>",
                    self.styles['SmallText']
                ))
        else:
            elements.append(Paragraph(
                "No hay análisis registrados en el período seleccionado.",
                self.styles['NormalText']
            ))
        
        # Construir PDF
        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        
        return filepath
    
    def generate_subject_report(
        self,
        subject_data: Dict[str, Any],
        sessions: List[Dict[str, Any]],
        user_data: Dict[str, Any] = None,
        filename: str = None
    ) -> str:
        """
        Genera un reporte PDF de un sujeto con todas sus sesiones
        
        Args:
            subject_data: Datos del sujeto
            sessions: Lista de sesiones ROM del sujeto
            user_data: Datos del usuario evaluador
            filename: Nombre del archivo (opcional)
        
        Returns:
            Ruta del archivo PDF generado
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            subject_code = subject_data.get('subject_code', 'sujeto')
            filename = f"reporte_sujeto_{subject_code}_{timestamp}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=70
        )
        
        elements = []
        
        # Encabezado
        subject_name = f"{subject_data.get('first_name', '')} {subject_data.get('last_name', '')}".strip()
        elements.extend(self._create_header(
            "Reporte de Evaluación",
            f"Sujeto: {subject_name or subject_data.get('subject_code', 'N/A')}"
        ))
        
        # Info del sujeto
        subject_info = {
            'Código': subject_data.get('subject_code', 'N/A'),
            'Nombre Completo': subject_name or 'N/A',
            'Género': 'Masculino' if subject_data.get('gender') == 'M' else 'Femenino' if subject_data.get('gender') == 'F' else 'N/A',
            'Edad': f"{subject_data.get('age', 'N/A')} años" if subject_data.get('age') else 'N/A',
            'Estatura': f"{subject_data.get('height', 'N/A')} cm" if subject_data.get('height') else 'N/A',
            'Peso': f"{subject_data.get('weight', 'N/A')} kg" if subject_data.get('weight') else 'N/A'
        }
        elements.extend(self._create_info_table(subject_info, "Datos del Sujeto"))
        
        # Info del evaluador
        if user_data:
            evaluator_info = {
                'Evaluador': user_data.get('full_name', user_data.get('username', 'N/A')),
                'Total de Evaluaciones': str(len(sessions))
            }
            elements.extend(self._create_info_table(evaluator_info, "Información del Evaluador"))
        
        # Resultados por sesión
        elements.append(Paragraph("📊 Resultados de Evaluaciones ROM", self.styles['SectionHeader']))
        
        if sessions:
            # Agrupar por segmento
            by_segment = {}
            for session in sessions:
                seg = session.get('segment', 'unknown')
                if seg not in by_segment:
                    by_segment[seg] = []
                by_segment[seg].append(session)
            
            for segment, seg_sessions in by_segment.items():
                elements.append(Paragraph(
                    f"<b>{self.SEGMENT_NAMES.get(segment, segment)}</b>",
                    self.styles['NormalText']
                ))
                
                seg_data = [['Ejercicio', 'Lado', 'ROM', 'Calidad', 'Fecha']]
                for s in seg_sessions:
                    date_val = s.get('created_at')
                    date_str = date_val.strftime('%d/%m/%y') if hasattr(date_val, 'strftime') else str(date_val)[:10] if date_val else 'N/A'
                    
                    seg_data.append([
                        s.get('exercise_name', s.get('exercise', ''))[:25],
                        'Izq' if s.get('side') == 'left' else 'Der' if s.get('side') == 'right' else '-',
                        f"{s.get('rom_value', 0):.1f}°",
                        f"{s.get('quality_score', 0):.0f}%",
                        date_str
                    ])
                
                seg_table = Table(seg_data, colWidths=[2.2*inch, 0.7*inch, 0.9*inch, 0.9*inch, 1*inch])
                seg_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['secondary']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), self.COLORS['dark']),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, self.COLORS['border']),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.COLORS['light_gray']]),
                    ('PADDING', (0, 0), (-1, -1), 5),
                ]))
                elements.append(seg_table)
                elements.append(Spacer(1, 15))
        else:
            elements.append(Paragraph(
                "No hay evaluaciones registradas para este sujeto.",
                self.styles['NormalText']
            ))
        
        # Construir PDF
        doc.build(elements, onFirstPage=self._create_footer, onLaterPages=self._create_footer)
        
        return filepath
    
    def _get_reference_rom(self, segment: str, exercise: str) -> str:
        """Obtiene el valor de referencia ROM para un ejercicio"""
        if not segment or not exercise:
            return "N/A"
        
        segment_refs = self.ROM_REFERENCES.get(segment, {})
        
        # Buscar coincidencia parcial en el ejercicio
        exercise_lower = exercise.lower()
        for ref_key, ref_value in segment_refs.items():
            if ref_key in exercise_lower:
                return f"{ref_value}° (referencia)"
        
        return "Consultar estándares"
    
    def _generate_interpretation(self, analysis_data: Dict[str, Any]) -> str:
        """Genera una interpretación del análisis"""
        rom = analysis_data.get('rom_value', analysis_data.get('rom_max', 0)) or 0
        quality = analysis_data.get('quality_score', analysis_data.get('quality', 0)) or 0
        segment = analysis_data.get('segment', '')
        exercise = analysis_data.get('exercise_name', analysis_data.get('exercise', ''))
        
        segment_name = self.SEGMENT_NAMES.get(segment, segment)
        
        interpretation = f"El análisis de {segment_name} "
        
        if exercise:
            interpretation += f"para el ejercicio de {exercise} "
        
        interpretation += f"registró un rango de movimiento máximo de {rom:.1f}°. "
        
        if quality >= 80:
            interpretation += f"La calidad del análisis fue óptima ({quality:.0f}%), lo que indica que los datos son confiables. "
        elif quality >= 60:
            interpretation += f"La calidad del análisis fue aceptable ({quality:.0f}%). Se recomienda verificar la postura durante futuras mediciones. "
        else:
            interpretation += f"La calidad del análisis fue baja ({quality:.0f}%). Se sugiere repetir la medición asegurando una correcta postura y visibilidad de los puntos anatómicos. "
        
        interpretation += "Para una evaluación completa, compare estos valores con los estándares de referencia y considere el contexto clínico del sujeto."
        
        return interpretation


# Instancia global del generador
pdf_generator = None

def get_pdf_generator() -> Optional[PDFReportGenerator]:
    """Obtiene o crea la instancia del generador de PDF"""
    global pdf_generator
    if pdf_generator is None:
        try:
            pdf_generator = PDFReportGenerator()
        except ImportError as e:
            print(f"⚠️ No se pudo inicializar el generador de PDF: {e}")
            return None
    return pdf_generator
