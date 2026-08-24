# ESP32-WROOM-32 con MicroPython

Proyecto de sistemas embebidos sobre el módulo **ESP32-WROOM-32** (Espressif Systems), programado con **MicroPython**. Incluye guía de instalación del firmware, mapa de pines y ejemplos de uso de GPIO, ADC, PWM y DAC.

> Universidad Militar Nueva Granada — Ingeniería Mecatrónica / Multimedia — Asignatura de Sistemas Embebidos (Micros).

## Tabla de contenidos

- [Descripción general](#descripción-general)
- [Requisitos](#requisitos)
- [Instalación del firmware](#instalación-del-firmware)
- [Mapa de pines](#mapa-de-pines)
- [Periféricos y ejemplos](#periféricos-y-ejemplos)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Referencias](#referencias)

## Descripción general

El ESP32-WROOM-32 integra un procesador **Xtensa LX6 dual-core de 32 bits** (hasta 240 MHz), 448 KB de ROM, 520 KB de SRAM y 4 MB de memoria Flash SPI externa, junto con conectividad **Wi-Fi 802.11 b/g/n** y **Bluetooth 4.2 (BR/EDR + BLE)**. Su alimentación recomendada es de 3.0 a 3.6 V y opera en un rango de temperatura de aproximadamente −40 °C a 85 °C.

A diferencia de una placa de desarrollo completa, el WROOM-32 es un *módulo* que se integra en tarjetas propias o en placas como las distintas versiones de ESP32 DevKit, que añaden regulador de voltaje, conversor USB–UART y botones de reset/boot.

| Característica | Descripción |
|---|---|
| Procesador | Xtensa LX6, dual-core, 32 bits, hasta 240 MHz |
| Memoria | 448 KB ROM, 520 KB SRAM, 4 MB SPI Flash |
| Wi-Fi | IEEE 802.11 b/g/n, hasta 150 Mbps |
| Bluetooth | 4.2 BR/EDR y BLE |
| GPIO | Hasta 32, con funciones alternativas y pines de *strapping* |
| Periféricos | UART, SPI, I2C, I2S, PWM (LEDC), ADC, DAC, touch, PCNT, TWAI |
| Antena | PCB integrada |

Este proyecto usa **MicroPython** en lugar de C/C++ (ESP-IDF/Arduino) porque su sintaxis basada en Python facilita el prototipado rápido, la lectura de sensores y las pruebas iterativas, a costa de un menor rendimiento frente a una implementación nativa en C.

## Requisitos

- Placa con módulo ESP32-WROOM-32 (por ejemplo, ESP32 DevKit v1).
- Cable USB (datos, no solo carga) y driver USB–UART instalado (CP2102 o CH340 según la placa).
- Python 3 instalado en el equipo host.
- Herramientas recomendadas:
  - [`esptool`](https://github.com/espressif/esptool) para flashear el firmware.
  - [Thonny IDE](https://thonny.org/) o `mpremote`/`rshell`/`ampy` para transferir archivos y abrir el REPL.

```bash
pip install esptool
pip install mpremote
```

## Instalación del firmware

1. Descarga el firmware `.bin` de MicroPython para ESP32 desde la [página oficial de descargas](https://micropython.org/download/ESP32_GENERIC/).
2. Conecta la placa y pon el módulo en modo *bootloader* (mantén presionado **BOOT/IO0** al reiniciar si no entra automáticamente).
3. Borra la flash completa antes de instalar el nuevo firmware:

```bash
esptool.py --port /dev/ttyUSB0 erase_flash
```

4. Escribe el firmware (ajusta el nombre de archivo y el puerto según tu sistema; en Windows suele ser `COMx`):

```bash
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-<version>.bin
```

5. Verifica la instalación abriendo el REPL serial (115200 baudios) y comprobando que responde con el prompt `>>>` de MicroPython.

## Mapa de pines

No todos los GPIO del ESP32-WROOM-32 se usan de la misma forma; varios tienen restricciones por función de arranque, memoria Flash interna o comunicación serie.

| GPIO | Función destacada | Observación |
|---|---|---|
| GPIO0 | ADC2, strapping | Interviene en el modo de arranque |
| GPIO1 | TXD | Uso típico para transmisión UART |
| GPIO2 | ADC2, strapping | Función analógica y de arranque |
| GPIO5 | GPIO, strapping | Función especial durante el arranque |
| GPIO6–11 | SPI0/1 | Asociados a la memoria Flash del módulo, evitar como GPIO de propósito general |
| GPIO12–15 | ADC2 / JTAG | Funciones especiales y de depuración |
| GPIO21–23 | GPIO / periféricos | Útiles para interfaces I2C o SPI |
| GPIO25–26 | DAC / ADC2 | Únicos pines con salida DAC integrada |
| GPIO32–33 | ADC1 | Entradas analógicas recomendadas si se usa Wi-Fi |
| GPIO34–39 | ADC1 / solo entrada | No admiten salida digital |

**Nota:** ADC2 comparte recursos con el radio Wi-Fi, por lo que cuando el Wi-Fi está activo se recomienda usar los canales de **ADC1** (GPIO32–39) para lecturas analógicas confiables.

## Periféricos y ejemplos

### GPIO digital

```python
from machine import Pin
from time import sleep

led = Pin(2, Pin.OUT)

while True:
    led.value(not led.value())
    sleep(0.5)
```

### ADC (entrada analógica)

El ESP32 usa un ADC SAR de 12 bits. Se recomienda configurar la atenuación para leer el rango completo de 0 a 3.3 V:

```python
from machine import ADC, Pin
from time import sleep

sensor = ADC(Pin(32))          # ADC1, seguro de usar junto con Wi-Fi
sensor.atten(ADC.ATTN_11DB)    # rango ~0-3.3 V
sensor.width(ADC.WIDTH_12BIT)  # resolución 0-4095

while True:
    valor = sensor.read()
    print("Lectura ADC:", valor)
    sleep(1)
```

### PWM (LEDC)

El controlador LEDC ofrece 16 canales (8 de alta y 8 de baja velocidad) para generar señales PWM, útiles para atenuar LEDs o controlar velocidad de motores mediante la etapa de potencia correspondiente:

```python
from machine import Pin, PWM

led_pwm = PWM(Pin(4), freq=5000, duty=0)

for duty in range(0, 1024, 32):
    led_pwm.duty(duty)
```

### DAC (salida analógica)

El ESP32 dispone de dos DAC de 8 bits en **GPIO25** y **GPIO26**, útiles para generar tensiones analógicas simples (256 niveles):

```python
from machine import DAC, Pin

salida = DAC(Pin(25))
salida.write(128)  # valor entre 0 y 255 (~1.65 V en el punto medio)
```

### Combinación potenciómetro + LED (ADC + PWM)

```python
from machine import Pin, ADC, PWM
from time import sleep

pot = ADC(Pin(34))
pot.atten(ADC.ATTN_11DB)

led = PWM(Pin(27), freq=5000)

while True:
    valor = pot.read()             # rango 0-4095
    duty = int(valor / 4095 * 1023)
    led.duty(duty)
    sleep(0.05)
```

## Estructura del repositorio

```
.
├── README.md
├── boot.py          # Configuración inicial (Wi-Fi, ajustes de arranque)
├── main.py           # Punto de entrada del programa principal
└── lib/               # Módulos y drivers adicionales
```

`boot.py` se ejecuta automáticamente al energizar la placa y suele reservarse para configuración de red o del sistema; `main.py` contiene la lógica principal de la aplicación y se ejecuta justo después.

## Referencias

- Espressif Systems. *ESP32-WROOM-32 Datasheet*. [documentation.espressif.com](https://documentation.espressif.com/esp32-wroom-32_datasheet_en.html)
- Espressif Systems. *ADC – ESP32 API Reference*. [docs.espressif.com](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/adc/index.html)
- Espressif Systems. *LED Control (LEDC) – ESP32*. [docs.espressif.com](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/ledc.html)
- MicroPython. *Quick reference for the ESP32*. [docs.micropython.org](https://docs.micropython.org/en/latest/esp32/quickref.html)
- MicroPython. *Getting started with MicroPython on the ESP32*. [docs.micropython.org](https://docs.micropython.org/en/latest/esp32/tutorial/intro.html)
