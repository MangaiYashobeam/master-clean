"""
📏 CALIBRACIÓN DEL ENCODER - BIOTRACK
======================================
Script para calibrar el factor de conversión del encoder.

PROCEDIMIENTO:
1. Coloca la cámara en una posición conocida (medir con cinta métrica)
2. Mueve manualmente o con el motor a otra posición conocida
3. El script calculará el factor correcto

Ejecutar:
    python scripts/calibrar_encoder.py

Autor: BIOTRACK Team
Fecha: 2025-12-03
"""

import serial
import serial.tools.list_ports
import time

def find_arduino_port():
    """Busca el puerto del Arduino"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        desc = port.description.lower()
        if any(x in desc for x in ['ch340', 'ch341', 'arduino', 'usb-serial']):
            return port.device
    return None

def calibrar():
    port = find_arduino_port()
    if not port:
        print("❌ No se encontró Arduino")
        return
    
    print(f"✅ Arduino en {port}")
    
    try:
        ser = serial.Serial(port, 115200, timeout=2)
        time.sleep(2)
        ser.reset_input_buffer()
        
        print("\n" + "=" * 50)
        print("📏 CALIBRACIÓN DEL ENCODER")
        print("=" * 50)
        
        print("""
INSTRUCCIONES:
1. Primero iremos a posición inicial (HOME)
2. Mide con cinta métrica la altura REAL de la cámara desde el suelo
3. Luego moveremos la cámara a otra posición
4. Mide nuevamente la altura REAL
5. Con esos datos calcularemos el factor correcto
        """)
        
        input("\nPresiona ENTER para ir a HOME...")
        
        # Ir a HOME
        ser.write(b"0.0\n")
        print("📤 Enviando comando HOME...")
        
        # Esperar a que termine con timeout
        time.sleep(1)
        intentos = 0
        max_intentos = 30  # Máximo 15 segundos (30 * 0.5s)
        
        while intentos < max_intentos:
            ser.reset_input_buffer()  # Limpiar buffer antes de pedir estado
            ser.write(b"STATUS\n")
            time.sleep(0.3)
            
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                print(f"   Recibido: {line}")
                
                if line.startswith("STATUS,"):
                    parts = line.split(",")
                    if len(parts) >= 3:
                        codigo = int(parts[1])
                        altura_arduino = int(parts[2])
                        print(f"   Estado: código={codigo}, altura_arduino={altura_arduino}mm")
                        
                        if codigo == 0:  # OK, terminó de moverse
                            break
                        elif codigo != 1:  # Algún error
                            print(f"   ⚠️ Error código {codigo}")
                            break
            
            intentos += 1
            time.sleep(0.5)
        
        if intentos >= max_intentos:
            print("\n⚠️ Timeout esperando HOME. Continuando de todos modos...")
        
        print("\n✅ Cámara en posición HOME (o cerca)")
        
        # Pedir altura real medida
        print("\n📏 MIDE LA ALTURA REAL DE LA CÁMARA DESDE EL SUELO")
        altura_real_1 = float(input("Altura REAL en cm (ej: 25.5): "))
        altura_real_1_mm = altura_real_1 * 10
        
        # Obtener pulsos actuales (reseteados a 0 en home)
        pulsos_1 = 0  # En home, los pulsos se resetean
        
        print(f"\n📊 Punto 1: Altura real = {altura_real_1_mm}mm, Pulsos = {pulsos_1}")
        
        # Ahora mover a otra posición
        print("\n" + "-" * 40)
        altura_objetivo = input("¿A qué altura quieres mover? (en mm, ej: 800): ")
        
        comando = f"1.{altura_objetivo}\n"
        ser.write(comando.encode())
        print(f"📤 Enviando comando: 1.{altura_objetivo}")
        
        # Esperar movimiento con timeout
        time.sleep(1)
        altura_arduino_final = 0
        intentos = 0
        max_intentos = 60  # Máximo 30 segundos
        
        while intentos < max_intentos:
            ser.reset_input_buffer()
            ser.write(b"STATUS\n")
            time.sleep(0.3)
            
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                print(f"   Recibido: {line}")
                
                if line.startswith("STATUS,"):
                    parts = line.split(",")
                    if len(parts) >= 3:
                        codigo = int(parts[1])
                        altura_arduino_final = int(parts[2])
                        print(f"   Estado: código={codigo}, altura_arduino={altura_arduino_final}mm")
                        
                        if codigo == 0:
                            break
                        elif codigo != 1:  # Error
                            print(f"   ⚠️ Error código {codigo}")
                            break
            
            intentos += 1
            time.sleep(0.5)
        
        if intentos >= max_intentos:
            print("\n⚠️ Timeout esperando movimiento.")
        
        print(f"\n✅ Movimiento completado. Arduino reporta: {altura_arduino_final}mm")
        
        # Pedir altura real medida
        print("\n📏 MIDE LA ALTURA REAL DE LA CÁMARA AHORA")
        altura_real_2 = float(input("Altura REAL en cm: "))
        altura_real_2_mm = altura_real_2 * 10
        
        # Calcular
        print("\n" + "=" * 50)
        print("📊 RESULTADOS DE CALIBRACIÓN")
        print("=" * 50)
        
        # =====================================================================
        # CONFIGURACIÓN - DEBE COINCIDIR CON Sensor.h
        # =====================================================================
        ALTURA_INICIAL_CODIGO = 375.0  # mm - AlturaInicial en Sensor.h
        FACTOR_ACTUAL = 50.0           # factor en Sensor.h
        # =====================================================================
        
        print(f"\n📋 Configuración actual en Sensor.h:")
        print(f"   AlturaInicial = {ALTURA_INICIAL_CODIGO} mm")
        print(f"   factor = {FACTOR_ACTUAL}")
        
        # Cálculos
        desplazamiento_real = altura_real_2_mm - altura_real_1_mm
        
        # El Arduino CREE que está en altura_arduino_final
        # Pero REALMENTE está en altura_real_2_mm
        # 
        # La fórmula es: distancia = pulsos/factor + AlturaInicial
        # Por tanto: pulsos = (distancia - AlturaInicial) * factor
        #
        # Con el factor actual, Arduino calculó:
        #   altura_arduino_final = pulsos/FACTOR_ACTUAL + ALTURA_INICIAL_CODIGO
        #   pulsos = (altura_arduino_final - ALTURA_INICIAL_CODIGO) * FACTOR_ACTUAL
        #
        # Pero la realidad es que esos mismos pulsos corresponden a:
        #   altura_real_2_mm = pulsos/FACTOR_CORRECTO + altura_real_1_mm
        #   FACTOR_CORRECTO = pulsos / (altura_real_2_mm - altura_real_1_mm)
        #
        # Entonces:
        #   FACTOR_CORRECTO = (altura_arduino_final - ALTURA_INICIAL_CODIGO) * FACTOR_ACTUAL / desplazamiento_real
        
        desplazamiento_arduino = altura_arduino_final - ALTURA_INICIAL_CODIGO
        pulsos_estimados = desplazamiento_arduino * FACTOR_ACTUAL
        
        print(f"\n📊 Mediciones:")
        print(f"   Altura real en HOME: {altura_real_1_mm} mm ({altura_real_1} cm)")
        print(f"   Altura real después de mover: {altura_real_2_mm} mm ({altura_real_2} cm)")
        print(f"   Arduino reportó altura final: {altura_arduino_final} mm")
        print(f"\n📊 Cálculos:")
        print(f"   Desplazamiento REAL: {desplazamiento_real} mm")
        print(f"   Desplazamiento según Arduino: {desplazamiento_arduino} mm")
        print(f"   Pulsos estimados: {pulsos_estimados:.0f}")
        
        if desplazamiento_real > 0:
            # Calcular el factor correcto
            nuevo_factor = pulsos_estimados / desplazamiento_real
            
            print(f"\n🎯 NUEVO FACTOR CALCULADO: {nuevo_factor:.1f}")
            
            # Verificación: con este factor, ¿qué altura reportaría?
            altura_verificacion = pulsos_estimados / nuevo_factor + altura_real_1_mm
            print(f"   Verificación: {pulsos_estimados:.0f} / {nuevo_factor:.1f} + {altura_real_1_mm} = {altura_verificacion:.1f} mm")
            
            # Nueva altura inicial (debe ser la altura real medida en HOME)
            nueva_altura_inicial = altura_real_1_mm
            
            print("\n" + "=" * 50)
            print("✏️  CAMBIOS A HACER EN Sensor.h:")
            print("=" * 50)
            print(f"""
float AlturaInicial = {nueva_altura_inicial:.1f};  // mm ({nueva_altura_inicial/10:.1f} cm)
float factor = {nuevo_factor:.1f};
            """)
            
            print("⚠️  IMPORTANTE:")
            print("   1. Cambia estos valores en Sensor.h")
            print("   2. Sube el código al Arduino")
            print("   3. Vuelve a ejecutar este script para verificar")
            print("   4. Si está correcto, el desplazamiento REAL ≈ desplazamiento Arduino")
        else:
            print("\n⚠️ No hubo desplazamiento real, no se puede calcular el factor")
        
        ser.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    calibrar()
