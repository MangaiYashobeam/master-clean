#include "Sensor.h"
#include "Motor.h"
#include "Funciones.h"
#define FCA 7  // Fin de carrera que identifica si esta conectado el fin de carrera
#define FCB 8  // FIn de carrera que identifica si llego el sistema al inicio
int codigo = 0; ///3-> fin de carrera desconectado
///// 2-> error de altura menoar a la del sistema
int Derror = 2; /// en milimetros
int Error_ = 0;
float KP = 13.0;
float controlP = 0.0;
void setup()
{
  // put your setup code here, to run once:
  iniciarMotor();
  iniciarSensor();

  Serial.begin(115200);
  pinMode(FCA, INPUT_PULLUP);/// Normalmente abierto
  pinMode(FCB, INPUT_PULLUP);/// Normalmente cerrado
  distancia = AlturaInicial;
}

void loop()
{
  // put your main code here, to run repeatedly:

  switch (valor[0])
  {
    case 0:
      PosicionInicial();
      valor[0] = 2;
      enviarAltura();
      break;
    case 1:
      if (valor[1] > AlturaInicial)
      {
        IrPosicion(valor[1]);
      }
      else
      {
        codigo = 2;
      }
      valor[0] = 2;
      enviarAltura();
      break;
    case 2:/// detener el sistema/// NOta esto usarlo en el control P
      girar (0);
      codigo = 0;
      enviarAltura();
      valor[0] = 4;
      break;
  }
  //enviarAltura();
}
///
void PosicionInicial()
{
  //Serial.print(digitalRead(FCB));
  //Serial.println(digitalRead(FCA));
  //Serial.println("BUscando la posicion inicial");
  if (!digitalRead(FCB))/// Esta cerrado el fin de carrera? esta conectado el fin de carrera
  {

    // mientras no llegue al inicio
    while (digitalRead(FCA))
    {
      girar(-100);
      
      // Pequeña pausa para verificar serial más frecuentemente
      delay(10);
      
      // Verificar si llega comando STOP durante el movimiento
      // serialEvent() puede haber procesado el comando, verificar valor[0]
      if (valor[0] == 2)
      {
        girar(0);
        MedirDistancia();  // Medir altura actual antes de salir
        return;
      }
      
      // También verificar directamente el serial por si acaso
      if (Serial.available())
      {
        mensaje = Serial.readString();
        decodificar();
        if (valor[0] == 2)
        {
          girar(0);
          MedirDistancia();  // Medir altura actual antes de salir
          return;
        }
      }
    }
    girar(0);
    distancia = AlturaInicial;
    cuentas = 0;
    // Serial.println("Llego a la posicion inicial");
    return;
  }
  else
  { // Entonces esta abierto, pero la otra terminal esta cerrado
    if (!digitalRead(FCA))//Esta cerrado?
    {
      // Quiere decir que esta en su posicion inicial
      girar(0);
      distancia = AlturaInicial;
      cuentas = 0;
      return;
    }
    /// Tambien esta abierto, no pueden estar los dos abiertos
    // por tanto no esta conectado el fin de carrera
    else
    {
      codigo = 3;
      return;
    }
  }
}

//////////
void IrPosicion(int Altura)
{
  //Serial.println("moviendo a la altura seleccionada");

  MedirDistancia();
  Error_ = float(Altura) - distancia;
  while (abs(Error_) > Derror)
  {
    MedirDistancia();
    Error_ = Altura - distancia;
    //Serial.println(Error_);
    controlP = KP * Error_;

    if (controlP > 100)
      controlP = 100;
    if (controlP < -100)
      controlP = -100;

    girar (controlP);
    
    // Pequeña pausa para verificar serial más frecuentemente
    delay(10);

    if (Serial.available())
    {
      mensaje = Serial.readString();
      decodificar();
      if (valor[0] == 2)
      {
        girar(0);
        MedirDistancia();  // Medir altura actual antes de salir
        return;
      }
      //Serial.println(valor[1]);
    }

    //Serial.println(cuentas);

  }
  girar (0);
  codigo = 0;
  //Serial.println("Se llego a altura seleccionada");

}

/////////////////

void enviarAltura()
{
  Serial.print(codigo);
  Serial.print(",");
  Serial.println(int (distancia));
}


////////

void serialEvent()
{
  if (Serial.available())
  {
    mensaje = Serial.readString();
    decodificar();
    //Serial.println(valor[1]);
  }
}