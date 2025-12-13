/// puertos del encoder
float AlturaInicial = 375.0; ////  en milimetros (37 cm desde el suelo)
int sensor = 3, sentido = 2;
float factor = 197;
long cuentas = 0, pulsos = 0;
float distancia = AlturaInicial;// milimetros
float distancia2 = AlturaInicial;
//float referencia=150.0; // milimetros
void Encoder();
////
void iniciarSensor()
{
  ////// calculo de factor de distancia
  pinMode(sentido, INPUT);
  pinMode(sensor, INPUT);
  attachInterrupt(digitalPinToInterrupt(sensor), Encoder, FALLING);
}
/// interrupcion
void Encoder()
{
  if (digitalRead(sentido))
  {
    cuentas = cuentas + 1;
  }
  else
  {
    cuentas = cuentas - 1;
  }
}
////////////////////////////////////
float MedirDistancia()
{
  pulsos = cuentas;
  distancia = pulsos / factor + AlturaInicial;
  //distancia = 0.9513048*distancia+1.9238539;
  distancia=0.0000083*pow(distancia,2)+1.0282274*distancia-5.3786964;  
  return distancia;
}
//////////////////////////////////////////