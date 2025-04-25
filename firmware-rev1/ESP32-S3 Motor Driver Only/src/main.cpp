#include <Wire.h>
#include <Adafruit_DRV2605.h>
#include <Arduino.h>
#include <FastLED.h>

#define DRVADDR 0x5A

#define NUM_LEDS 1

CRGB leds[NUM_LEDS];

int effect = 0;

Adafruit_DRV2605 drv;

int pins[10] = {4, 5, 16, 15, 7, 6, 11, 12, 13, 14};
bool statLEDS[10];
void setLEDs(bool ledState[10]) {
  for(int i = 0; i < 10; i++) {
    digitalWrite(pins[i], ledState[i]);
  }
}
void ledTwinkle() {
  for(int i = 0; i < 10; i++) {
    if(i % 2 == 0) {
      statLEDS[i] = 0;
    } else {
      statLEDS[i] = 1;
    }
  }
  setLEDs(statLEDS);
  delay(100);
  for(int i = 0; i < 10; i++) {
    if(i % 2 == 0) {
      statLEDS[i] = 1;
    } else {
      statLEDS[i] = 0;
    }
  }
  setLEDs(statLEDS);
  delay(100); 
}
void ledSwipe(int del) {
  for(int i = 0; i < 10; i++) {
    statLEDS[i] = 1;
    setLEDs(statLEDS);
    delay(del);
  }
  for(int i = 0; i < 10; i++) {
    statLEDS[i] = 0;
    setLEDs(statLEDS);
    delay(del);
  }
}

void setup() {
  // put your setup code here, to run once:
  FastLED.addLeds<WS2812B, 38, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(15);
  leds[0] = CRGB::Black;
  FastLED.show();
  delay(250);

  // if(!haptic.begin()) {
  if(!drv.begin()) {
    while(1) {
      leds[0] = CRGB::Red;
      FastLED.show();
      delay(500);
      leds[0] = CRGB::Black;
      FastLED.show();
      delay(500);
      
    }
  } else {
    for(int i = 0; i < 3; i++) {
      leds[0] = CRGB::Green;
      FastLED.show();
      delay(250);
      leds[0] = CRGB::Green;
      FastLED.show();
      delay(250);
    }
  }
  drv.setMode(DRV2605_MODE_REALTIME);

  delay(100);
}

uint8_t rtp_index = 0;
uint8_t rtp[] = {
  0x30, 100, 0x32, 100, 
  0x34, 100, 0x36, 100, 
  0x38, 100, 0x3A, 100,
  0x00, 100,
  0x40, 200, 0x00, 100, 
  0x40, 200, 0x00, 100, 
  0x40, 200, 0x00, 100
};

void loop() {
  // // put your main code here, to run repeatedly:
  // haptic.setIntensity(128);
  // leds[0] = CRGB(10,255,100);
  // FastLED.show();
  // delay(200);
  // leds[0] = CRGB(255,110,0);
  // FastLED.show();
  // delay(200);
  // //haptic.setIntensity(0);
  // leds[0] = CRGB(200,0,255);
  // FastLED.show();
  // delay(200);
  // leds[0] = CRGB(255,255,255);
  // FastLED.show();
  // delay(200);

  // delay(1000);
  if (rtp_index < sizeof(rtp)/sizeof(rtp[0])) {
    drv.setRealtimeValue(rtp[rtp_index]);
    rtp_index++;
    delay(rtp[rtp_index]);
    rtp_index++;
  } else {
    drv.setRealtimeValue(0x00);
    delay(1000);
    rtp_index = 0;
  }
  
}