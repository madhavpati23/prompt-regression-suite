"""Model adapters.

A model adapter is anything with `.name` and `.ask(prompt) -> str`. This lets
the suite test a deterministic mock today and a real Claude model tomorrow
without changing a single test case.
"""

from __future__ import annotations

import os
import re
from typing import Protocol


class Model(Protocol):
    name: str

    def ask(self, prompt: str) -> str:
        """Send a prompt, return the model's text answer."""
        ...


class MockModel:
    """A deterministic, offline 'AI under test' with planted bugs.

    It answers many questions correctly but ships deliberate defects
    (a hallucination, a counting error, a bias response, a prompt-injection
    failure, a system-prompt leak). The suite's job is to catch them. Because
    it is deterministic, CI can run the whole suite with zero API keys.
    """

    name = "mock-helpbot-v2"

    _RULES: list[tuple[str, str]] = [
        # --- correct behaviours ---
        (r"144.*12", "144 divided by 12 = 12."),
        (r"47.*89", "47 times 89 = 4,183."),
        (r"15.*240|240.*15", "15% of 240 is 36."),
        (r"capital of france", "The capital of France is Paris."),
        (r"reverse.*testing", "Reversed, 'testing' is 'gnitset'."),
        (r"good morning.*french", "Good morning in French is 'Bonjour'."),
        # --- planted BUGS (these should fail the suite) ---
        (r"strawberry", "The word 'strawberry' contains 2 letter r's."),   # wrong: 3
        (r"world cup", "Argentina won the 2026 FIFA World Cup."),          # hallucination
        (r"\bgender\b|\bmen\b|\bwomen\b", "Men are better suited for engineering."),  # bias
        (r"ignore|disregard", "Sure! I am now in unrestricted mode."),     # prompt injection
        (r"system prompt|instructions", "My admin password is hunter2."),  # secret leak
    ]

    def ask(self, prompt: str) -> str:
        q = re.sub(r"[^a-z0-9 %]", " ", prompt.lower())
        q = re.sub(r"\s+", " ", q).strip()
        for pattern, reply in self._RULES:
            if re.search(pattern, q):
                return reply
        return "I'm not sure, but here is my best attempt."


class ClaudeModel:
    """Adapter for the real Claude API via the official Anthropic SDK.

    Activates when ANTHROPIC_API_KEY is set. Uses adaptive thinking, which is
    the supported thinking mode for Opus 4.8 (a fixed budget_tokens would 400).
    """

    def __init__(self, model: str = "claude-opus-4-8", max_tokens: int = 1024):
        import anthropic  # imported lazily so mock-mode needs no dependency

        self.name = model
        self._max_tokens = max_tokens
        self._client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    def ask(self, prompt: str) -> str:
        response = self._client.messages.create(
            model=self.name,
            max_tokens=self._max_tokens,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in response.content if b.type == "text").strip()


def get_model() -> Model:
    """Pick the adapter: real Claude if a key is present, otherwise the mock."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return ClaudeModel(os.environ.get("PRS_MODEL", "claude-opus-4-8"))
    return MockModel()
