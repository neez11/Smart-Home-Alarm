# smart_alarm/pir_sensor.py

import time
import threading
from gpiozero import MotionSensor, LED
from smart_alarm.buzzer import BuzzerService

from config import (
    GPIO_PIR,
    GPIO_LED,
    GPIO_BUZZER,
    POLL_INTERVAL,
    ENABLE_BUZZER,
)
from smart_alarm.system_state import SystemState


class PirAlarmController:
    def __init__(self, state: SystemState, logger, buzzer: BuzzerService | None = None):
        self.state = state
        self.logger = logger

        self.running = False
        self.thread = None

        self.pir = MotionSensor(GPIO_PIR)
        self.led = LED(GPIO_LED)

        self.buzzer = buzzer if ENABLE_BUZZER else None

        self._last_motion_state = False

        self.led.off()
        self.state.set_led_on(False)

        if self.buzzer is not None:
            self.buzzer.off()
        self.state.set_buzzer_on(False)

    def start(self) -> None:
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        self.logger.info("PirAlarmController started")
        self.state.add_event("PIR controller started")

    def stop(self) -> None:
        self.running = False

        if self.thread is not None:
            self.thread.join(timeout=2)

        self._safe_outputs_off()
        self.logger.info("PirAlarmController stopped")
        self.state.add_event("PIR controller stopped")

    def arm(self) -> None:
        self.state.set_armed(True)
        self.state.set_motion_detected(False)
        self.state.set_alarm_triggered(False)
        self._safe_outputs_off()
        self.logger.info("System armed")
        self.state.add_event("System armed")

    def disarm(self) -> None:
        self.state.set_armed(False)
        self.state.set_motion_detected(False)
        self.state.set_alarm_triggered(False)
        self._safe_outputs_off()
        self.logger.info("System disarmed")
        self.state.add_event("System disarmed")

    def reset_alarm(self) -> None:
        self.state.set_motion_detected(False)
        self.state.set_alarm_triggered(False)
        self._safe_outputs_off()
        self.logger.info("Alarm reset")
        self.state.add_event("Alarm reset")

    def test_outputs(self, duration: float = 1.0) -> None:
        self.logger.info("Testing outputs")
        self.state.add_event("Output test started")

        self.led.on()
        self.state.set_led_on(True)

        if self.buzzer is not None:
            self.buzzer.on()
            self.state.set_buzzer_on(True)

        time.sleep(duration)

        self._safe_outputs_off()
        self.state.add_event("Output test finished")

    def _safe_outputs_off(self) -> None:
        self.led.off()
        self.state.set_led_on(False)

        if self.buzzer is not None:
            self.buzzer.off()
        self.state.set_buzzer_on(False)

    def _trigger_alarm(self, source: str = "PIR motion") -> None:
        self.state.set_motion_detected(True)
        self.state.set_alarm_triggered(True)

        self.led.on()
        self.state.set_led_on(True)

        if self.buzzer is not None:
            self.buzzer.on()
            self.state.set_buzzer_on(True)

        self.logger.warning("Alarm triggered by %s", source)
        self.state.add_event(f"Alarm triggered by {source}")

    def trigger_external_alarm(self, source: str) -> None:
        if not self.state.armed:
            return

        if self.state.alarm_triggered:
            return

        self._trigger_alarm(source)


    def _clear_motion_idle(self) -> None:
        self.state.set_motion_detected(False)

        if not self.state.alarm_triggered:
            self.led.off()
            self.state.set_led_on(False)

            if self.buzzer is not None:
                self.buzzer.off()
            self.state.set_buzzer_on(False)

    def _read_motion_safe(self):
        try:
            return self.pir.motion_detected
        except RuntimeError as exc:
            if "deque mutated during iteration" in str(exc):
                self.logger.warning("PIR read skipped due to gpiozero deque race")
                time.sleep(0.05)
                return None
            raise

    def _loop(self) -> None:
        while self.running:
            try:
                motion_now = self._read_motion_safe()

                if motion_now is None:
                    time.sleep(POLL_INTERVAL)
                    continue

                if motion_now != self._last_motion_state:
                    self._last_motion_state = motion_now

                    if motion_now:
                        self.logger.info("Motion detected")
                        self.state.add_event("Motion detected")

                        if self.state.armed:
                            self._trigger_alarm()
                        else:
                            self.state.set_motion_detected(True)
                            self.led.on()
                            self.state.set_led_on(True)
                    else:
                        self.logger.info("Motion ended")
                        self.state.add_event("Motion ended")
                        self._clear_motion_idle()

                time.sleep(POLL_INTERVAL)

            except Exception as exc:
                self.logger.exception("Error in PIR loop: %s", exc)
                self.state.add_event(f"PIR loop error: {exc}")
                time.sleep(1)
