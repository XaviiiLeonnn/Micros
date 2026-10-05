const int AX[4] = {34, 35, 32, 33};
const int BT[4] = {25, 26, 27, 14};

float norm(int pin) {
  float x = (analogRead(pin) - 2048) / 2048.0;
  if (fabs(x) < 0.08) x = 0;               // zona muerta
  return constrain(x, -1.0, 1.0);
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  for (int i = 0; i < 4; i++) pinMode(BT[i], INPUT_PULLUP);
}

void loop() {
  Serial.printf("J,%.2f,%.2f,%.2f,%.2f,%d,%d,%d,%d\n",
    norm(AX[0]), norm(AX[1]), norm(AX[2]), norm(AX[3]),
    !digitalRead(BT[0]), !digitalRead(BT[1]),
    !digitalRead(BT[2]), !digitalRead(BT[3]));
  delay(20);                                // 50 Hz
}