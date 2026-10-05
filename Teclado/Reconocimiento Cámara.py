import cv2, numpy as np, serial, time
from tensorflow.keras.models import load_model

model = load_model("modelo_digitos.h5")
ser = serial.Serial("COM5", 115200, timeout=0.1)   # puerto del ESP-A
cap = cv2.VideoCapture(0)
x1, y1, x2, y2 = 220, 140, 420, 340                # recuadro verde
last, last_t = None, 0

while True:
    ok, frame = cap.read()
    if not ok: break
    roi = frame[y1:y2, x1:x2]
    g = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    g = cv2.GaussianBlur(g, (5,5), 0)
    th = cv2.adaptiveThreshold(g,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY_INV,11,6)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((3,3),np.uint8))
    cnts,_ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = [c for c in cnts if cv2.contourArea(c) > 300]
    if cnts:
        x,y,w,h = cv2.boundingRect(np.vstack(cnts))
        d = th[y:y+h, x:x+w]
        s = max(w,h); sq = np.zeros((s,s),np.uint8)
        sq[(s-h)//2:(s-h)//2+h, (s-w)//2:(s-w)//2+w] = d
        sq = cv2.copyMakeBorder(sq, s//4,s//4,s//4,s//4, cv2.BORDER_CONSTANT)
        img = cv2.resize(sq,(28,28)).astype("float32")/255.0
        pred = model.predict(img[None,...,None], verbose=0)[0]
        n, conf = int(np.argmax(pred)), float(np.max(pred))
        cv2.putText(frame, f"Numero: {n} ({conf*100:.1f}%)", (x1,y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        cv2.imshow("Digito", cv2.resize(img,(140,140)))
        if conf > 0.9 and (n != last or time.time()-last_t > 2):
            ser.write(f"{n}\n".encode()); last, last_t = n, time.time()
    cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
    cv2.imshow("Reconocimiento", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break
cap.release(); cv2.destroyAllWindows()