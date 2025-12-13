/*
 * ============================================================================
 * ESP32 BIOTRACK - CONTROL DE PANEO (BLE)
 * ============================================================================
 * Control de servo para paneo horizontal de cámara
 * Comunicación: Bluetooth Low Energy (compatible con Web Bluetooth API)
 * 
 * Comandos (enviar como texto):
 *   L     - Izquierda -10°
 *   R     - Derecha +10°
 *   C     - Centro (90°)
 *   S     - Status
 *   P###  - Posición directa (ej: P090, P045, P180)
 * 
 * Respuestas:
 *   OK:###    - Confirmación con ángulo actual
 * ============================================================================
 */

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <ESP32Servo.h>

// =============================================================================
// CONFIGURACIÓN BLE
// =============================================================================

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define DEVICE_NAME         "BIOTRACK-PAN"

// =============================================================================
// CONFIGURACIÓN SERVO
// =============================================================================

#define SERVO_PIN       18
#define SERVO_MIN_US    500
#define SERVO_MAX_US    2400
#define ANGLE_MIN       0
#define ANGLE_MAX       180
#define ANGLE_CENTER    90
#define ANGLE_STEP      10

// =============================================================================
// VARIABLES GLOBALES
// =============================================================================

BLEServer* pServer = NULL;
BLECharacteristic* pCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;

Servo servoPan;
int currentAngle = ANGLE_CENTER;

// Forward declarations
void processCommand(String cmd);
void setAngle(int angle);
void sendResponse(String response);

// =============================================================================
// CALLBACKS BLE
// =============================================================================

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        Serial.println("[BLE] Cliente conectado");
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        Serial.println("[BLE] Cliente desconectado");
    }
};

class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        String value = pCharacteristic->getValue().c_str();
        
        if (value.length() > 0) {
            processCommand(value);
        }
    }
};

// =============================================================================
// FUNCIONES DE CONTROL
// =============================================================================

void processCommand(String cmd) {
    cmd.trim();
    cmd.toUpperCase();
    
    Serial.printf("[CMD] Recibido: '%s'\n", cmd.c_str());
    
    if (cmd.length() == 0) return;
    
    char firstChar = cmd.charAt(0);
    
    switch (firstChar) {
        case 'P': // Posición directa
            if (cmd.length() >= 2) {
                int angle = cmd.substring(1).toInt();
                setAngle(angle);
            }
            break;
            
        case 'L': // Izquierda
            setAngle(currentAngle - ANGLE_STEP);
            break;
            
        case 'R': // Derecha
            setAngle(currentAngle + ANGLE_STEP);
            break;
            
        case 'C': // Centro
            setAngle(ANGLE_CENTER);
            break;
            
        case 'S': // Status
            sendResponse("OK:" + String(currentAngle));
            break;
            
        default:
            sendResponse("ERR:UNKNOWN");
            break;
    }
}

void setAngle(int angle) {
    // Limitar rango
    if (angle < ANGLE_MIN) angle = ANGLE_MIN;
    if (angle > ANGLE_MAX) angle = ANGLE_MAX;
    
    currentAngle = angle;
    servoPan.write(currentAngle);
    
    Serial.printf("[SERVO] Movido a: %d°\n", currentAngle);
    sendResponse("OK:" + String(currentAngle));
}

void sendResponse(String response) {
    if (deviceConnected) {
        pCharacteristic->setValue(response.c_str());
        pCharacteristic->notify();
    }
    Serial.printf("[RESP] %s\n", response.c_str());
}

// =============================================================================
// SETUP
// =============================================================================

void setup() {
    Serial.begin(115200);
    delay(500);
    
    Serial.println("\n========================================");
    Serial.println("  ESP32 BIOTRACK - PAN CONTROL (BLE)");
    Serial.println("========================================");
    
    // Inicializar Servo
    ESP32PWM::allocateTimer(0);
    servoPan.setPeriodHertz(50);
    servoPan.attach(SERVO_PIN, SERVO_MIN_US, SERVO_MAX_US);
    servoPan.write(currentAngle);
    Serial.printf("[SERVO] GPIO %d, posición: %d°\n", SERVO_PIN, currentAngle);
    
    // Inicializar BLE
    BLEDevice::init(DEVICE_NAME);
    
    // Crear servidor BLE
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());
    
    // Crear servicio
    BLEService *pService = pServer->createService(SERVICE_UUID);
    
    // Crear característica (lectura, escritura, notificación)
    pCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID,
        BLECharacteristic::PROPERTY_READ   |
        BLECharacteristic::PROPERTY_WRITE  |
        BLECharacteristic::PROPERTY_NOTIFY |
        BLECharacteristic::PROPERTY_WRITE_NR
    );
    
    // Agregar descriptor para notificaciones
    pCharacteristic->addDescriptor(new BLE2902());
    pCharacteristic->setCallbacks(new MyCallbacks());
    pCharacteristic->setValue("OK:90");
    
    // Iniciar servicio
    pService->start();
    
    // Iniciar advertising
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06);
    pAdvertising->setMinPreferred(0x12);
    BLEDevice::startAdvertising();
    
    Serial.println("[BLE] Activo - Nombre: " DEVICE_NAME);
    Serial.println("[BLE] Esperando conexión...");
    Serial.println("========================================\n");
}

// =============================================================================
// LOOP
// =============================================================================

void loop() {
    // Reconectar advertising si se desconectó
    if (!deviceConnected && oldDeviceConnected) {
        delay(500);
        pServer->startAdvertising();
        Serial.println("[BLE] Reiniciando advertising...");
        oldDeviceConnected = deviceConnected;
    }
    
    if (deviceConnected && !oldDeviceConnected) {
        oldDeviceConnected = deviceConnected;
    }
    
    delay(10);
}
