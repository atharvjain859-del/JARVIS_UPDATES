# JARVIS Serial Protocol 1

Transport: USB serial.

Messages are UTF-8 text lines terminated by `\n`.

Arduino -> JARVIS:
- `JARVIS|HELLO|<device>`
- `JARVIS|EVENT|<name>|<value>`

JARVIS -> Arduino:
- `JARVIS|CMD|<command>`

Example:

    JARVIS|CMD|LED ON

The initial protocol intentionally has no arbitrary code execution, shell commands, firmware flashing, or destructive device operations.
