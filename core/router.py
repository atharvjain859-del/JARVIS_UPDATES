import os
import subprocess
import urllib.parse
import webbrowser

from voice.speech import speak
from voice.personality import jarvis_reply

try:
    from core.ai import JARVISAI
except Exception:
    JARVISAI = None


class Router:
    def __init__(self, app):
        self.app = app
        self.ai = getattr(app, "ai", None) or getattr(app, "AI", None)
        if self.ai is None and JARVISAI is not None:
            try:
                import json
                from pathlib import Path
                config_path = Path(__file__).resolve().parents[1] / "config.json"
                config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
                api_key = config.get("api_key", "")
                model = config.get("model", "")
                provider = config.get("provider", "")
                if api_key:
                    self.ai = JARVISAI(api_key=api_key, model=model, provider=provider)
            except Exception:
                self.ai = None

    def say(self, message, speak_it=True):
        message = str(message)
        print("JARVIS:", message)
        if speak_it:
            speak(message)
        return message

    def handle(self, command):
        x = command.strip()
        l = x.lower()
        if not x:
            return

        if l in ("exit", "quit", "shutdown", "stop jarvis"):
            self.say(jarvis_reply("shutdown") or "Shutting down. Try not to miss me too much.")
            self.app.running = False
            return

        if l in ("help", "commands", "?"):
            return self.say(
                "Commands: status, system, security, current, clear current, mission <text>, "
                "remember <text>, memory, monitor <url> every <n> seconds, list monitors, "
                "stop monitoring <url>, open <target>, search google <query>, search youtube <query>, "
                "run <program>, voice, exit. Ask me anything else normally and I'll use my AI brain."
            )

        if l in ("voice", "voice mode", "start voice"):
            return self.voice_mode()

        if l == "status":
            return self.say(f"JARVIS V8 online. {len(self.app.registry.skills)} skills registered.")
        if l == "system":
            return self.say(self.app.diagnostics.system())
        if l == "security":
            return self.say(self.app.security.status())
        if l == "current":
            return self.say(self.app.context.get())
        if l == "clear current":
            self.app.context.clear()
            return self.say("Current mission cleared.")
        if l.startswith("mission "):
            self.app.context.set(x[8:].strip())
            return self.say("Current mission updated.")
        if l.startswith("remember "):
            self.app.memory.add(x[9:].strip())
            return self.say("Remembered. I have successfully added that to my memory.")
        if l == "memory":
            return self.say(self.app.memory.list())
        if l.startswith("monitor "):
            return self.say(self.app.monitors.parse_and_add(x[8:]))
        if l == "list monitors":
            return self.say(self.app.monitors.list())
        if l.startswith("stop monitoring "):
            return self.say(self.app.monitors.remove(x[16:].strip()))
        if l == "stop all monitors":
            self.app.monitors.stop_all()
            return self.say("All website monitors have been stopped.")
        if l.startswith("open "):
            return self.open_target(x[5:].strip())
        if l.startswith("search google "):
            return self.search("https://www.google.com/search?q=", x[14:])
        if l.startswith("search youtube "):
            return self.search("https://www.youtube.com/results?search_query=", x[15:])
        if l.startswith("run "):
            return self.run_program(x[4:].strip())

        conversational = jarvis_reply(x)
        if conversational is not None:
            return self.say(conversational)

        skill = self.app.registry.match(l)
        if skill:
            try:
                return self.say(skill.handle(x))
            except Exception as exc:
                return self.say(f"That skill failed: {exc}")

        # Unknown natural-language requests go to the real AI brain.
        return self.ask_ai(x)

    def ask_ai(self, command):
        if self.ai is None:
            return self.say(
                "I understood the question, but my AI brain is not connected. "
                "Check that your API key is present in config.json."
            )
        try:
            response = self.ai.ask(command)
            answer = response.content if hasattr(response, "content") else str(response)
            return self.say(answer)
        except Exception as exc:
            return self.say(f"My AI brain encountered an error: {exc}")

    def voice_mode(self):
        try:
            from voice.recognition import listen
        except Exception as exc:
            return self.say(f"Voice recognition could not load: {exc}")

        self.say("Voice mode activated. Finally, someone decided to use my voice.")
        self.say("Ask me anything. Say 'exit voice' when you want to return to typing.")

        while self.app.running:
            try:
                text = listen(timeout=5, phrase_time_limit=8)
            except Exception as exc:
                self.say(f"Microphone error: {exc}")
                return
            if not text:
                continue
            print("YOU:", text)
            if text.lower().strip() in ("exit voice", "stop voice", "voice off", "leave voice mode", "exit the voice"):
                self.say("Voice mode deactivated. Try not to miss me too much.")
                return
            self.handle(text)

    def search(self, prefix, query):
        webbrowser.open(prefix + urllib.parse.quote_plus(query.strip()))
        return self.say("Search opened. Your internet connection has been given a small task.")

    def open_target(self, target):
        websites = {
            "youtube": "https://youtube.com",
            "github": "https://github.com",
            "chatgpt": "https://chatgpt.com",
            "google": "https://google.com",
            "instagram": "https://instagram.com",
            "reddit": "https://reddit.com",
        }
        key = target.lower()
        if key in websites:
            webbrowser.open(websites[key])
            return self.say(f"Opening {target}. Try not to break anything while I'm gone.")
        if target.startswith(("http://", "https://")):
            webbrowser.open(target)
            return self.say("Opening the website.")
        try:
            os.startfile(target)
            return self.say(f"Opening {target}.")
        except Exception as exc:
            return self.say(f"I couldn't open that: {exc}")

    def run_program(self, program):
        try:
            subprocess.Popen(program, shell=True)
            return self.say("Program started. I shall pretend that was exactly what you intended.")
        except Exception as exc:
            return self.say(f"I couldn't start that program: {exc}")
