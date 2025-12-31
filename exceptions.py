"""Custom exceptions for WhatsApp Unwrapped."""


class WhatsAppUnwrappedError(Exception):
    """Base exception for all WhatsApp Unwrapped errors."""

    pass


class UnsupportedFormatError(WhatsAppUnwrappedError):
    """Raised when the chat export format is not recognized."""

    pass


class ParseError(WhatsAppUnwrappedError):
    """Raised when parsing fails due to malformed content."""

    pass


# =============================================================================
# LLM Feature Exceptions
# =============================================================================


class LLMError(WhatsAppUnwrappedError):
    """Base exception for all LLM-related errors."""

    pass


class ProviderError(LLMError):
    """Raised when an LLM API call fails."""

    pass


class ChunkingError(LLMError):
    """Raised when conversation chunking fails."""

    pass


class EvidenceError(LLMError):
    """Raised when Haiku evidence extraction fails."""

    pass


class SynthesisError(LLMError):
    """Raised when Sonnet award generation fails."""

    pass
