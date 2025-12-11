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
