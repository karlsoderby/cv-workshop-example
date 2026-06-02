# Detect Objects on Camera with LED Matrix Feedback

The **Detect Objects on Camera with LED Matrix Feedback** example lets you detect objects on a live feed from a USB camera and displays the confidence score as a percentage on the onboard LED Matrix in real-time.

**Note:** This example must be run in **Network Mode** in the Arduino App Lab, since it requires a USB-C hub and a USB camera.

![Detect Objects on Camera](assets/docs_assets/video-object-detection.png)

This example uses a pre-trained model to detect objects on a live video feed from a camera. The workflow involves continuously getting frames from a USB camera, processing them through an AI model using the `video_objectdetection` Brick, and sending the highest confidence score to the Arduino sketch via the Bridge. The sketch then renders the score as a percentage on the LED Matrix. The App is managed from an interactive web interface.

## Bricks Used

The example uses the following Bricks:

- `web_ui`: Brick to create a web interface to display the live camera feed.
- `video_objectdetection`: Brick to detect objects within a live video feed from a camera.

## Hardware and Software Requirements

### Hardware

- [Arduino® UNO Q](https://store.arduino.cc/products/uno-q)
- USB camera (x1)
- USB-C® hub adapter with external power (x1)
- A power supply (5 V, 3 A) for the USB hub (e.g. a phone charger)
- Personal computer with internet access

### Software

- Arduino App Lab

## How to Use the Example

1. Connect the USB-C hub to the UNO Q and the USB camera.
   ![Hardware setup](assets/docs_assets/hardware-setup.png)
2. Attach the external power supply to the USB-C hub to power everything.
3. Run the App.
   ![Arduino App Lab - Run App](assets/docs_assets/launch-app.png)
4. The App should open automatically in the web browser. You can open it manually via `<board-name>.local:7000`.
5. Position any object in front of the camera. The LED Matrix on the UNO Q displays the confidence score (e.g. `75%`) when an object is detected, and clears after 1.5 seconds of no detection.

>Note that the default model loaded in this example is Face Detection. To swap for other models (such as generic object), go to Video Object Detection Brick > AI Models tab and select another model. Here you can also choose a custom model, and train it using the Edge Impulse platform.

![Example of special reaction](assets/docs_assets/special-detection.png)

## How it Works

This example hosts a Web UI that shows the live video feed from the USB camera. The video stream is processed using the `video_objectdetection` Brick. When one or more objects are detected, the highest confidence score is forwarded to the Arduino sketch via the Bridge. The sketch renders the score as a percentage on the LED Matrix and lights the green status LED (`LED3_G`). If no detection occurs for more than 1.5 seconds, the display is cleared.

Here is a brief explanation of the full-stack application:

### 🔧 Backend (main.py)

- Initializes the app Bricks:
  - **WebUI** (`ui = WebUI()`): serves the live camera feed to the web interface.
  - **VideoObjectDetection** (`detection_stream = VideoObjectDetection(confidence=0.5, debounce_sec=0.0)`): runs object detection on the video stream with a 50% confidence threshold.

- Wires detection events to actions using a callback:
  - `on_detect_all(handle_detections)`: iterates all detected labels, picks the highest confidence score, and calls `Bridge.call("update_display", float(highest))` to send it to the sketch.

- **Watchdog thread**:
  - Runs in the background and calls `Bridge.call("update_display", 0.0)` if no detection has occurred for more than `HOLD_TIME_SEC` (1.5 s), clearing the LED Matrix display.

- Runs with `App.run()`, which starts the internal event loop and keeps the detection stream alive.

---

### 🔌 Sketch (sketch.ino)

- Registers a Bridge handler: `Bridge.provide("update_display", update_display)`.
- `update_display(float confidence)`:
  - If `confidence < 0.1` (sent by the watchdog): turns off `LED3_G` and clears the LED Matrix.
  - Otherwise: turns on `LED3_G`, converts confidence to an integer percentage, and renders it as text (e.g. `75%`) on the LED Matrix using `ArduinoGraphics`.

---

### 💻 Frontend (index.html + app.js)

- **Video feed**: iframe auto-retries `/embed` until the camera stream is available.
- **Connection status**: shows an error message if the WebSocket connection drops.

---

## Understanding the Code

Once the application is running, you can open it in your browser by navigating to `<BOARD-IP-ADDRESS>:7000`.
At that point, the device begins performing the following:

- Serving the **object detection UI** and exposing realtime transports.

    The UI is hosted by the `WebUI` Brick and communicates with the backend via WebSocket (Socket.IO).  
    The backend pushes detection messages whenever new objects are found.

    ```python
    from arduino.app_bricks.web_ui import WebUI
    from arduino.app_bricks.video_objectdetection import VideoObjectDetection
    from datetime import datetime, UTC

    ui = WebUI()
    detection_stream = VideoObjectDetection()

    ui.on_message("override_th",
                  lambda sid, threshold: detection_stream.override_threshold(threshold))

    detection_stream.on_detect_all(send_detections_to_ui)
    ```

    - `detection` (WebSocket message): JSON entry with label, confidence, and timestamp sent to the UI.  
    - `override_th` (WebSocket → backend): adjusts the confidence threshold live.

- Processing detections and broadcasting updates.

    When the model detects objects, the backend:

    1. Iterates over all detected objects with their confidence scores.  
    2. Attaches an ISO 8601 UTC timestamp.  
    3. Publishes each detection as a JSON entry to the frontend channel `detection`.

    ```python
    def send_detections_to_ui(detections: dict):
        for key, value in detections.items():
            entry = {
                "content": key,
                "confidence": value,
                "timestamp": datetime.now(UTC).isoformat()
            }
            ui.send_message("detection", message=entry)
    ```

- Rendering and interacting on the frontend.

    The **index.html + app.js** bundle defines the interface:

    - A **video feed iframe** auto-retries `/embed` until the camera stream is live.  
    - A **confidence control** (slider + input + reset) lets the user adjust the detection threshold.  
    - A **feedback section** shows animations and messages for known classes (cat, dog, cup, clock, potted plant, etc.).  
    - A **recent detections list** displays the latest 5 detections with percentage and timestamp.  

    ```javascript
    const socket = io(`http://${window.location.host}`);

    socket.on('detection', (message) => {
        printDetection(message);   // update history
        renderDetections();        // redraw the list
        updateFeedback(message);   // update feedback panel
    });
    ```

    - `detection` (WebSocket): received whenever the backend publishes results.  
    - The slider and input dynamically update the backend threshold (`override_th`).  
    - If the connection drops, an error banner is shown (`error-container`).  

- Executing the event loop.

    Finally, the backend keeps everything alive with:

    ```python
    App.run()
    ```

    This maintains the object detection stream, callback hooks, threshold overrides, and WebSocket communication with the frontend.
