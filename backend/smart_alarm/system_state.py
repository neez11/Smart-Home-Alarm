# smart_alarm/system_state.py

from threading import Lock
from datetime import datetime
from typing import Dict, Any, List


class SystemState:
    def __init__(self, event_limit: int = 40):
        self._lock = Lock()
        self.event_limit = event_limit

        self.armed = False
        self.motion_detected = False
        self.door_open = False
        self.alarm_triggered = False
        self.led_on = False
        self.buzzer_on = False
        self.camera_online = False
        self.last_event = "System initialized"
        self.events: List[Dict[str, Any]] = []

        self.add_event("System initialized")

    def add_event(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        event = {
            "timestamp": timestamp,
            "message": message,
        }

        with self._lock:
            self.last_event = message
            self.events.insert(0, event)
            self.events = self.events[: self.event_limit]

    def set_armed(self, value: bool) -> None:
        with self._lock:
            self.armed = value

    def set_motion_detected(self, value: bool) -> None:
        with self._lock:
            self.motion_detected = value

    def set_door_open(self, value: bool) -> None:
        with self._lock:
            self.door_open = value

    def set_alarm_triggered(self, value: bool) -> None:
        with self._lock:
            self.alarm_triggered = value

    def set_led_on(self, value: bool) -> None:
        with self._lock:
            self.led_on = value

    def set_buzzer_on(self, value: bool) -> None:
        with self._lock:
            self.buzzer_on = value

    def set_camera_online(self, value: bool) -> None:
        with self._lock:
            self.camera_online = value

    def reset_alarm_flags(self) -> None:
        with self._lock:
            self.motion_detected = False
            self.alarm_triggered = False
            self.buzzer_on = False
            self.led_on = False
            self.last_event = "Alarm reset"

        self.add_event("Alarm reset")

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "alarm_status": "armed" if self.armed else "disarmed",
                "armed": self.armed,
                "motion_detected": self.motion_detected,
                "door_open": self.door_open,
                "alarm_triggered": self.alarm_triggered,
                "led_on": self.led_on,
                "buzzer_on": self.buzzer_on,
                "camera_online": self.camera_online,
                "last_event": self.last_event,
                "events_count": len(self.events),
            }

    def get_events(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.events)
