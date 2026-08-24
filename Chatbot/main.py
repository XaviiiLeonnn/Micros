import json
import time
import logging
from dataclasses import dataclass

import numpy as np
import paho.mqtt.client as mqtt
import requests
import sounddevice as sd
import speech_recognition as sr


@dataclass(frozen=True)
class ConfiguracionModelo:
    url_endpoint: str = "http://localhost:11434/api/chat"
    nombre_modelo: str = "llama3.1:8b"
    temperatura: float = 0.1
    tiempo_maximo_espera: int = 12


CONFIG_MODELO = ConfiguracionModelo()

INSTRUCCION_SISTEMA = """
Eres el controlador domótico de un LED conectado a un ESP32.
Tu único trabajo es interpretar la intención del usuario y responder ESTRICTAMENTE con un objeto JSON válido con este formato:
{
  "comando": "LED_ON" | "LED_OFF" | "NINGUNO",
  "respuesta": "Frase breve confirmando la acción"
}

Reglas:
- Si el usuario pide encender, iluminar o que está oscuro -> comando: "LED_ON"
- Si el usuario pide apagar, oscurecer o dormir -> comando: "LED_OFF"
- Si no tiene relación con luces -> comando: "NINGUNO"
"""

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
registro = logging.getLogger("puente_llm")


SERVIDOR_MQTT = "broker.hivemq.com"
PUERTO_MQTT = 1883
TEMA_LED = "lab_micro_deepseek/led_unico"

cliente_mqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "pc_voice_llama31")

try:
    cliente_mqtt.connect(SERVIDOR_MQTT, PUERTO_MQTT, 60)
    cliente_mqtt.loop_start()
    print(">> MQTT ok, conectado al broker")
except Exception as error:
    print(f">> uy, no pude conectar al MQTT: {error}")


def consultar_modelo(texto_usuario: str) -> dict:
    cuerpo_peticion = {
        "model": CONFIG_MODELO.nombre_modelo,
        "messages": [
            {"role": "system", "content": INSTRUCCION_SISTEMA},
            {"role": "user", "content": texto_usuario},
        ],
        "format": "json",
        "stream": False,
        "options": {"temperature": CONFIG_MODELO.temperatura},
    }

    try:
        respuesta = requests.post(
            CONFIG_MODELO.url_endpoint,
            json=cuerpo_peticion,
            timeout=CONFIG_MODELO.tiempo_maximo_espera,
        )
        respuesta.raise_for_status()
        contenido_bruto = respuesta.json()["message"]["content"]
        resultado = json.loads(contenido_bruto)

        if "comando" not in resultado or "respuesta" not in resultado:
            raise ValueError("La respuesta del modelo llegó incompleta")

        return resultado

    except requests.exceptions.Timeout:
        registro.error("Se agotó el tiempo de espera consultando el modelo local.")
    except requests.exceptions.RequestException as excepcion:
        registro.error(f"Fallo de conexión con Ollama: {excepcion}")
    except (KeyError, json.JSONDecodeError, ValueError) as excepcion:
        registro.error(f"Respuesta inválida del modelo: {excepcion}")

    return {"comando": "NINGUNO", "respuesta": "Error procesando orden."}


def grabar_voz(duracion=4, frecuencia_muestreo=16000):
    print("\n>> ESCUCHANDO... habla ahora:")

    try:
        audio = sd.rec(
            int(duracion * frecuencia_muestreo),
            samplerate=frecuencia_muestreo,
            channels=1,
            dtype="int16",
        )
        sd.wait()

        reconocedor = sr.Recognizer()
        fuente_audio = sr.AudioData(audio.tobytes(), frecuencia_muestreo, 2)
        texto = reconocedor.recognize_google(fuente_audio, language="es-ES")

        print(f"-> dijiste: '{texto}'")
        return texto

    except sr.UnknownValueError:
        print("-> no se entendió nada, intenta de nuevo")
        return None
    except Exception as error:
        print(f"-> error grabando: {error}")
        return None


def publicar_comando_led(comando):
    cliente_mqtt.publish(TEMA_LED, comando)
    print(f"-> mandado al ESP32 por MQTT: {comando}")


def main():
    print(f"=== ASISTENTE DE VOZ - {CONFIG_MODELO.nombre_modelo.upper()} LOCAL ===")
    print("Dale [ENTER] para hablar. Decí 'salir' para terminar.\n")

    palabras_de_salida = ("salir", "terminar")

    while True:
        input("Presiona [ENTER] para hablar...")
        frase = grabar_voz()

        if not frase:
            continue

        if any(palabra in frase.lower() for palabra in palabras_de_salida):
            print("listo, hasta luego!")
            break

        print("...pensando con el modelo...")
        resultado = consultar_modelo(frase)

        comando = resultado.get("comando", "NINGUNO")
        respuesta = resultado.get("respuesta", "")

        print(f"Modelo: {respuesta} | [comando detectado: {comando}]")

        if comando in ("LED_ON", "LED_OFF"):
            publicar_comando_led(comando)


if __name__ == "__main__":
    main()
#https://wokwi.com/projects/473196574995253249
