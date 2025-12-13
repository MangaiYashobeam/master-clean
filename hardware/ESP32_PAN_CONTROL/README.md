# ESP32 Control de Paneo - BIOTRACK

## Descripción
Control simple de servo horizontal para paneo de cámara.
Comunicación vía **Bluetooth Low Energy (BLE)** compatible con Web Bluetooth API de Chrome.

## Hardware Requerido
- ESP32 (cualquier variante con BLE)
- Servo motor (MG995 o similar)
- Alimentación para servo (5V, 1A mínimo)

## Conexiones
| ESP32 | Servo |
|-------|-------|
| GPIO 18 | Signal (naranja/amarillo) |
| GND | GND (marrón) |
| 5V/VIN | VCC (rojo) - usar fuente externa si es necesario |

## Instalación en Arduino IDE
1. Abrir `ESP32_PAN_CONTROL_BLE.ino`
2. Instalar librería: **ESP32Servo** (por Kevin Harrington)
3. **IMPORTANTE:** Eliminar librería `ESP32_BLE_Arduino` si existe (causa conflictos)
4. Seleccionar placa: **ESP32 Dev Module**
5. Partition Scheme: **Huge APP (3MB No OTA/1MB SPIFFS)**
6. Subir el código

## Uso desde el Navegador
1. El navegador debe ser **Chrome** (soporta Web Bluetooth API)
2. En la interfaz de BIOTRACK, ir a cualquier segmento
3. En el panel "Control de Paneo", click en **"Conectar"**
4. Seleccionar dispositivo **BIOTRACK-PAN** de la lista
5. Usar el slider o botones para controlar el servo
6. Al cambiar de segmento, se reconecta automáticamente

## Comandos BLE
| Comando | Descripción | Respuesta |
|---------|-------------|-----------|
| `P###` | Posición directa (ej: P090, P045, P180) | `OK:###` |
| `L` | Izquierda -10° | `OK:###` |
| `R` | Derecha +10° | `OK:###` |
| `C` | Centro (90°) | `OK:90` |
| `S` | Status | `OK:###` (ángulo actual) |

## Características BLE
- **Service UUID:** `4fafc201-1fb5-459e-8fcc-c5c9c331914b`
- **Characteristic UUID:** `beb5483e-36e1-4688-b7f5-ea07361b26a8`
- **Nombre del dispositivo:** `BIOTRACK-PAN`

## Formato de Respuesta
- `OK:###` - Operación exitosa, ### es el ángulo actual
- `ERR:mensaje` - Error

## Solución de Problemas

### "BIOTRACK-PAN no aparece en la lista"
- Asegurar que el ESP32 está encendido
- El LED del ESP32 debe estar encendido
- Reiniciar el ESP32
- Verificar que no esté conectado a otro dispositivo

### "El servo no se mueve"
- Verificar conexiones
- Asegurar alimentación suficiente para el servo (fuente externa recomendada)
- Revisar que el GPIO sea el correcto (18)

### "Error de compilación: BLEDevice.h"
- Eliminar la carpeta `ESP32_BLE_Arduino` de `Documentos/Arduino/libraries/`
- Arduino usará la librería BLE nativa del ESP32 core

### "Error de conexión en Chrome"
- Chrome requiere HTTPS o localhost para Web Bluetooth API
- La app en localhost funciona correctamente
- Verificar que el ESP32 no esté conectado a otro dispositivo

## Notas
- El servo tiene rango de 0° a 180°
- 90° es la posición central
- Los comandos L/R mueven 10° cada vez
- El slider envía posición exacta (P###)
- La conexión persiste al cambiar de segmento (reconexión automática)

## Notas
- El servo tiene rango de 0° a 180°
- 90° es la posición central
- Los comandos L/R mueven 10° cada vez
- El slider envía posición exacta (P###)
