#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>

Arduino_LED_Matrix matrix;
const uint32_t blank_frame[] = {0, 0, 0, 0};

void setup() {
  matrix.begin();
  
  // LED3_G: HIGH = Off, LOW = On
  pinMode(LED3_G, OUTPUT);
  digitalWrite(LED3_G, HIGH); 

  Bridge.begin();
  Bridge.provide("update_display", update_display);
  
  matrix.loadFrame(blank_frame);
}

void loop() { }

void update_display(float confidence) {
  // Turn off if confidence is 0 (sent by watchdog) or too low
  if (confidence < 0.1) { 
    digitalWrite(LED3_G, HIGH); // OFF
    matrix.loadFrame(blank_frame);
    return;
  }

  // Object detected
  digitalWrite(LED3_G, LOW); // ON

  int score = (int)(confidence * 100);
  matrix.beginDraw();
  matrix.clear();
  matrix.stroke(0xFFFFFFFF);
  matrix.textFont(Font_4x6);
  matrix.beginText(1, 1, 0xFFFFFFFF);
  matrix.print(score);
  matrix.print("%");
  matrix.endText();
  matrix.endDraw();
}