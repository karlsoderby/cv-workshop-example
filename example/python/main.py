import time
import threading
from arduino.app_utils import App, Bridge
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection

# Configuration
CONFIDENCE_THRESHOLD = 0.5
HOLD_TIME_SEC = 1.5  # How long to keep the LED on after last detection

# State
last_detection_time = 0
is_currently_on = False

ui = WebUI()
detection_stream = VideoObjectDetection(confidence=CONFIDENCE_THRESHOLD, debounce_sec=0.0)

def handle_detections(detections: dict):
    global last_detection_time, is_currently_on
    
    highest = 0.0
    found = False
    
    for label, results in detections.items():
        for item in results:
            conf = item.get("confidence", 0.0)
            if conf > highest:
                highest = conf
                found = True
    
    if found:
        last_detection_time = time.time()
        is_currently_on = True
        try:
            Bridge.call("update_display", float(highest))
        except:
            pass

def watchdog_loop():
    global last_detection_time, is_currently_on
    while True:
        # If it's been silent longer than our HOLD_TIME
        if is_currently_on and (time.time() - last_detection_time > HOLD_TIME_SEC):
            try:
                Bridge.call("update_display", 0.0)
                is_currently_on = False
            except:
                pass
        time.sleep(0.1)

detection_stream.on_detect_all(handle_detections)

# Start the timer thread
threading.Thread(target=watchdog_loop, daemon=True).start()

App.run()