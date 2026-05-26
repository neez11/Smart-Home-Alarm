import loggindg


def setup_logger(name="smart_alarm"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.propagate = False

    return logger
find ~/project1 -name "*.py" | xargs grep -n "class SystemState"
nano ~/project1/smart_alarm/state.py
from collections import deque
from threading import Lock
from datetime import datetime


class SystemState:
    def init(self):
        self.lock = Lock()

        self.armed = False
        self.motion_detected = False
        self.alarm_triggered = False
        self.buzzer_active = False
        self.led_on = False
        self.camera_online = False
        self.last_updated = datetime.now().strftime("%H:%M:%S")

        self.events = deque(maxlen=50)

    def add_event(self, message, room="System", event_type="info", icon="shield"):
        with self.lock:
            self.events.appendleft({
                "id": str(datetime.now().timestamp()),
                "time": datetime.now().strftime("%H:%M:%S"),
                "message": message,
                "room": room,
                "type": event_type,
                "icon": icon,
            })
            self.last_updated = datetime.now().strftime("%H:%M:%S")

    def get_events(self):
        with self.lock:
            return list(self.events)

    def get_status(self):
        with self.lock:
            return {
                "armed": self.armed,
                "motion_detected": self.motion_detected,
                "alarm_triggered": self.alarm_triggered,
                "buzzer_active": self.buzzer_active,
                "led_on": self.led_on,
                "camera_online": self.camera_online,
                "last_updated": self.last_updated,
            }
