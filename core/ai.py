"""Real conversational/reasoning brain for JARVIS V8.

Supports OpenAI Responses API and OpenAI-compatible chat-completions
providers such as OpenRouter. No third-party SDK is required.
"""

import json
import os
import urllib.error
import urllib.request


class JARVISAI:
    def __init__(self, api_key="", model="", provider=""):
        self.api_key = (api_key or os.getenv("JARVIS_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
        self.provider = (provider or os.getenv("JARVIS_AI_PROVIDER") or "").strip().lower()
        self.model = (model or os.getenv("JARVIS_AI_MODEL") or "").strip()
        self.history = []

        if not self.model:
            self.model = "gpt-5.6-luna"

        # A model beginning with openrouter/ automatically selects OpenRouter.
        if self.model.lower().startswith("openrouter/"):
            self.provider = "openrouter"

        if not self.provider:
            self.provider = "openai"

        self.system_prompt = (
            "You are JARVIS, a capable desktop AI assistant. "
            "Be intelligent, concise, calm, technically precise, and helpful. "
            "Use a polished dry sense of humor and light sarcasm when appropriate, "
            "but never let jokes interfere with solving the user's problem. "
            "The user is building software and electronics projects, so explain "
            "technical concepts clearly and provide practical steps and code when useful. "
            "Do not pretend you performed an action you cannot actually perform. "
            "When a request is ambiguous, ask a short clarification. "
            "When debugging, reason from the evidence instead of guessing."
        )

    def _request_json(self, url, payload, headers):
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = response.read().decode("utf-8", errors="replace")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(body)
                message = detail.get("error", {}).get("message") or body
            except Exception:
                message = body or str(exc)
            raise RuntimeError(f"AI API error {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"AI network error: {exc.reason}") from exc

    def _openai(self, text):
        payload = {
            "model": self.model,
            "instructions": self.system_prompt,
            "input": self._input_messages(text),
        }
        result = self._request_json(
            "https://api.openai.com/v1/responses",
            payload,
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        answer = result.get("output_text")
        if answer:
            return answer.strip()

        # Defensive fallback for response objects that do not expose output_text.
        pieces = []
        for item in result.get("output", []) or []:
            for content in item.get("content", []) or []:
                if content.get("type") in ("output_text", "text") and content.get("text"):
                    pieces.append(content["text"])
        if pieces:
            return "\n".join(pieces).strip()
        raise RuntimeError("The AI returned no text response.")

    def _openrouter(self, text):
        model = self.model
        if model.lower().startswith("openrouter/"):
            model = model.split("/", 1)[1]
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                *self._chat_messages(text),
            ],
        }
        result = self._request_json(
            "https://openrouter.ai/api/v1/chat/completions",
            payload,
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/atharvjain859-del/JARVIS_UPDATES",
                "X-Title": "JARVIS Desktop Assistant",
            },
        )
        choices = result.get("choices") or []
        if not choices:
            raise RuntimeError("The AI returned no choices.")
        message = choices[0].get("message", {})
        answer = message.get("content")
        if not answer:
            raise RuntimeError("The AI returned an empty response.")
        return str(answer).strip()

    def _chat_messages(self, text):
        messages = list(self.history)
        messages.append({"role": "user", "content": text})
        return messages[-20:]

    def _input_messages(self, text):
        messages = []
        for item in self._chat_messages(text):
            messages.append({
                "role": item["role"],
                "content": [{"type": "input_text", "text": item["content"]}],
            })
        return messages

    def ask(self, text):
        text = str(text).strip()
        if not text:
            raise ValueError("Empty AI request.")
        if not self.api_key:
            raise RuntimeError(
                "No AI API key configured. Add api_key to config.json or set JARVIS_API_KEY."
            )

        if self.provider in ("openrouter", "router"):
            answer = self._openrouter(text)
        else:
            answer = self._openai(text)

        self.history.append({"role": "user", "content": text})
        self.history.append({"role": "assistant", "content": answer})
        self.history = self.history[-20:]
        return _Response(answer)


class _Response:
    def __init__(self, content):
        self.content = content
