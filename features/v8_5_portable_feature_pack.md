# JARVIS V8.5 Portable Feature Pack — queued specification

**Status: queued / not installable yet.** This PR makes the ten capabilities discoverable in the update manifest and adds documentation. It does not publish executable feature payloads or change the updater installer. Existing V8 files are not changed by this repository change.

## Planned modules
1. Universal Command Router
2. System Intelligence
3. Smart App Launcher
4. Persistent Memory
5. Offline Brain
6. File Intelligence
7. Focus Mode
8. Network Watch
9. Hardware Simulator
10. Portable Profile

## Installation contract required before activation
- Publish versioned, reviewed source files and SHA-256 for every payload.
- Update the V8 updater to distinguish queued, requires_approval, and installable.
- Installer must back up destination files, validate paths against traversal, verify hashes before writing, avoid overwriting existing user data without consent, and record installed version.
- Feature install should be opt-in per package and rollbackable.
- Never execute arbitrary shell text from manifest or feature payload.
- No admin-only service/firewall/startup changes without explicit approval.
- The offline brain must disclose whether it is a rule-based fallback or a local LLM.
- Hardware simulator must not actuate physical hardware.

See JARVIS_V8.5_COMMAND_MANUAL.txt for the proposed command reference.
