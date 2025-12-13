"""
🔧 TEST DIRECTO DE ARDUINO
===========================
Script simple para probar la comunicación con Arduino
sin usar el sistema completo de Flask.

Ejecutar:
    python scripts/test_arduino_direct.py

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

def test_arduino():
    # Buscar puerto
    port = find_arduino_port()
    if not port:
        print("❌ No se encontró Arduino")
        print("\nPuertos disponibles:")
        for p in serial.tools.list_ports.comports():
            print(f"  - {p.device}: {p.description}")
        return
    
    print(f"✅ Arduino encontrado en {port}")
    
    try:
        # Conectar
        ser = serial.Serial(port, 115200, timeout=2)
        time.sleep(2)  # Esperar que Arduino reinicie
        
        # Limpiar buffer
        ser.reset_input_buffer()
        
        print("\n📡 Conexión establecida")
        print("-" * 40)
        
        # Leer mensaje READY inicial (puede que ya se haya perdido)
        time.sleep(0.5)
        while ser.in_waiting:
            ready = ser.readline().decode('utf-8', errors='ignore').strip()
            if ready:
                print(f"Arduino dice: {ready}")
        
        while True:
            print("\n📋 COMANDOS DISPONIBLES:")
            print("  1. STATUS - Ver estado actual")
            print("  2. MOVE <altura> - Mover a altura (ej: MOVE 500)")
            print("  3. STOP - Detener motor INMEDIATAMENTE")
            print("  4. HOME - Ir a posición inicial")
            print("  5. RAW <comando> - Enviar comando raw")
            print("  6. MONITOR - Monitorear estado continuamente")
            print("  0. SALIR")
            
            cmd = input("\n> ").strip().upper()
            
            if cmd == "0" or cmd == "SALIR":
                break
            
            elif cmd == "STATUS" or cmd == "1":
                ser.write(b"STATUS\n")
                print("📤 Enviado: STATUS")
                
            elif cmd.startswith("MOVE") or cmd.startswith("2"):
                parts = cmd.split()
                if len(parts) >= 2:
                    altura = parts[1]
                    comando = f"1.{altura}\n"
                    ser.write(comando.encode())
                    print(f"📤 Enviado: 1.{altura}")
                else:
                    altura = input("Altura en mm (200-1700): ")
                    comando = f"1.{altura}\n"
                    ser.write(comando.encode())
                    print(f"📤 Enviado: 1.{altura}")
                    
            elif cmd == "STOP" or cmd == "3":
                ser.write(b"2.0\n")
                print("📤 Enviado: 2.0 (STOP)")
                
            elif cmd == "HOME" or cmd == "4":
                ser.write(b"0.0\n")
                print("📤 Enviado: 0.0 (HOME)")
                
            elif cmd.startswith("RAW") or cmd.startswith("5"):
                parts = cmd.split(maxsplit=1)
                if len(parts) >= 2:
                    raw_cmd = parts[1]
                else:
                    raw_cmd = input("Comando raw: ")
                ser.write(f"{raw_cmd}\n".encode())
                print(f"📤 Enviado: {raw_cmd}")
            
            elif cmd == "MONITOR" or cmd == "6":
                print("\n📊 MODO MONITOR - Presiona Ctrl+C para salir")
                print("   Escribe 'S' + ENTER para enviar STOP durante el monitoreo")
                print("-" * 40)
                try:
                    import threading
                    import sys
                    import select
                    
                    stop_flag = False
                    
                    while not stop_flag:
                        # Pedir estado
                        ser.write(b"STATUS\n")
                        time.sleep(0.3)
                        
                        if ser.in_waiting:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if line.startswith("STATUS,"):
                                parts = line.split(",")
                                if len(parts) >= 3:
                                    codigo = int(parts[1])
                                    altura = int(parts[2])
                                    codigos = {0: "OK", 1: "⚡Moviendo", 2: "❌Error", 3: "❌FC", 4: "❌Timeout"}
                                    estado = codigos.get(codigo, '?')
                                    barra = "█" * (altura // 50)
                                    print(f"\r[{estado:12}] Altura: {altura:4}mm |{barra}", end="", flush=True)
                        
                        # Verificar si hay input del usuario (solo en Windows)
                        import msvcrt
                        if msvcrt.kbhit():
                            key = msvcrt.getch().decode('utf-8', errors='ignore').upper()
                            if key == 'S':
                                ser.write(b"2.0\n")
                                print("\n🛑 STOP enviado!")
                            elif key == 'Q':
                                stop_flag = True
                        
                        time.sleep(0.2)
                        
                except KeyboardInterrupt:
                    print("\n\n📊 Monitor detenido")
                except ImportError:
                    # Fallback sin msvcrt
                    while True:
                        ser.write(b"STATUS\n")
                        time.sleep(0.5)
                        if ser.in_waiting:
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            print(f"  {line}")
                continue
            
            else:
                print("❓ Comando no reconocido")
                continue
            
            # Esperar y mostrar respuestas
            time.sleep(0.3)  # Dar tiempo al Arduino
            
            responses = []
            timeout_start = time.time()
            while time.time() - timeout_start < 5:  # 5 segundos máximo
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        responses.append(line)
                        print(f"📥 Respuesta: {line}")
                        
                        # Parsear STATUS
                        if line.startswith("STATUS,"):
                            parts = line.split(",")
                            if len(parts) >= 3:
                                codigo = int(parts[1])
                                altura = int(parts[2])
                                codigos = {0: "OK", 1: "Moviendo", 2: "Error altura", 3: "FC desconectado", 4: "Timeout"}
                                print(f"   → Código: {codigo} ({codigos.get(codigo, '?')})")
                                print(f"   → Altura actual: {altura} mm")
                        
                        # Si codigo != 1 (no está moviendo), podemos salir del loop
                        if line.startswith("STATUS,0,") or line.startswith("STATUS,2,") or \
                           line.startswith("STATUS,3,") or line.startswith("STATUS,4,"):
                            break
                else:
                    time.sleep(0.1)
            
            if not responses:
                print("⚠️  No hubo respuesta del Arduino")
        
        ser.close()
        print("\n👋 Conexión cerrada")
        
    except serial.SerialException as e:
        print(f"❌ Error de comunicación: {e}")
    except KeyboardInterrupt:
        print("\n👋 Interrumpido por usuario")

if __name__ == "__main__":
    print("=" * 50)
    print("🔧 TEST DIRECTO DE ARDUINO - BIOTRACK")
    print("=" * 50)
    test_arduino()
