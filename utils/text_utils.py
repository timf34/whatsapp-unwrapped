"""Text processing utilities."""

from .constants import (
    DELETED_MESSAGE_PATTERNS,
    MEDIA_PLACEHOLDER,
    MENTION_PATTERN,
    SYSTEM_MESSAGE_PATTERNS,
    URL_PATTERN,
)


def is_system_message(text: str) -> bool:
    """Check if text matches a known system message pattern."""
    for pattern in SYSTEM_MESSAGE_PATTERNS:
        if pattern.search(text):
            return True
    return False


def is_deleted_message(text: str) -> bool:
    """Check if text indicates a deleted message."""
    for pattern in DELETED_MESSAGE_PATTERNS:
        if pattern.match(text):
            return True
    return False


def is_media_placeholder(text: str) -> bool:
    """Check if text is a media placeholder."""
    return text.strip() == MEDIA_PLACEHOLDER


def detect_links(text: str) -> bool:
    """Check if text contains any URLs."""
    return bool(URL_PATTERN.search(text))


def extract_mentions(text: str) -> list[str]:
    """Extract @mentions from text.

    Handles WhatsApp's Unicode directional isolates around mention names.
    """
    matches = MENTION_PATTERN.findall(text)
    return [m.strip() for m in matches if m.strip()]
