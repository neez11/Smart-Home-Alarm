# app.py
from smart_alarm.buzzer import BuzzerService
from smart_alarm.zigbee_door_listener import ZigbeeDoorListener
from flask import Flask, jsonify, Response
from flask_cors import CORS

from config import (
    API_HOST,
    API_PORT,
    DEBUG,
    EVENT_LIMIT,
    GPIO_BUZZER,
    ENABLE_BUZZER,
    ZIGBEE_MQTT_ENABLED,
    ZIGBEE_MQTT_BROKER,
    ZIGBEE_MQTT_PORT,
    ZIGBEE_MQTT_TOPIC,
)
from smart_alarm.logger import setup_logger
from smart_alarm.system_state import SystemState
from smart_alarm.pir_sensor import PirAlarmController
from smart_alarm.camera_service import CameraService

logger = setup_logger()
state = SystemState(event_limit=EVENT_LIMIT)
buzzer = BuzzerService(pin=GPIO_BUZZER) if ENABLE_BUZZER else None
controller = PirAlarmController(state=state, logger=logger, buzzer=buzzer)
camera_service = CameraService(logger=logger, state=state)
door_listener = ZigbeeDoorListener(
    state=state,
    logger=logger,
    controller=controller,
    broker_host=ZIGBEE_MQTT_BROKER,
    broker_port=ZIGBEE_MQTT_PORT,
    topic=ZIGBEE_MQTT_TOPIC,
) if ZIGBEE_MQTT_ENABLED else None

app = Flask(__name__)
CORS(app)


@app.route("/api/test-buzzer", methods=["POST"])
def api_test_buzzer():
    if buzzer is not None:
        buzzer.alarm_pattern()

    return jsonify({
        "ok": True,
        "message": "Buzzer test completed"
    }), 200


@app.route("/api/arm", methods=["POST"])
def api_arm():
    controller.arm()

    if buzzer is not None:
        buzzer.beep()

    return jsonify({
        "ok": True,
        "message": "System armed",
        "status": state.get_status()
    }), 200


@app.route("/api/disarm", methods=["POST"])
def api_disarm():
    controller.disarm()

    if buzzer is not None:
        buzzer.beep()

    return jsonify({
        "ok": True,
        "message": "System disarmed",
        "status": state.get_status()
    }), 200


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "ok": True,
        "service": "smart-hemlarm-backend"
    }), 200


@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify(state.get_status()), 200


@app.route("/api/events", methods=["GET"])
def api_events():
    return jsonify({
        "events": state.get_events()
    }), 200


@app.route("/api/reset", methods=["POST"])
def api_reset():
    controller.reset_alarm()

    return jsonify({
        "ok": True,
        "message": "Alarm reset",
        "status": state.get_status()
    }), 200


@app.route("/api/test", methods=["POST"])
def api_test():
    controller.test_outputs(duration=1.0)

    return jsonify({
        "ok": True,
        "message": "Output test completed",
        "status": state.get_status()
    }), 200


@app.route("/api/camera-stream")
def camera_stream():
    from time import sleep

    def generate():
        while True:
            status = state.get_status()

            if not status.get("alarm_triggered", False):
                break

            frame = camera_service.get_latest_image_bytes()
            if frame is None:
                sleep(0.2)
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )

            sleep(0.2)

    response = Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

def main():
    logger.info("Starting backend on %s:%s", API_HOST, API_PORT)
    state.add_event("Backend starting")

    controller.start()

    if door_listener is not None:
        door_listener.start()

    if buzzer is not None:
        buzzer.beep()

    try:
        app.run(host=API_HOST, port=API_PORT, debug=DEBUG, threaded=True, use_reloader=False)
    finally:
        if door_listener is not None:
            door_listener.stop()

        controller.stop()
        logger.info("Backend stopped")



if __name__ == "__main__":
    main()
