#include <JARVIS.h>

JARVIS jarvis;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  jarvis.begin(115200, "MY_ARDUINO");
}

void loop() {
  if (jarvis.commandReceived("LED ON")) {
    digitalWrite(LED_BUILTIN, HIGH);
    jarvis.say("LED ON");
  }

  if (jarvis.commandReceived("LED OFF")) {
    digitalWrite(LED_BUILTIN, LOW);
    jarvis.say("LED OFF");
  }
}
