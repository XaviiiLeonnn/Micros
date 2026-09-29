/*
 * Control de iluminación por gestos - ESP32
 *
 * Recibe por UART/USB Serial a 115200:
 * '1' -> LED amarillo al 30 %
 * '2' -> LED azul al 70 %
 * '3' -> LED rojo al 100 %
 * '4' -> Secuencia Modo 1
 * '5' -> Secuencia Modo 2
 * 'X' -> Apagar todo
 *
 * LEDs:
 * Amarillo -> GPIO 25
 * Azul     -> GPIO 26
 * Rojo     -> GPIO 27
 */

const int PIN_AMARILLO = 25;
const int PIN_AZUL     = 26;
const int PIN_ROJO     = 27;

const int PINES[3] = {
  PIN_AMARILLO,
  PIN_AZUL,
  PIN_ROJO
};

const int FREQ_PWM = 5000;
const int RES_PWM  = 8;

enum Modo {
  APAGADO,
  FIJO,
  SECUENCIA_1,
  SECUENCIA_2
};

Modo modo = APAGADO;

unsigned long tPaso = 0;
int paso = 0;

// --------------------------------------------------
// Inicialización PWM compatible con Core 2.x y 3.x
// --------------------------------------------------
void iniciarPWM() {
#if ESP_ARDUINO_VERSION_MAJOR >= 3

  ledcAttach(PIN_AMARILLO, FREQ_PWM, RES_PWM);
  ledcAttach(PIN_AZUL,     FREQ_PWM, RES_PWM);
  ledcAttach(PIN_ROJO,     FREQ_PWM, RES_PWM);

#else

  ledcSetup(0, FREQ_PWM, RES_PWM);
  ledcSetup(1, FREQ_PWM, RES_PWM);
  ledcSetup(2, FREQ_PWM, RES_PWM);

  ledcAttachPin(PIN_AMARILLO, 0);
  ledcAttachPin(PIN_AZUL, 1);
  ledcAttachPin(PIN_ROJO, 2);

#endif
}

// --------------------------------------------------
// Escribir brillo en porcentaje: 0 a 100
// --------------------------------------------------
void brilloLED(int indice, int porcentaje) {
  porcentaje = constrain(porcentaje, 0, 100);

  int duty = map(porcentaje, 0, 100, 0, 255);

#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(PINES[indice], duty);
#else
  ledcWrite(indice, duty);
#endif
}

// --------------------------------------------------
// Apagar los 3 LEDs
// --------------------------------------------------
void apagarTodo() {
  for (int i = 0; i < 3; i++) {
    brilloLED(i, 0);
  }
}

// --------------------------------------------------
// Procesar carácter recibido
// --------------------------------------------------
void procesarComando(char c) {
  // No reiniciar la secuencia si se repite el gesto.
  if (c == '4' && modo == SECUENCIA_1) return;
  if (c == '5' && modo == SECUENCIA_2) return;

  apagarTodo();

  paso = 0;
  tPaso = millis();

  switch (c) {
    case '1':
      modo = FIJO;
      brilloLED(0, 30);
      Serial.println("Amarillo: 30%");
      break;

    case '2':
      modo = FIJO;
      brilloLED(1, 70);
      Serial.println("Azul: 70%");
      break;

    case '3':
      modo = FIJO;
      brilloLED(2, 100);
      Serial.println("Rojo: 100%");
      break;

    case '4':
      modo = SECUENCIA_1;
      Serial.println("Modo 1 activado");
      break;

    case '5':
      modo = SECUENCIA_2;
      Serial.println("Modo 2 activado");
      break;

    case 'X':
    case 'x':
      modo = APAGADO;
      apagarTodo();
      Serial.println("Todo apagado");
      break;
  }
}

// --------------------------------------------------
// Secuencia 1:
// Amarillo -> Azul -> Rojo -> Azul
// --------------------------------------------------
void secuencia1() {
  const int orden[4] = {0, 1, 2, 1};

  if (millis() - tPaso < 200) {
    return;
  }

  tPaso = millis();

  apagarTodo();

  brilloLED(orden[paso % 4], 100);

  paso++;
}

// --------------------------------------------------
// Secuencia 2:
// Parpadeo inicial + respiración de los 3 LEDs
// --------------------------------------------------
void secuencia2() {
  if (millis() - tPaso < 15) {
    return;
  }

  tPaso = millis();

  int ciclo = paso % 200;
  int brillo;

  if (ciclo < 80) {
    // Cambia cada 10 pasos: 10 x 15 ms = 150 ms
    brillo = ((ciclo / 10) % 2 == 0) ? 0 : 100;
  } else {
    // 120 pasos x 15 ms = 1.8 s de efecto respiración
    int k = ciclo - 80;

    if (k < 60) {
      brillo = k * 100 / 60;
    } else {
      brillo = (119 - k) * 100 / 60;
    }
  }

  for (int i = 0; i < 3; i++) {
    brilloLED(i, brillo);
  }

  paso++;
}

// --------------------------------------------------
// Configuración
// --------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(500);

  iniciarPWM();
  apagarTodo();

  Serial.println("ESP32 listo");
  Serial.println("Envie: 1, 2, 3, 4, 5 o X");
}

// --------------------------------------------------
// Ciclo principal
// --------------------------------------------------
void loop() {
  // Recepción simple y confiable por UART/USB.
  while (Serial.available() > 0) {
    char c = Serial.read();

    // Ignora terminadores enviados por monitor serie/Python.
    if (c == '\n' || c == '\r' || c == ' ') {
      continue;
    }

    Serial.print("Caracter recibido: ");
    Serial.println(c);

    if ((c >= '1' && c <= '5') || c == 'X' || c == 'x') {
      procesarComando(c);
    } else {
      Serial.println("Comando invalido");
    }
  }

  if (modo == SECUENCIA_1) {
    secuencia1();
  }

  if (modo == SECUENCIA_2) {
    secuencia2();
  }
}