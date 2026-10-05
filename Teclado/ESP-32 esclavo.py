#include <ESP32SPISlave.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

ESP32SPISlave slave;
Adafruit_SSD1306 oled(128, 64, &Wire, -1);
static constexpr size_t BUF = 4;
uint8_t rx[BUF], tx[BUF] = {0};

void mostrar(char c) {
  oled.clearDisplay();
  oled.setTextSize(6); oled.setTextColor(WHITE);
  oled.setCursor(48, 8); oled.print(c);
  oled.display();
}

void setup() {
  Serial.begin(115200);
  Wire.begin(8, 9);    // SDA, SCL (ajusta; en ESP32 clasico 21,22)
  oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  mostrar('-');
  slave.setDataMode(SPI_MODE0);
  slave.begin(HSPI, 18, 19, 23, 5);   // SCK, MISO, MOSI, CS (ajusta)
}

void loop() {
  slave.queue(rx, tx, BUF);
  slave.wait();                       // espera una transaccion
  while (slave.available()) {
    char c = rx[0];
    if (c >= '0' && c <= '9') mostrar(c);
    slave.pop();
  }
}