#include <Wire.h>
#include <Keypad.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);

const byte ROWS = 4, COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
byte rowPins[ROWS] = {19, 18, 5, 17};   // ajusta a tu cableado
byte colPins[COLS] = {16, 4, 2, 15};
Keypad kp = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  lcd.init(); lcd.backlight();
  lcd.setCursor(0,0); lcd.print("Presione tecla");
}

void loop() {
  char k = kp.getKey();
  if (k) {
    lcd.clear();
    lcd.setCursor(0,0); lcd.print("Tecla: ");
    lcd.print(k);
    Serial.println(k);          // PC recibe el caracter + '\n'
  }
}