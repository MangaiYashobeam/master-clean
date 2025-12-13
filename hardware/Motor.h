#include <TimerOne.h>
#define IN1 9
#define IN2 10

void iniciarMotor()
{
  Timer1.initialize(40);  // 40 us = 25 kHz
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  Timer1.pwm(IN1, 0);//1023
  Timer1.pwm(IN2, 0);//1023
}

void girar(int velocidad)
{
  if (velocidad > 0 && velocidad <101)
  {    
    Timer1.pwm(IN1, map(abs(velocidad),0,100,600,1023));//1023
    Timer1.pwm(IN2, 0);//1023
    return;
  }
  if (abs(velocidad) > 0 && abs(velocidad) <101)
  {    
    Timer1.pwm(IN2, map(abs(velocidad),0,100,600,1023));//1023
    Timer1.pwm(IN1, 0);//1023
    return;
  }
  Timer1.pwm(IN1, 0);//1023
  Timer1.pwm(IN2, 0);//1023
}