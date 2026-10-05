import serial, threading

class Console:
    def __init__(self, port="COM3", baud=115200):
        self.s = serial.serial_for_url(port, baud, timeout=0.1)
        self.ax = [0.0]*4
        self.bt = [0]*4
        self._ev = [False]*4
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while True:
            l = self.s.readline().decode(errors="ignore").strip()
            if not l.startswith("J,"): continue
            try:
                v = l.split(",")[1:]
                self.ax = [float(x) for x in v[:4]]
                b = [int(x) for x in v[4:8]]
            except ValueError:
                continue
            for i in range(4):
                if b[i] and not self.bt[i]: self._ev[i] = True
            self.bt = b

    def pressed(self, i):          # flanco de subida de un boton
        r = self._ev[i]; self._ev[i] = False
        return r