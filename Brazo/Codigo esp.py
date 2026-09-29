/*
   Control de brazo robótico con ESP32 + joystick de 5 pines

   Joystick:
   VRx -> GPIO 34
   VRy -> GPIO 35
   SW  -> GPIO 32
   VCC -> 3V3
   GND -> GND

   Servos:
   Base  (joint_1)      -> GPIO 18
   Brazo (joint_2)      -> GPIO 19
   Pinza (joint_gripper)-> GPIO 23

   IMPORTANTE:
   - Alimentar servos con fuente externa de 5 V.
   - Conectar GND de la fuente de servos con GND del ESP32.
   - No conectar las señales analógicas del joystick a 5 V.
*/

#include <ESP32Servo.h>

// ---------------------- Pines del joystick ----------------------
const int PIN_JOYSTICK_X  = 34;   // VRx: ADC1
const int PIN_JOYSTICK_Y  = 35;   // VRy: ADC1
const int PIN_JOYSTICK_SW = 32;   // Pulsador del joystick

// ------------------------ Pines de servos -----------------------
const int PIN_SERVO_BASE  = 18;   // joint_1
const int PIN_SERVO_BRAZO = 19;   // joint_2
const int PIN_SERVO_PINZA = 23;   // joint_gripper

// ---------------------- Objetos de servo ------------------------
Servo servoBase;
Servo servoBrazo;
Servo servoPinza;

// -------------------- Límites mecánicos seguros -----------------
// Ajusta estos valores después de probar físicamente tu brazo.
const int BASE_MIN  = 10;
const int BASE_MAX  = 170;

const int BRAZO_MIN = 20;
const int BRAZO_MAX = 160;

// En muchos mecanismos: ángulo pequeño = pinza abierta,
// ángulo grande = pinza cerrada. Invierte si tu pinza funciona al revés.
const int PINZA_ABIERTA = 20;
const int PINZA_CERRADA = 85;

// ---------------------- Posiciones iniciales --------------------
int anguloBase  = 90;
int anguloBrazo = 90;
int anguloPinza = PINZA_ABIERTA;

// ---------------------- Parámetros de control -------------------
const int ADC_MIN = 0;
const int ADC_MAX = 4095;       // ADC de 12 bits del ESP32

const int ZONA_MUERTA = 250;    // Evita vibraciones cerca del centro
const int CENTRO_ADC  = 2048;

const int PASO_BASE  = 1;       // Grados por ciclo de control
const int PASO_BRAZO = 1;

const unsigned long PERIODO_CONTROL_MS = 20;
const unsigned long DEBOUNCE_MS = 250;

bool pinzaCerrada = false;
bool ultimoEstadoBoton = HIGH;

unsigned long tiempoAnterior = 0;
unsigned long ultimoCambioBoton = 0;

// Lee varias veces y promedia para reducir ruido del ADC
int leerJoystickPromedio(int pin) {
  const int muestras = 8;
  long suma = 0;

  for (int i = 0; i < muestras; i++) {
    suma += analogRead(pin);
    delayMicroseconds(300);
  }

  return suma / muestras;
}

// Convierte lectura ADC a dirección: -1, 0 o +1
int direccionJoystick(int valorADC) {
  if (valorADC > CENTRO_ADC + ZONA_MUERTA) {
    return 1;
  }

  if (valorADC < CENTRO_ADC - ZONA_MUERTA) {
    return -1;
  }

  return 0;
}

void moverBaseConJoystick(int lecturaX) {
  int direccion = direccionJoystick(lecturaX);

  if (direccion != 0) {
    anguloBase += direccion * PASO_BASE;
    anguloBase = constrain(anguloBase, BASE_MIN, BASE_MAX);

    servoBase.write(anguloBase);
  }
}

void moverBrazoConJoystick(int lecturaY) {
  int direccion = direccionJoystick(lecturaY);

  if (direccion != 0) {
    anguloBrazo += direccion * PASO_BRAZO;
    anguloBrazo = constrain(anguloBrazo, BRAZO_MIN, BRAZO_MAX);

    servoBrazo.write(anguloBrazo);
  }
}

void controlarPinza() {
  bool estadoBoton = digitalRead(PIN_JOYSTICK_SW);

  // Detectar flanco de bajada: botón presionado
  if (ultimoEstadoBoton == HIGH && estadoBoton == LOW) {
    if (millis() - ultimoCambioBoton > DEBOUNCE_MS) {
      pinzaCerrada = !pinzaCerrada;

      if (pinzaCerrada) {
        anguloPinza = PINZA_CERRADA;
      } else {
        anguloPinza = PINZA_ABIERTA;
      }

      servoPinza.write(anguloPinza);

      ultimoCambioBoton = millis();
    }
  }

  ultimoEstadoBoton = estadoBoton;
}

void imprimirEstado(int x, int y) {
  Serial.print("X: ");
  Serial.print(x);

  Serial.print(" | Y: ");
  Serial.print(y);

  Serial.print(" | Base: ");
  Serial.print(anguloBase);

  Serial.print(" | Brazo: ");
  Serial.print(anguloBrazo);

  Serial.print(" | Pinza: ");
  Serial.println(pinzaCerrada ? "CERRADA" : "ABIERTA");
}

void setup() {
  Serial.begin(115200);

  // Configuración de entradas
  pinMode(PIN_JOYSTICK_X, INPUT);
  pinMode(PIN_JOYSTICK_Y, INPUT);
  pinMode(PIN_JOYSTICK_SW, INPUT_PULLUP);

  // Resolución del ADC: valores entre 0 y 4095
  analogReadResolution(12);

  // Rango de medida adecuado para señales cercanas a 0 - 3.3 V
  analogSetAttenuation(ADC_11db);

  // Configuración de los pulsos PWM para servos.
  // El rango 500-2400 us suele cubrir aproximadamente 0° a 180°.
  servoBase.setPeriodHertz(50);
  servoBrazo.setPeriodHertz(50);
  servoPinza.setPeriodHertz(50);

  servoBase.attach(PIN_SERVO_BASE, 500, 2400);
  servoBrazo.attach(PIN_SERVO_BRAZO, 500, 2400);
  servoPinza.attach(PIN_SERVO_PINZA, 500, 2400);

  // Llevar el brazo a una posición segura al encender
  servoBase.write(anguloBase);
  servoBrazo.write(anguloBrazo);
  servoPinza.write(anguloPinza);

  delay(800);

  Serial.println("====================================");
  Serial.println("Control de brazo robotico iniciado");
  Serial.println("Eje X: gira la base");
  Serial.println("Eje Y: mueve el brazo");
  Serial.println("Boton: abre/cierra la pinza");
  Serial.println("====================================");
}

void loop() {
  if (millis() - tiempoAnterior >= PERIODO_CONTROL_MS) {
    tiempoAnterior = millis();

    int lecturaX = leerJoystickPromedio(PIN_JOYSTICK_X);
    int lecturaY = leerJoystickPromedio(PIN_JOYSTICK_Y);

    moverBaseConJoystick(lecturaX);
    moverBrazoConJoystick(lecturaY);
    controlarPinza();

    imprimirEstado(lecturaX, lecturaY);
  }
}