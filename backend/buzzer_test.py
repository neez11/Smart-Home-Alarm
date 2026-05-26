import RPi.GPIO as GPIO
import time

BUZZER_PIN = 13

print("Programmet har startat")
print(f"Alarm-test på GPIO {BUZZER_PIN}")

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

pwm = GPIO.PWM(BUZZER_PIN, 1500)
pwm.start(90)

try:
    print("Buzzern kör högre siren nu...")
    while True:
        for freq in range(1500, 3500, 40):
            pwm.ChangeFrequency(freq)
            time.sleep(0.005)

        for freq in range(3500, 1500, -40):
            pwm.ChangeFrequency(freq)
            time.sleep(0.005)

except KeyboardInterrupt:
    print("Stoppad med Ctrl+C")
finally:
    pwm.stop()
    GPIO.cleanup()
    print("GPIO cleanup klar")
