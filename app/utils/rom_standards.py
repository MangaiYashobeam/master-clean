"""
ROM_STANDARDS - Estándares de Rango de Movimiento Articular
============================================================

Referencias Bibliográficas:
- AAOS (American Academy of Orthopaedic Surgeons). Joint Motion: Method of Measuring and Recording
- Beighton P, Solomon L, Soskolne CL. Articular mobility in an African population. Ann Rheum Dis. 1973
- Nordin M, Frankel VH. Basic Biomechanics of the Musculoskeletal System. 5th ed. 2022
- Kapandji IA. Fisiología Articular. 6th ed. Editorial Médica Panamericana
- American Medical Association (AMA). Guides to the Evaluation of Permanent Impairment. 6th ed.

Sistema de Clasificación de ROM:
- AUMENTADO: >100% del rango normal (Hiperlaxitud - según AAOS/Beighton Scale)
- ÓPTIMO: 90-100% del rango normal máximo
- FUNCIONAL: 70-89% del rango normal
- LIMITADO: 50-69% del rango normal
- MUY LIMITADO: <50% del rango normal

NOTA CLÍNICA: "Aumentado" NO significa "mejor". La hiperlaxitud indica:
- Laxitud ligamentosa constitucional
- Mayor demanda de control neuromuscular
- Posible riesgo de inestabilidad articular
"""

