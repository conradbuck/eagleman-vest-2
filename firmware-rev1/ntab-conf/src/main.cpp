#include <Wire.h>
#include <Adafruit_DRV2605.h>
#include <Arduino.h>

#define TCAADDR_UPPER 0x70
#define TCAADDR_LOWER 0x74
#define TCA_UPP_RST 47
#define TCA_LOW_RST 48
#define DRVADDR 0x5A

#define SDA_PIN 8
#define SCL_PIN 9

#define DRV_EN 10



/*
    LED funcions

*/ 
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
void errorFlash(int x) { //0, 1, 2, 3, 4
  if (x > 4 || x < 0) {
    x = 0;
  }
  for(int i = 0; i < 3; i++) {
    statLEDS[x];
    // statLEDS[2 * (x + 1) - 2] = 1;
    // statLEDS[2 * (x + 1) - 1] = 1;
    setLEDs(statLEDS);
    delay(200);
    statLEDS[x];
    // statLEDS[2 * (x + 1) - 2] = 0;
    // statLEDS[2 * (x + 1) - 1] = 0;
    setLEDs(statLEDS);
    delay(200);
  }
}




void resetUmux() {
  digitalWrite(TCA_UPP_RST, LOW);
  delay(10);
  digitalWrite(TCA_UPP_RST, HIGH);
}
void resetLmux() {
  digitalWrite(TCA_LOW_RST, LOW);
  delay(10);
  digitalWrite(TCA_LOW_RST, HIGH);
}


void disconnectUmux() {
  Wire.beginTransmission(TCAADDR_UPPER);
  Wire.write(0x00);
  Wire.endTransmission();
}
void disconnectLmux() {
  Wire.beginTransmission(TCAADDR_LOWER);
  Wire.write(0x00);
  Wire.endTransmission();
}

class HapticMotorDriver {
private:
    Adafruit_DRV2605 drv;
    uint8_t i2c_mux_address;
    uint8_t motor_channel;

    void selectChannel(uint8_t i) { //select the mux output channel [0,7]
      if (i > 7) return;
      Wire.beginTransmission(i2c_mux_address); // i2c_mux_address is taken from the private variables
      Wire.write(1 << i);
      Wire.endTransmission(); 
      // delay(10); 
    }

public:
    HapticMotorDriver(uint8_t mux_addr, uint8_t channel) : i2c_mux_address(mux_addr), motor_channel(channel) {}

    bool begin() {
      selectChannel(motor_channel);
      if(!drv.begin()) {
        errorFlash(4);
        return false; // Initialization failed
      }
      drv.selectLibrary(1); // Select effect library
      drv.setMode(DRV2605_MODE_REALTIME); // Use real-time playback mode
      return true;
    }
    void setIntensity(uint8_t intensity) {
      selectChannel(motor_channel);
      drv.setRealtimeValue(intensity);
    }
};



static constexpr std::array<uint8_t, 10> driver_mux_addr = {4, 5, 6, 7, 1, 0, 0, 1, 2, 3};
static constexpr std::array<uint8_t, 10> driver_mux_sel = {TCAADDR_UPPER, TCAADDR_UPPER, TCAADDR_UPPER, TCAADDR_UPPER, TCAADDR_LOWER, TCAADDR_LOWER, TCAADDR_UPPER, TCAADDR_UPPER, TCAADDR_UPPER, TCAADDR_UPPER};
HapticMotorDriver* motors[10];

bool spinMotor(int index, uint8_t intensity) {
  if(index > 9) {
    return false;
  }
  if(index == 4 || index == 5) {
    disconnectUmux();
  } else {
    disconnectLmux();
  }
  motors[index]->setIntensity(intensity);
  if(intensity > 0) {
    statLEDS[index] = 1;
  } else {
    statLEDS[index] = 0;
  }
  setLEDs(statLEDS);
  return true;
}

bool setAllMotors(const std::array<uint8_t,10>& setting_packet) {
  for (int i=0; i<10; i++) {
    if(!spinMotor(i, setting_packet[i])) {
      return false;
    } else {}
  }
  return true;

}





void setup() {
  Wire.begin(SDA_PIN, SCL_PIN); // setup for I2C
  pinMode(DRV_EN, OUTPUT);
  pinMode(TCA_UPP_RST, OUTPUT);
  pinMode(TCA_LOW_RST, OUTPUT);
  for(int i = 0; i < 10; i++) { // LED config
    pinMode(pins[i], OUTPUT);
    statLEDS[i] = 0;
  }
  delay(100);
  digitalWrite(DRV_EN, HIGH); // enabling all drivers 
  resetUmux(); // resetting TCA9548A
  resetLmux(); // resetting TCA9548A

  // initialize the drivers  
  for(int i = 0; i < 10; i++) {
    motors[i] = new HapticMotorDriver( driver_mux_sel[i], driver_mux_addr[i]);
    if (!motors[i]->begin()) {
      errorFlash(i); // Visual indication for which one failed
      while (1); // Halt on error  // TODO: make this an actual error 
    } else { /* ledSwipe(23); */}
  }

  std::array<uint8_t, 10> packet = {0x00, 0x80, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00};

  bool val = setAllMotors(packet);
  delay(1000);
  packet = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
  val = setAllMotors(packet);
  delay(1000);
  packet = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x80};
  val = setAllMotors(packet);
  delay(1000);
  packet = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
  val = setAllMotors(packet);
  delay(1000);



  // spinMotor(1, 128); //spin motor 0 and 128/255 intensity
  // delay(1000);
  // spinMotor(1, 0);
  // delay(200);
  // spinMotor(9, 128); //spin motor 0 and 128/255 intensity
  // delay(1000);
  // spinMotor(9, 0);
  // delay(200);
  // spinMotor(6, 128); //spin motor 0 and 128/255 intensity
  // delay(1000);
  // spinMotor(6, 0);
  // delay(200);
  // spinMotor(5, 128); //spin motor 0 and 128/255 intensity
  // delay(1000);
  // spinMotor(5, 0);
  // delay(200);
  // spinMotor(6, 128); //spin motor 0 and 128/255 intensity
  // delay(1000);
  // spinMotor(6, 0);
  // delay(200);
};

void loop() {
  ledSwipe(76);
};