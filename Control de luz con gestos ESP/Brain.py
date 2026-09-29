import os
import time
import urllib.request

import cv2
import mediapipe as mp
import serial
import serial.tools.list_ports
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ================== CONFIGURACIÓN ==================
PUERTO_SERIAL = 'COM6'          # Puerto del ESP32
BAUDIOS = 115200                # Debe coincidir con Serial.begin() del ESP32
CAMARA = 0                      # 0 = cámara integrada, 1 = cámara USB externa

FRAMES_ESTABLES = 5             # Frames seguidos con el mismo gesto para aceptarlo
CONFIANZA_MIN = 0.6             # Confianza mínima del gesto (0 a 1)
ESPERA_SECUENCIA = 2.0          # Segundos entre repeticiones de las secuencias (4 y 5)

# El modelo se busca en la MISMA carpeta de este archivo (evita el FileNotFoundError)
CARPETA = os.path.dirname(os.path.abspath(__file__))
MODELO = os.path.join(CARPETA, 'gesture_recognizer.task')
URL_MODELO = ('https://storage.googleapis.com/mediapipe-models/gesture_recognizer/'
              'gesture_recognizer/float16/latest/gesture_recognizer.task')

# Gesto de MediaPipe -> (comando para el ESP32, texto en pantalla, color BGR)
GESTOS = {
    'Closed_Fist': ('1', 'Puno (Amarillo 30%)',          (0, 255, 255)),
    'Victory':     ('2', 'Paz (Azul 70%)',               (255, 150, 0)),
    'Open_Palm':   ('3', 'Mano Abierta (Rojo 100%)',     (0, 0, 255)),
    'Thumb_Down':  ('4', 'Pulgar Abajo (Secuencia 1)',   (200, 0, 200)),
    'Thumb_Up':    ('5', 'Pulgar Arriba (Secuencia 2)',  (0, 200, 0)),
}


def descargar_modelo():
    if not os.path.exists(MODELO):
        print('Descargando modelo gesture_recognizer.task ...')
        urllib.request.urlretrieve(URL_MODELO, MODELO)
        print(f'Modelo guardado en: {MODELO}')


def iniciar_serial():
    try:
        esp = serial.Serial(PUERTO_SERIAL, BAUDIOS, timeout=1)
        time.sleep(2)                       # El ESP32 se reinicia al abrir el puerto
        esp.reset_input_buffer()
        print(f'Conectado exitosamente al ESP32 en {PUERTO_SERIAL}')
        return esp
    except Exception as e:
        print(f'¡Atención! No se pudo conectar a {PUERTO_SERIAL}: {e}')
        print('Puertos disponibles:')
        for p in serial.tools.list_ports.comports():
            print(f'   {p.device} - {p.description}')
        print('Revisa el cable y cierra el Monitor Serie de Arduino. Se continúa sin ESP32.\n')
        return None


def enviar(esp32, comando):
    if esp32 is None:
        return
    try:
        esp32.write(comando.encode())
        print(f'-> Enviado al ESP32: {comando}')
    except serial.SerialException as e:
        print(f'Error enviando por serial: {e}')


def main():
    descargar_modelo()
    esp32 = iniciar_serial()

    # --- MediaPipe Tasks en modo VIDEO ---
    options = vision.GestureRecognizerOptions(
        base_options=python.BaseOptions(model_asset_path=MODELO),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
    )
    recognizer = vision.GestureRecognizer.create_from_options(options)

    # --- Cámara (CAP_DSHOW abre más rápido en Windows) ---
    cap = cv2.VideoCapture(CAMARA, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(CAMARA)
    if not cap.isOpened():
        print('No se pudo abrir la cámara. Prueba con CAMARA = 1.')
        return

    comando_actual = ''
    candidato, contador = '', 0
    t_ultimo_envio = 0.0
    t_inicio = time.monotonic()
    ultimo_ts = -1
    t_fps, fps = time.monotonic(), 0.0

    print("Cámara iniciada. Presiona 'ESC' en la ventana de video para salir.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print('No se pudo leer la cámara.')
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            # El modo VIDEO exige timestamps estrictamente crecientes
            ts = int((time.monotonic() - t_inicio) * 1000)
            if ts <= ultimo_ts:
                ts = ultimo_ts + 1
            ultimo_ts = ts

            resultado = recognizer.recognize_for_video(mp_image, ts)

            # --- Gesto detectado en este frame ---
            gesto, score = '', 0.0
            if resultado.gestures:
                g = resultado.gestures[0][0]
                if g.category_name in GESTOS and g.score >= CONFIANZA_MIN:
                    gesto, score = g.category_name, g.score

            # --- Filtro: el gesto debe mantenerse varios frames ---
            if gesto == candidato:
                contador += 1
            else:
                candidato, contador = gesto, 1

            texto, color = 'Buscando gesto...', (200, 200, 200)
            if candidato and contador >= FRAMES_ESTABLES:
                comando, texto, color = GESTOS[candidato]
                ahora = time.monotonic()
                es_secuencia = comando in ('4', '5')
                if comando != comando_actual or (es_secuencia and ahora - t_ultimo_envio > ESPERA_SECUENCIA):
                    enviar(esp32, comando)
                    comando_actual = comando
                    t_ultimo_envio = ahora

            # --- Interfaz ---
            ahora = time.monotonic()
            fps = 0.9 * fps + 0.1 / max(ahora - t_fps, 1e-6)
            t_fps = ahora
            estado = f'ESP32: {PUERTO_SERIAL} OK' if esp32 else 'ESP32: desconectado'

            cv2.rectangle(frame, (0, 0), (frame.shape[1], 95), (0, 0, 0), -1)
            cv2.putText(frame, texto, (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.putText(frame, f'{estado} | Ultimo cmd: {comando_actual or "-"} | '
                               f'conf: {score:.2f} | {fps:.0f} FPS',
                        (15, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (0, 255, 0) if esp32 else (0, 0, 255), 1)
            cv2.imshow('Control Gestual UMNG', frame)

            if cv2.waitKey(1) & 0xFF == 27:     # ESC
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        recognizer.close()
        if esp32:
            esp32.close()
        print('Programa finalizado.')


if __name__ == '__main__':
    main()