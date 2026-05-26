import json
import paho.mqtt.client as mqtt


class ZigbeeDoorListener:
    def __init__(self, state, logger, controller, broker_host, broker_port, topic):
        self.state = state
        self.logger = logger
        self.controller = controller
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.client = None

    def start(self):
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.connect(self.broker_host, self.broker_port, 60)
        self.client.loop_start()
        if self.logger is not None:
            self.logger.info("ZigbeeDoorListener started")
        if self.state is not None:
            self.state.add_event("Zigbee door listener started")

    def stop(self):
        if self.client is not None:
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None

    def _on_connect(self, client, userdata, flags, rc):
        if self.logger is not None:
            self.logger.info("MQTT connected with code %s", rc)
        client.subscribe(self.topic)

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())

            if "contact" not in data:
                return

            door_open = not bool(data["contact"])

            if self.state is None:
                return

            current = self.state.get_status()["door_open"]
            self.state.set_door_open(door_open)

            if door_open != current:
                if door_open:
                    if self.logger is not None:
                        self.logger.info("Front door opened")
                    self.state.add_event("Front door opened")

                    if self.controller is not None and self.state.get_status()["armed"]:
                        self.controller.trigger_external_alarm("front door")
                else:
                    if self.logger is not None:
                        self.logger.info("Front door closed")
                    self.state.add_event("Front door closed")

        except Exception as exc:
            if self.logger is not None:
                self.logger.exception("MQTT door listener error: %s", exc)
            if self.state is not None:
                self.state.add_event(f"MQTT door listener error: {exc}")
