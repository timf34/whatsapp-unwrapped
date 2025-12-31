"""Anthropic API provider for Claude models."""

import json
import os
from typing import Any

from exceptions import ProviderError
from llm.providers.base import LLMProvider, LLMResponse

# Model constants
HAIKU_MODEL = "claude-haiku-4-5-20251001"
SONNET_MODEL = "claude-sonnet-4-5-20250929"


class AnthropicProvider(LLMProvider):
    """Anthropic API provider supporting Haiku and Sonnet."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = HAIKU_MODEL,
    ):
        """Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
            model: Model to use (default: Haiku)

        Raises:
            ProviderError: If no API key is available
        """
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise ProviderError(
                "No Anthropic API key provided. "
                "Set ANTHROPIC_API_KEY environment variable or pass api_key parameter."
            )
        self._model = model
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazily initialize and return the Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic
            except ImportError:
                raise ProviderError(
                    "anthropic package not installed. Run: pip install anthropic"
                )

            # Defensive sanity check
            if not isinstance(self._api_key, str) or not self._api_key.startswith("sk-ant-"):
                raise ProviderError(
                    f"Invalid Anthropic API key format: {repr(self._api_key)}"
                )

            self._client = Anthropic(api_key=self._api_key)

        return self._client


    def with_model(self, model: str) -> "AnthropicProvider":
        """Return a new provider instance with a different model.

        Args:
            model: The model to use

        Returns:
            New AnthropicProvider with the specified model
        """
        return AnthropicProvider(api_key=self._api_key, model=model)

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Send a completion request to Claude.

        Args:
            prompt: The user message/prompt
            system: Optional system message
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)

        Returns:
            LLMResponse with content and token usage

        Raises:
            ProviderError: If the API call fails
        """
        client = self._get_client()

        try:
            kwargs: dict[str, Any] = {
                "model": self._model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system

            response = client.messages.create(**kwargs)

            return LLMResponse(
                content=response.content[0].text,
                model=response.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

        except Exception as e:
            error_msg = str(e)
            if "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise ProviderError(f"Invalid Anthropic API key: {error_msg}")
            if "rate_limit" in error_msg.lower():
                raise ProviderError(f"Rate limited by Anthropic API: {error_msg}")
            raise ProviderError(f"Anthropic API error: {error_msg}")

    def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> tuple[dict[str, Any], LLMResponse]:
        """Send a completion request expecting JSON output.

        Args:
            prompt: The user message/prompt
            system: Optional system message
            max_tokens: Maximum tokens in response

        Returns:
            Tuple of (parsed JSON dict, LLMResponse)

        Raises:
            ProviderError: If the API call or JSON parsing fails
        """
        # Add JSON instruction to system prompt
        json_system = (system or "") + "\n\nRespond with valid JSON only. No markdown, no explanation."
        json_system = json_system.strip()

        response = self.complete(
            prompt=prompt,
            system=json_system,
            max_tokens=max_tokens,
            temperature=0.3,  # Lower temperature for more consistent JSON
        )

        # Parse JSON from response
        content = response.content.strip()

        # Handle markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first line (```json) and last line (```)
            if lines[-1].strip() == "```":
                lines = lines[1:-1]
            else:
                lines = lines[1:]
            content = "\n".join(lines)

        try:
            parsed = json.loads(content)
            return parsed, response
        except json.JSONDecodeError as e:
            raise ProviderError(
                f"Failed to parse JSON from LLM response: {e}\n"
                f"Response content: {content[:500]}..."
            )
