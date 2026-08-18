import time
import sys

import cv2
from ultralytics import YOLO
import paho.mqtt.client as mqtt
#

class BrokerConfig:
    HOST = "broker.hivemq.com"
    PORT = 1883
    KEEPALIVE = 60
    CHANNEL = "lab_vision_carros_motos/control"
    CLIENT_TAG = "pc_vision_node"


class VehicleWatcher:
    """
    Encapsula la captura de video, la inferencia YOLO
    y la publicacion de estado por MQTT.
    """

    CAR_LABELS = {"car"}
    MOTO_LABELS = {"motorcycle", "motorbike"}

    def __init__(self, weights_path="yolov8n.pt", cam_index=0, min_conf=0.5):
        self.min_conf = min_conf
        self.detector = YOLO(weights_path)
        self.video_source = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
        self.last_state = None
        self.mqtt_client = self._build_mqtt_client()

    def _build_mqtt_client(self):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, BrokerConfig.CLIENT_TAG)
        try:
            client.connect(BrokerConfig.HOST, BrokerConfig.PORT, BrokerConfig.KEEPALIVE)
            client.loop_start()
            print(f"[MQTT] conectado a {BrokerConfig.HOST}")
        except Exception as exc:
            print(f"[MQTT] no se pudo conectar: {exc}")
            sys.exit(1)
        return client

    def _classify_frame(self, results):
        car_found = False
        moto_found = False

        for result in results:
            for box in result.boxes:
                label = self.detector.names[int(box.cls[0])]

                if label in self.CAR_LABELS:
                    car_found = True
                elif label in self.MOTO_LABELS:
                    moto_found = True

        if car_found:
            return "CAR"
        if moto_found:
            return "MOTO"
        return "OFF"

    def _publish_if_changed(self, state):
        if state == self.last_state:
            return

        self.mqtt_client.publish(BrokerConfig.CHANNEL, state)
        print(f"[MQTT] estado publicado -> {state}")
        self.last_state = state

    def run(self):
        print("Watcher activo. Pulsa 'q' en la ventana de video para salir.")

        while self.video_source.isOpened():
            success, frame = self.video_source.read()
            if not success:
                break

            inference = self.detector(frame, conf=self.min_conf, verbose=False)
            state = self._classify_frame(inference)
            self._publish_if_changed(state)

            preview = inference[0].plot()
            cv2.imshow("Monitor de trafico - YOLO", preview)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.shutdown()

    def shutdown(self):
        self.mqtt_client.publish(BrokerConfig.CHANNEL, "OFF")
        time.sleep(0.2)

        self.video_source.release()
        cv2.destroyAllWindows()

        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        print("[MQTT] desconectado, recursos liberados")


def main():
    watcher = VehicleWatcher(weights_path="yolov8n.pt", cam_index=0, min_conf=0.5)
    watcher.run()


if __name__ == "__main__":
    main()
    #https://wokwi.com/projects/386238412259789825