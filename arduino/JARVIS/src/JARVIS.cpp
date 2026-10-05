#include "JARVIS.h"

bool JARVIS::begin(unsigned long baud, const char* deviceName) {
  Serial.begin(baud);
  _deviceName = deviceName;
  _ready = true;
  Serial.print("JARVIS|HELLO|");
  Serial.println(_deviceName);
  return true;
}

bool JARVIS::connected() {
  return _ready;
}

bool JARVIS::readLine(String& line) {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      line = _buffer;
      _buffer = "";
      line.trim();
      return true;
    }
    if (c != '\r' && _buffer.length() < 240) _buffer += c;
  }
  return false;
}

bool JARVIS::commandReceived(const char* command) {
  String line;
  if (!readLine(line)) return false;
  String expected = "JARVIS|CMD|" + String(command);
  return line == expected;
}

bool JARVIS::send(const char* eventName, const char* value) {
  if (!_ready) return false;
  Serial.print("JARVIS|EVENT|");
  Serial.print(eventName);
  Serial.print("|");
  Serial.println(value);
  return true;
}

bool JARVIS::send(const char* eventName, long value) {
  String text = String(value);
  return send(eventName, text.c_str());
}

void JARVIS::say(const char* message) {
  send("say", message);
}
