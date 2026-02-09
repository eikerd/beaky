"""Ollama LLM interface with streaming and conversation history."""

import ollama
import config


class LLM:
    def __init__(self, model: str = config.LLM_MODEL):
        self.model = model
        self.client = ollama.Client(host=config.OLLAMA_HOST)
        self.history: list[dict] = [
            {"role": "system", "content": config.SYSTEM_PROMPT}
        ]

    def _trim_history(self):
        """Keep history within the configured limit, always preserving the system prompt."""
        # +1 for the system message
        max_len = config.LLM_MAX_HISTORY * 2 + 1
        if len(self.history) > max_len:
            self.history = [self.history[0]] + self.history[-(max_len - 1):]

    def _build_user_message(self, text: str, scene: str | None = None, person: str | None = None) -> str:
        """Inject vision and person context into the user message."""
        parts = []
        if scene:
            parts.append(f"[SCENE] {scene}")
        if person:
            parts.append(f"[PERSON] {person}")
        parts.append(text)
        return "\n".join(parts)

    def chat(self, user_text: str, scene: str | None = None, person: str | None = None) -> str:
        """Send a message and return the full response."""
        message = self._build_user_message(user_text, scene, person)
        self.history.append({"role": "user", "content": message})
        self._trim_history()

        response = self.client.chat(
            model=self.model,
            messages=self.history,
            options={"temperature": config.LLM_TEMPERATURE},
        )
        reply = response["message"]["content"]
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def chat_stream(self, user_text: str, scene: str | None = None, person: str | None = None):
        """Send a message and yield response chunks as they arrive."""
        message = self._build_user_message(user_text, scene, person)
        self.history.append({"role": "user", "content": message})
        self._trim_history()

        stream = self.client.chat(
            model=self.model,
            messages=self.history,
            options={"temperature": config.LLM_TEMPERATURE},
            stream=True,
        )

        full_reply = []
        for chunk in stream:
            token = chunk["message"]["content"]
            full_reply.append(token)
            yield token

        self.history.append({"role": "assistant", "content": "".join(full_reply)})

    def reset(self):
        """Clear conversation history, keeping the system prompt."""
        self.history = [self.history[0]]
