#pragma once
#include <Arduino.h>

class JARVIS {
public:
  bool begin(unsigned long baud = 115200, const char* deviceName = "ARDUINO");
  bool connected();
  bool commandReceived(const char* command);
  bool send(const char* eventName, const char* value);
  bool send(const char* eventName, long value);
  void say(const char* message);

private:
  String _deviceName;
  String _buffer;
  bool _ready = false;
  bool readLine(String& line);
};
