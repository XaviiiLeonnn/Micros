#include <SPI.h>
#define CS 5
SPIClass *vspi = &SPI;           // SCK18 MISO19 MOSI23 CS5

void setup() {
  Serial.begin(115200);
  pinMode(CS, OUTPUT); digitalWrite(CS, HIGH);
  vspi->begin(18, 19, 23, CS);
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if (c >= '0' && c <= '9') {
      vspi->beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0));
      digitalWrite(CS, LOW);
      vspi->transfer(c);
      digitalWrite(CS, HIGH);
      vspi->endTransaction();
    }
  }
}