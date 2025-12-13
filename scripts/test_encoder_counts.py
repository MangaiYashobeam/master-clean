"""
🔍 TEST DE ENCODER - BIOTRACK
==============================
Este script monitorea los pulsos del encoder en tiempo real
para diagnosticar si está contando correctamente.

Ejecutar:
    python scripts/test_encoder_counts.py
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

def test_encoder():
    port = find_arduino_port()
    if not port:
        print("❌ No se encontró Arduino")
        return
    
    print(f"✅ Arduino en {port}")
    
    try:
        ser = serial.Serial(port, 115200, timeout=0.5)
        time.sleep(2)
        ser.reset_input_buffer()
        
        print("\n" + "=" * 60)
        print("🔍 TEST DE ENCODER")
        print("=" * 60)
        
        print("""
INSTRUCCIONES:
1. Mueve la cámara MANUALMENTE (con la mano, sin motor)
2. Observa si los PULSOS cambian
3. Si los pulsos NO cambian → problema de hardware/conexión
4. Si los pulsos SÍ cambian → el encoder funciona

Presiona Ctrl+C para salir
        """)
        
        input("Presiona ENTER para comenzar el monitoreo...")
        
        print("\n📊 Monitoreando encoder... (mueve la cámara manualmente)")
        print("-" * 60)
        
        # Primero, ir a HOME para resetear cuentas
        print("Enviando HOME para resetear contador...")
        ser.write(b"0.0\n")
        time.sleep(3)
        
        # Leer cualquier respuesta pendiente
        while ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"   {line}")
        
        print("\n🎯 Ahora mueve la cámara MANUALMENTE y observa los pulsos:")
        print("-" * 60)
        
        last_cuentas = 0
        same_count = 0
        
        while True:
            # Usar comando ENCODER para ver datos crudos
            ser.write(b"ENCODER\n")
            time.sleep(0.3)
            
            while ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if line.startswith("ENCODER,"):
                    # Parsear: ENCODER,cuentas=X,pulsos=X,distancia=X,factor=X
                    print(f"📊 {line}")
                    
                    # Extraer cuentas para ver si cambian
                    try:
                        parts = line.split(",")
                        for part in parts:
                            if part.startswith("cuentas="):
                                cuentas = int(part.split("=")[1])
                                if cuentas != last_cuentas:
                                    diff = cuentas - last_cuentas
                                    print(f"   ✅ ¡Encoder detectó movimiento! Δcuentas = {diff}")
                                    last_cuentas = cuentas
                                    same_count = 0
                                else:
                                    same_count += 1
                    except:
                        pass
                        
                elif line.startswith("STATUS,"):
                    parts = line.split(",")
                    if len(parts) >= 3:
                        height = int(parts[2])
                        print(f"📍 Altura Arduino: {height}mm")
                        
                elif line.startswith("DEBUG") or line.startswith("READY"):
                    print(f"🔧 {line}")
            
            time.sleep(0.2)
            
    except KeyboardInterrupt:
        print("\n\n✅ Test terminado")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'ser' in locals():
            ser.close()

if __name__ == "__main__":
    test_encoder()
