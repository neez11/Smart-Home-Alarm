import threading
import time
import RPi.GPIO as GPIO


class BuzzerService:
    def __init__(self, pin=13, base_frequency=1500, duty_cycle=90):
        self.pin = pin
        self.base_frequency = base_frequency
        self.duty_cycle = duty_cycle

        self._running = False
        self._thread = None
        self._lock = threading.Lock()

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)

        self.pwm = GPIO.PWM(self.pin, self.base_frequency)

    def _siren_loop(self):
        try:
            self.pwm.start(self.duty_cycle)

            while self._running:
                for freq in range(1500, 3500, 40):
                    if not self._running:
                        break
                    self.pwm.ChangeFrequency(freq)
                    time.sleep(0.005)

                for freq in range(3500, 1500, -40):
                    if not self._running:
                        break
                    self.pwm.ChangeFrequency(freq)
                    time.sleep(0.005)

        finally:
            try:
                self.pwm.ChangeDutyCycle(0)
            except Exception:
                pass

            try:
                self.pwm.stop()
            except Exception:
                pass

    def on(self):
        with self._lock:
            if self._running:
                return

            self._running = True
            self._thread = threading.Thread(target=self._siren_loop, daemon=True)
            self._thread.start()

    def off(self):
        with self._lock:
            self._running = False
            thread = self._thread
            self._thread = None

        if thread is not None:
            thread.join(timeout=1)

    def beep(self, frequency=2000, duration=0.15):
        self.off()
        self.pwm.start(self.duty_cycle)
        self.pwm.ChangeFrequency(frequency)
        time.sleep(duration)
        self.pwm.stop()

    def alarm_pattern(self):
        self.off()
        self.pwm.start(self.duty_cycle)

        try:
            for _ in range(2):
                for freq in range(1500, 3500, 40):
                    self.pwm.ChangeFrequency(freq)
                    time.sleep(0.005)

                for freq in range(3500, 1500, -40):
                    self.pwm.ChangeFrequency(freq)
                    time.sleep(0.005)
        finally:
            self.pwm.stop()

    def continuous_alarm(self):
        self.on()

    def cleanup(self):
        self.off()
        GPIO.cleanup(self.pin)