ROM_STANDARDS = {
    # =========================================================================
    # HOMBRO (Articulación Glenohumeral)
    # =========================================================================
    "shoulder": {
        "segment_name": "Hombro",
        "joint_type": "Enartrosis (esférica)",
        "bibliography": "Nordin & Frankel (2022), Kapandji (6ta ed.)",
        
        "exercises": {
            "flexion": {
                "name": "Flexión de Hombro",
                "normal_range": {"min": 0, "max": 180},
                "classification": {
                    "optimo": {"min": 162, "max": 180, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 135, "max": 161, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 90, "max": 134, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 89, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Movimiento esencial para actividades sobre la cabeza",
                "reference": "AAOS: 0-180°, AMA: 0-180°"
            },
            "extension": {
                "name": "Extensión de Hombro",
                "normal_range": {"min": 0, "max": 60},
                "classification": {
                    "optimo": {"min": 54, "max": 60, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 45, "max": 53, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 30, "max": 44, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 29, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Importante para alcanzar objetos detrás del cuerpo",
                "reference": "AAOS: 0-60°, AMA: 0-50°"
            },
            "abduction": {
                "name": "Abducción de Hombro",
                "normal_range": {"min": 0, "max": 180},
                "classification": {
                    "optimo": {"min": 162, "max": 180, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 135, "max": 161, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 90, "max": 134, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 89, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Movimiento fundamental para vestirse y higiene personal",
                "reference": "AAOS: 0-180°, Kapandji: 0-180°"
            },
            "external_rotation": {
                "name": "Rotación Externa de Hombro",
                "normal_range": {"min": 0, "max": 90},
                "classification": {
                    "optimo": {"min": 81, "max": 90, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 67, "max": 80, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 45, "max": 66, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 44, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Esencial para actividades de la vida diaria como peinarse",
                "reference": "AAOS: 0-90°, AMA: 0-90°"
            },
            "internal_rotation": {
                "name": "Rotación Interna de Hombro",
                "normal_range": {"min": 0, "max": 70},
                "classification": {
                    "optimo": {"min": 63, "max": 70, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 52, "max": 62, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 35, "max": 51, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 34, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Importante para higiene personal y vestirse",
                "reference": "AAOS: 0-70°, AMA: 0-80°"
            }
        }
    },
    
    # =========================================================================
    # CODO
    # =========================================================================
    "elbow": {
        "segment_name": "Codo",
        "joint_type": "Troclear (bisagra)",
        "bibliography": "Nordin & Frankel (2022), AMA Guides 6th ed.",
        
        "exercises": {
            "flexion": {
                "name": "Flexión de Codo",
                "normal_range": {"min": 0, "max": 150},
                "classification": {
                    "optimo": {"min": 135, "max": 150, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 112, "max": 134, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 75, "max": 111, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 74, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Rango funcional mínimo: 30-130° para actividades diarias",
                "reference": "AAOS: 0-150°, AMA: 0-140°"
            },
            "extension": {
                "name": "Extensión de Codo",
                "normal_range": {"min": 0, "max": 10},
                "classification": {
                    # Clasificación basada en:
                    # - AAOS: 0° = extensión completa
                    # - Nordin & Frankel: 0° ± 5° variabilidad normal
                    # - AMA Guides 6th ed: déficit <10° no afecta función
                    # - Morrey BF (1993): Arco funcional 30-130° (déficit extensión <30° aceptable)
                    "optimo": {"min": 0, "max": 5, "percentage": "Extensión completa (0-5°)", "color": "#4CAF50"},
                    "funcional": {"min": 6, "max": 10, "percentage": "Déficit leve (6-10°)", "color": "#2196F3"},
                    "limitado": {"min": 11, "max": 20, "percentage": "Déficit moderado (11-20°)", "color": "#FF9800"},
                    "muy_limitado": {"min": 21, "max": 90, "percentage": "Contractura (>20°)", "color": "#f44336"}
                },
                "clinical_notes": "Déficit <10° generalmente no afecta AVD. Hiperextensión hasta -10° es normal (Beighton).",
                "reference": "AAOS: 0°, AMA Guides 6th ed, Nordin & Frankel (2022), Morrey BF (1993)"
            },
            "overhead_extension": {
                "name": "Extensión de Codo Sobre Cabeza",
                "normal_range": {"min": 0, "max": 150},
                "classification": {
                    "optimo": {"min": 135, "max": 150, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 112, "max": 134, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 75, "max": 111, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 74, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Evalúa extensión con hombro en flexión completa",
                "reference": "AAOS: Combinación flexión hombro + extensión codo"
            }
        }
    },
    
    # =========================================================================
    # RODILLA
    # =========================================================================
    "knee": {
        "segment_name": "Rodilla",
        "joint_type": "Bicondílea modificada",
        "bibliography": "Nordin & Frankel (2022), Kapandji (6ta ed.)",
        
        "exercises": {
            "flexion": {
                "name": "Flexión de Rodilla",
                "normal_range": {"min": 0, "max": 150},
                "classification": {
                    "optimo": {"min": 135, "max": 150, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 112, "max": 134, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 75, "max": 111, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 74, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Flexión de 90° requerida para sentarse. 115° para subir escaleras.",
                "reference": "AAOS: 0-150°, AMA: 0-140°"
            },
            "extension": {
                "name": "Extensión de Rodilla",
                "normal_range": {"min": 0, "max": 10},
                "classification": {
                    "optimo": {"min": 0, "max": 0, "percentage": "Extensión completa", "color": "#4CAF50"},
                    "funcional": {"min": 1, "max": 5, "percentage": "Leve déficit", "color": "#2196F3"},
                    "limitado": {"min": 6, "max": 15, "percentage": "Déficit moderado", "color": "#FF9800"},
                    "muy_limitado": {"min": 16, "max": 90, "percentage": "Contractura", "color": "#f44336"}
                },
                "clinical_notes": "Déficit de extensión afecta patrón de marcha",
                "reference": "AAOS: 0° (extensión completa)"
            }
        }
    },
    
    # =========================================================================
    # CADERA
    # =========================================================================
    "hip": {
        "segment_name": "Cadera",
        "joint_type": "Enartrosis (esférica)",
        "bibliography": "Nordin & Frankel (2022), Kapandji (6ta ed.)",
        
        "exercises": {
            "flexion": {
                "name": "Flexión de Cadera",
                "normal_range": {"min": 0, "max": 135},
                "classification": {
                    "optimo": {"min": 122, "max": 135, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 101, "max": 121, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 68, "max": 100, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 67, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Flexión de 90° necesaria para sentarse. 120° para atarse zapatos.",
                "reference": "AAOS: 0-135°, AMA: 0-100°"
            },
            "extension": {
                "name": "Extensión de Cadera",
                "normal_range": {"min": 0, "max": 30},
                "classification": {
                    "optimo": {"min": 27, "max": 30, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 22, "max": 26, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 15, "max": 21, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 14, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Esencial para fase de despegue en la marcha",
                "reference": "AAOS: 0-30°, AMA: 0-20°"
            },
            "abduction": {
                "name": "Abducción de Cadera",
                "normal_range": {"min": 0, "max": 45},
                "classification": {
                    "optimo": {"min": 40, "max": 45, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 34, "max": 39, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 22, "max": 33, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 21, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Importante para estabilidad pélvica y marcha",
                "reference": "AAOS: 0-45°, Kapandji: 0-45°"
            },
            "adduction": {
                "name": "Aducción de Cadera",
                "normal_range": {"min": 0, "max": 30},
                "classification": {
                    "optimo": {"min": 27, "max": 30, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 22, "max": 26, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 15, "max": 21, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 14, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Necesaria para cruzar las piernas",
                "reference": "AAOS: 0-30°"
            },
            "internal_rotation": {
                "name": "Rotación Interna de Cadera",
                "normal_range": {"min": 0, "max": 45},
                "classification": {
                    "optimo": {"min": 40, "max": 45, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 34, "max": 39, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 22, "max": 33, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 21, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Evaluación en posición sedente con rodilla a 90°",
                "reference": "AAOS: 0-45°, AMA: 0-40°"
            },
            "external_rotation": {
                "name": "Rotación Externa de Cadera",
                "normal_range": {"min": 0, "max": 45},
                "classification": {
                    "optimo": {"min": 40, "max": 45, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 34, "max": 39, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 22, "max": 33, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 21, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Importante para marcha y cambios de dirección",
                "reference": "AAOS: 0-45°, AMA: 0-40°"
            }
        }
    },
    
    # =========================================================================
    # TOBILLO
    # =========================================================================
    "ankle": {
        "segment_name": "Tobillo",
        "joint_type": "Troclear (bisagra)",
        "bibliography": "Nordin & Frankel (2022), AAOS",
        
        "exercises": {
            "dorsiflexion": {
                "name": "Dorsiflexión de Tobillo",
                "normal_range": {"min": 0, "max": 20},
                "classification": {
                    "optimo": {"min": 18, "max": 20, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 15, "max": 17, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 10, "max": 14, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 9, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Mínimo 10° requerido para marcha normal",
                "reference": "AAOS: 0-20°"
            },
            "plantarflexion": {
                "name": "Flexión Plantar de Tobillo",
                "normal_range": {"min": 0, "max": 50},
                "classification": {
                    "optimo": {"min": 45, "max": 50, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 37, "max": 44, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 25, "max": 36, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 24, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Importante para fase de despegue en marcha",
                "reference": "AAOS: 0-50°"
            },
            "inversion": {
                "name": "Inversión de Tobillo",
                "normal_range": {"min": 0, "max": 35},
                "classification": {
                    "optimo": {"min": 31, "max": 35, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 26, "max": 30, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 17, "max": 25, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 16, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Movimiento de articulación subtalar",
                "reference": "AAOS: 0-35°"
            },
            "eversion": {
                "name": "Eversión de Tobillo",
                "normal_range": {"min": 0, "max": 20},
                "classification": {
                    "optimo": {"min": 18, "max": 20, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 15, "max": 17, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 10, "max": 14, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 9, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Movimiento de articulación subtalar",
                "reference": "AAOS: 0-20°"
            },
            # Alias para "flexion" -> usa plantarflexion
            "flexion": {
                "name": "Flexión Plantar de Tobillo",
                "normal_range": {"min": 0, "max": 50},
                "classification": {
                    "optimo": {"min": 45, "max": 50, "percentage": "≥90%", "color": "#4CAF50"},
                    "funcional": {"min": 37, "max": 44, "percentage": "75-89%", "color": "#2196F3"},
                    "limitado": {"min": 25, "max": 36, "percentage": "50-74%", "color": "#FF9800"},
                    "muy_limitado": {"min": 0, "max": 24, "percentage": "<50%", "color": "#f44336"}
                },
                "clinical_notes": "Importante para fase de despegue en marcha",
                "reference": "AAOS: 0-50°"
            }
        }
    }
}


def get_rom_classification(segment: str, exercise: str, angle: float) -> dict:
    """
    Clasifica un ángulo ROM según los estándares definidos.
    
    Sistema de Clasificación (basado en AAOS/Beighton Scale):
    - AUMENTADO: >100% del rango normal (Hiperlaxitud)
    - ÓPTIMO: 90-100% del rango normal máximo
    - FUNCIONAL: 70-89% del rango normal
    - LIMITADO: 50-69% del rango normal
    - MUY LIMITADO: <50% del rango normal
    
    Args:
        segment: Tipo de segmento (shoulder, elbow, knee, hip, ankle)
        exercise: Tipo de ejercicio (flexion, extension, abduction, etc.)
        angle: Ángulo medido en grados
    
    Returns:
        dict con clasificación, color, porcentaje y notas clínicas
    """
    if segment not in ROM_STANDARDS:
        return {"error": f"Segmento '{segment}' no encontrado"}
    
    segment_data = ROM_STANDARDS[segment]
    
    if exercise not in segment_data["exercises"]:
        return {"error": f"Ejercicio '{exercise}' no encontrado para {segment}"}
    
    exercise_data = segment_data["exercises"][exercise]
    classification = exercise_data["classification"]
    normal_range = exercise_data["normal_range"]
    
    # =========================================================================
    # CASO ESPECIAL: Hiperextensión de codo (ángulos negativos)
    # Referencias: Beighton Scale, AMA Guides 6th ed.
    # Ángulos negativos indican que el antebrazo pasó la línea vertical (0°)
    # Hasta -10° es normal en algunas personas, >-10° indica hiperlaxitud
    # =========================================================================
    if segment == "elbow" and exercise == "extension" and angle < 0:
        hyperextension_deg = abs(angle)  # Convertir a positivo para mostrar
        
        # Clasificar según grado de hiperextensión
        if hyperextension_deg <= 5:
            # Hiperextensión leve (0 a -5°): Normal en algunas personas
            return {
                "level": "aumentado",
                "level_display": "Aumentado (Hiperextensión Leve)",
                "color": "#F59E0B",  # Amarillo dorado
                "percentage_label": ">100%",
                "percentage_value": 100 + (hyperextension_deg * 10),  # 100-150%
                "angle": angle,  # Mantener negativo para indicar hiperextensión
                "normal_max": 0,
                "clinical_notes": f"Hiperextensión de {hyperextension_deg}°. {exercise_data['clinical_notes']}",
                "reference": "Beighton Scale: Hiperextensión ≤5° es variante normal",
                "is_hypermobile": True,
                "is_hyperextension": True
            }
        elif hyperextension_deg <= 10:
            # Hiperextensión moderada (-5° a -10°): Límite superior normal
            return {
                "level": "aumentado",
                "level_display": "Aumentado (Hiperextensión Moderada)",
                "color": "#F59E0B",  # Amarillo dorado
                "percentage_label": ">100%",
                "percentage_value": 100 + (hyperextension_deg * 10),  # 150-200%
                "angle": angle,
                "normal_max": 0,
                "clinical_notes": f"Hiperextensión de {hyperextension_deg}°. Dentro del rango de hiperlaxitud leve.",
                "reference": "Beighton Scale: Hiperextensión >10° suma 1 punto por codo",
                "is_hypermobile": True,
                "is_hyperextension": True
            }
        else:
            # Hiperextensión marcada (>-10°): Criterio Beighton positivo
            return {
                "level": "aumentado",
                "level_display": "Aumentado (Hiperlaxitud)",
                "color": "#FF6B35",  # Naranja más intenso
                "percentage_label": ">100%",
                "percentage_value": 100 + (hyperextension_deg * 10),  # >200%
                "angle": angle,
                "normal_max": 0,
                "clinical_notes": f"Hiperextensión de {hyperextension_deg}°. Criterio Beighton positivo para codo.",
                "reference": "Beighton Scale: Hiperextensión >10° indica hiperlaxitud ligamentosa significativa",
                "is_hypermobile": True,
                "is_hyperextension": True
            }
    
    # Determinar clasificación para casos normales
    angle = abs(angle)  # Usar valor absoluto para otros casos
    normal_max = normal_range["max"]
    
    # Calcular porcentaje respecto al máximo normal
    percentage = (angle / normal_max) * 100 if normal_max > 0 else 0
    
    # =========================================================================
    # CASO ESPECIAL: Extensión de codo/rodilla (lógica inversa)
    # En extensión, el objetivo es llegar a 0° (brazo/pierna recta).
    # Un ángulo ALTO (ej: 75°) significa LIMITACIÓN, no hiperlaxitud.
    # El "aumentado" solo aplica para ángulos NEGATIVOS (hiperextensión).
    # Por lo tanto, NO usar verificación de porcentaje >100% para estos casos.
    # =========================================================================
    is_extension_exercise = (
        (segment == "elbow" and exercise == "extension") or
        (segment == "knee" and exercise == "extension")
    )
    
    # =========================================================================
    # AUMENTADO (Hiperlaxitud): >100% del rango normal
    # Referencias: AAOS, Beighton Scale (Ann Rheum Dis. 1973)
    # NOTA: Usar >100.5% para evitar falsos positivos por precisión numérica
    # NOTA: NO aplica para extensión de codo/rodilla (ya manejado arriba)
    # =========================================================================
    if percentage > 100.5 and not is_extension_exercise:
        return {
            "level": "aumentado",
            "level_display": "Aumentado",
            "color": "#F59E0B",  # Amarillo dorado
            "percentage_label": ">100%",
            "percentage_value": round(percentage, 1),
            "angle": angle,
            "normal_max": normal_max,
            "clinical_notes": f"Hiperlaxitud detectada. {exercise_data['clinical_notes']}",
            "reference": f"AAOS/Beighton Scale: ROM > {normal_max}° indica posible hiperlaxitud ligamentosa",
            "is_hypermobile": True
        }
    
    # Redondear ángulo para clasificación (evita huecos entre categorías)
    # Ej: 5.8° se redondea a 6° para caer correctamente en la categoría
    angle_rounded = round(angle)
    
    # Clasificaciones normales (de mejor a peor)
    for level, ranges in classification.items():
        if ranges["min"] <= angle_rounded <= ranges["max"]:
            return {
                "level": level,
                "level_display": level.replace("_", " ").title(),
                "color": ranges["color"],
                "percentage_label": ranges["percentage"],
                "percentage_value": round(percentage, 1),
                "angle": angle,
                "normal_max": normal_max,
                "clinical_notes": exercise_data["clinical_notes"],
                "reference": exercise_data["reference"],
                "is_hypermobile": False
            }
    
    # Por defecto, muy limitado (ángulos muy bajos que no cayeron en ninguna categoría)
    return {
        "level": "muy_limitado",
        "level_display": "Muy Limitado",
        "color": "#f44336",
        "percentage_label": "<50%",
        "percentage_value": round(percentage, 1),
        "angle": angle,
        "normal_max": normal_max,
        "clinical_notes": exercise_data["clinical_notes"],
        "reference": exercise_data["reference"],
        "is_hypermobile": False
    }


def get_exercise_rom_info(segment: str, exercise: str):
    """
    Obtiene toda la información ROM de un ejercicio para mostrar en UI.
    
    Args:
        segment: Tipo de segmento (shoulder, elbow, knee, hip, ankle)
        exercise: Tipo de ejercicio (flexion, extension, etc.)
    
    Returns:
        dict con rangos, clasificaciones y bibliografía, o None si no existe
    """
    if segment not in ROM_STANDARDS:
        return None
    
    segment_data = ROM_STANDARDS[segment]
    
    if exercise not in segment_data["exercises"]:
        return None
    
    exercise_data = segment_data["exercises"][exercise]
    
    return {
        "segment_name": segment_data["segment_name"],
        "joint_type": segment_data["joint_type"],
        "bibliography": segment_data["bibliography"],
        "exercise_name": exercise_data["name"],
        "normal_range": exercise_data["normal_range"],
        "classification": exercise_data["classification"],
        "clinical_notes": exercise_data["clinical_notes"],
        "reference": exercise_data["reference"]
    }


def is_suspicious_measurement(segment: str, exercise: str, angle: float) -> dict:
    """
    Determina si una medición ROM es sospechosa y podría ser un error.
    
    Una medición se considera sospechosa si:
    1. Está clasificada como "muy_limitado" (muy por debajo de lo normal)
    2. O si el ángulo está muy lejos del rango esperado para el ejercicio
    
    Esto ayuda a advertir al usuario que revise la medición antes de guardar.
    
    Args:
        segment: Tipo de segmento (shoulder, elbow, knee, hip, ankle)
        exercise: Tipo de ejercicio (flexion, extension, etc.)
        angle: Ángulo medido en grados
    
    Returns:
        dict con:
            - is_suspicious: bool - True si la medición es sospechosa
            - reason: str - Razón de por qué es sospechosa
            - recommendation: str - Qué debería hacer el usuario
            - severity: str - 'warning' o 'error' según qué tan sospechoso
    """
    # Obtener clasificación ROM
    classification = get_rom_classification(segment, exercise, angle)
    
    if "error" in classification:
        return {
            "is_suspicious": False,
            "reason": None,
            "recommendation": None,
            "severity": None
        }
    
    level = classification.get("level", "")
    normal_max = classification.get("normal_max", 0)
    percentage = classification.get("percentage_value", 0)
    
    # =========================================================================
    # CASO 1: Clasificación "muy_limitado"
    # Un ROM muy limitado podría indicar:
    # a) Condición real del paciente (legítimo)
    # b) Error de medición (mal posicionamiento, no hizo el movimiento completo)
    # =========================================================================
    if level == "muy_limitado":
        # Para extensión de codo/rodilla, un ángulo alto significa contractura
        is_extension = exercise == "extension" and segment in ["elbow", "knee"]
        
        if is_extension:
            return {
                "is_suspicious": True,
                "reason": f"El ángulo medido ({abs(angle):.1f}°) indica un déficit de extensión significativo.",
                "recommendation": "Verifique que el sujeto intentó extender completamente. Si es correcto, podría indicar una contractura en flexión.",
                "severity": "warning",
                "expected_range": f"Extensión completa debería ser cerca de 0°",
                "measured_angle": angle
            }
        else:
            return {
                "is_suspicious": True,
                "reason": f"El ROM medido ({abs(angle):.1f}°) es muy inferior al rango funcional ({classification.get('percentage_label', '<50%')}).",
                "recommendation": "Verifique que el sujeto realizó el movimiento completo y estaba bien posicionado. Si el valor es correcto, considere documentar posibles causas.",
                "severity": "warning",
                "expected_range": f"Rango normal: 0° - {normal_max}°",
                "measured_angle": angle
            }
    
    # =========================================================================
    # CASO 2: Clasificación "aumentado"
    # Un ROM aumentado (por encima del rango normal) podría indicar:
    # a) Hiperlaxitud real del paciente (legítimo pero raro)
    # b) Error de medición (mal posicionamiento, compensación)
    # =========================================================================
    if level == "aumentado":
        return {
            "is_suspicious": True,
            "reason": f"El ROM medido ({abs(angle):.1f}°) supera el rango normal máximo ({normal_max}°).",
            "recommendation": "Verifique que no hubo compensación del tronco o pelvis. Si es correcto, el sujeto podría tener hiperlaxitud articular.",
            "severity": "warning",
            "expected_range": f"Rango normal: 0° - {normal_max}°",
            "measured_angle": angle
        }
    
    # =========================================================================
    # CASO 3: Ángulos fuera de rango físico razonable
    # Esto casi siempre indica error de medición
    # =========================================================================
    
    # Definir límites físicos razonables por ejercicio
    physical_limits = {
        "shoulder": {
            "flexion": {"max_reasonable": 200, "min_reasonable": 0},
            "extension": {"max_reasonable": 80, "min_reasonable": 0},
            "abduction": {"max_reasonable": 200, "min_reasonable": 0}
        },
        "elbow": {
            "flexion": {"max_reasonable": 160, "min_reasonable": 0},
            "extension": {"max_reasonable": 30, "min_reasonable": -20}  # Negativo = hiperextensión
        },
        "knee": {
            "flexion": {"max_reasonable": 160, "min_reasonable": 0},
            "extension": {"max_reasonable": 30, "min_reasonable": -15}
        },
        "hip": {
            "flexion": {"max_reasonable": 140, "min_reasonable": 0},
            "extension": {"max_reasonable": 40, "min_reasonable": 0},
            "abduction": {"max_reasonable": 60, "min_reasonable": 0},
            "adduction": {"max_reasonable": 40, "min_reasonable": 0}
        },
        "ankle": {
            "dorsiflexion": {"max_reasonable": 35, "min_reasonable": 0},
            "plantarflexion": {"max_reasonable": 60, "min_reasonable": 0}
        }
    }
    
    # Verificar si está fuera de límites físicos
    if segment in physical_limits and exercise in physical_limits[segment]:
        limits = physical_limits[segment][exercise]
        
        if angle > limits["max_reasonable"]:
            return {
                "is_suspicious": True,
                "reason": f"El ángulo medido ({angle:.1f}°) excede el límite físico razonable ({limits['max_reasonable']}°).",
                "recommendation": "Este valor probablemente es un error de medición. Verifique el posicionamiento del sujeto y repita la medición.",
                "severity": "error",
                "expected_range": f"Rango físico razonable: {limits['min_reasonable']}° - {limits['max_reasonable']}°",
                "measured_angle": angle
            }
        
        if angle < limits["min_reasonable"]:
            return {
                "is_suspicious": True,
                "reason": f"El ángulo medido ({angle:.1f}°) está por debajo del mínimo razonable ({limits['min_reasonable']}°).",
                "recommendation": "Verifique la calibración y el posicionamiento. Repita la medición si es necesario.",
                "severity": "error",
                "expected_range": f"Rango físico razonable: {limits['min_reasonable']}° - {limits['max_reasonable']}°",
                "measured_angle": angle
            }
    
    # =========================================================================
    # CASO 4: No es sospechoso - medición parece válida
    # =========================================================================
    return {
        "is_suspicious": False,
        "reason": None,
        "recommendation": None,
        "severity": None
    }
