"""
Thin wrapper around Google's Gemini API.

Kept deliberately small and provider-isolated: every bot in this framework
calls `GeminiClient.generate(...)`, never the Gemini SDK directly. That is
what makes the "modular, re-usable across systems" requirement in the job
post real rather than a slogan -- swapping or mocking the model later means
editing this one file, not every bot.

YOU MUST SUPPLY YOUR OWN KEY. This repo never ships one.
  export GEMINI_API_KEY=...        (https://aistudio.google.com/apikey)
"""
from __future__ import annotations

import os
from dataclasses import dataclass


class GeminiNotConfigured(RuntimeError):
    pass


@dataclass
class GeminiClient:
    model: str = "gemini-2.5-flash"
    api_key: str | None = None

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.getenv("GEMINI_API_KEY", "")

    def _require_key(self) -> None:
        if not self.api_key:
            raise GeminiNotConfigured(
                "GEMINI_API_KEY is not set. Get a key at "
                "https://aistudio.google.com/apikey and `export GEMINI_API_KEY=...`"
            )

    def generate(self, prompt: str, system: str | None = None, max_tokens: int = 512) -> str:
        """Return Gemini's plain-text reply to `prompt`. Raises GeminiNotConfigured
        if no key is set, and re-raises any SDK/network error so callers' error
        handling (see core.logger.ActivityLogger.step) can log it properly."""
        self._require_key()
        try:
            from google import genai  # google-genai package
        except ImportError as exc:  # pragma: no cover - import-time guard
            raise RuntimeError(
                "pip install google-genai (see requirements.txt)"
            ) from exc

        client = genai.Client(api_key=self.api_key)
        config = {"max_output_tokens": max_tokens}
        if system:
            config["system_instruction"] = system
        response = client.models.generate_content(
            model=self.model, contents=prompt, config=config
        )
        return (response.text or "").strip()
