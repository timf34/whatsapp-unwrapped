"""OpenAI API provider for GPT models."""

import json
import os
from typing import Any

from exceptions import ProviderError
from llm.providers.base import LLMProvider, LLMResponse

# Model constants - GPT equivalents to Claude models
GPT_MINI_MODEL = "gpt-5-mini-2025-08-07"  # Equivalent to Haiku
GPT_MAIN_MODEL = "gpt-5.2-2025-12-11"  # Equivalent to Sonnet


class OpenAIProvider(LLMProvider):
    """OpenAI API provider supporting GPT models."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = GPT_MINI_MODEL,
    ):
        """Initialize the OpenAI provider.

        Args:
            api_key: OpenAI API key. Falls back to OPENAI_API_KEY env var.
            model: Model to use (default: GPT-5-mini)

        Raises:
            ProviderError: If no API key is available
        """
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise ProviderError(
                "No OpenAI API key provided. "
                "Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )
        self._model = model
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazily initialize and return the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ProviderError(
                    "openai package not installed. Run: pip install openai"
                )

            self._client = OpenAI(api_key=self._api_key)

        return self._client

    def with_model(self, model: str) -> "OpenAIProvider":
        """Return a new provider instance with a different model.

        Args:
            model: The model to use

        Returns:
            New OpenAIProvider with the specified model
        """
        return OpenAIProvider(api_key=self._api_key, model=model)

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Send a completion request to GPT.

        Args:
            prompt: The user message/prompt
            system: Optional system message
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (ignored for GPT-5 models)

        Returns:
            LLMResponse with content and token usage

        Raises:
            ProviderError: If the API call fails
        """
        client = self._get_client()

        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            # Note: GPT-5 models don't support temperature parameter
            response = client.chat.completions.create(
                model=self._model,
                max_completion_tokens=max_tokens,
                messages=messages,
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
            )

        except Exception as e:
            error_msg = str(e)
            if "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise ProviderError(f"Invalid OpenAI API key: {error_msg}")
            if "rate_limit" in error_msg.lower():
                raise ProviderError(f"Rate limited by OpenAI API: {error_msg}")
            raise ProviderError(f"OpenAI API error: {error_msg}")

    def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> tuple[dict[str, Any], LLMResponse]:
        """Send a completion request expecting JSON output.

        Uses OpenAI's native JSON mode for more reliable JSON output.

        Args:
            prompt: The user message/prompt
            system: Optional system message
            max_tokens: Maximum tokens in response

        Returns:
            Tuple of (parsed JSON dict, LLMResponse)

        Raises:
            ProviderError: If the API call or JSON parsing fails
        """
        client = self._get_client()

        # Add JSON instruction to system prompt
        json_system = (system or "") + "\n\nRespond with valid JSON only. No markdown, no explanation."
        json_system = json_system.strip()

        try:
            messages = []
            if json_system:
                messages.append({"role": "system", "content": json_system})
            messages.append({"role": "user", "content": prompt})

            # Note: GPT-5 models don't support temperature parameter
            response = client.chat.completions.create(
                model=self._model,
                max_completion_tokens=max_tokens,
                messages=messages,
                response_format={"type": "json_object"},  # OpenAI's native JSON mode
            )

            content = response.choices[0].message.content

            llm_response = LLMResponse(
                content=content,
                model=response.model,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
            )

            # Parse JSON from response
            content = content.strip()

            # Handle markdown code blocks (just in case)
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[-1].strip() == "```":
                    lines = lines[1:-1]
                else:
                    lines = lines[1:]
                content = "\n".join(lines)

            try:
                parsed = json.loads(content)
                return parsed, llm_response
            except json.JSONDecodeError as e:
                raise ProviderError(
                    f"Failed to parse JSON from LLM response: {e}\n"
                    f"Response content: {content[:500]}..."
                )

        except ProviderError:
            raise
        except Exception as e:
            error_msg = str(e)
            if "invalid_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise ProviderError(f"Invalid OpenAI API key: {error_msg}")
            if "rate_limit" in error_msg.lower():
                raise ProviderError(f"Rate limited by OpenAI API: {error_msg}")
            raise ProviderError(f"OpenAI API error: {error_msg}")
