"""Format detection and timestamp parsing utilities."""

from datetime import datetime

from ..exceptions import UnsupportedFormatError
from ..utils.constants import TIMESTAMP_PATTERN


def is_message_start(line: str) -> bool:
    """Check if a line starts a new message (has timestamp pattern)."""
    return bool(TIMESTAMP_PATTERN.match(line))


def parse_timestamp(date_str: str, time_str: str) -> datetime:
    """Parse date and time strings into datetime.

    Args:
        date_str: Date in DD/MM/YYYY format
        time_str: Time in HH:MM format

    Returns:
        Parsed datetime object
    """
    return datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")


def parse_message_line(line: str) -> tuple[datetime, str] | None:
    """Parse a message line into timestamp and content.

    Args:
        line: A line from the chat export

    Returns:
        Tuple of (timestamp, content after " - ") or None if not a message start
    """
    match = TIMESTAMP_PATTERN.match(line)
    if not match:
        return None

    date_str, time_str, content = match.groups()
    timestamp = parse_timestamp(date_str, time_str)
    return timestamp, content


def extract_sender_and_text(content: str) -> tuple[str | None, str]:
    """Extract sender and message text from content after timestamp.

    Content format is either:
    - "Sender: message text" (regular message)
    - "message text" (system message, no sender)

    Args:
        content: The content part after "DD/MM/YYYY, HH:MM - "

    Returns:
        Tuple of (sender or None, message text)
    """
    # Check for sender pattern "Name: message"
    # Be careful: message text itself might contain colons
    colon_idx = content.find(": ")
    if colon_idx != -1:
        potential_sender = content[:colon_idx]
        # Validate it looks like a sender (no newlines, reasonable length)
        if "\n" not in potential_sender and len(potential_sender) < 100:
            return potential_sender, content[colon_idx + 2 :]

    # No sender found - this is a system message
    return None, content


def validate_format(lines: list[str]) -> None:
    """Validate that the file appears to be a WhatsApp export.

    Args:
        lines: Lines from the file

    Raises:
        UnsupportedFormatError: If format is not recognized
    """
    if not lines:
        raise UnsupportedFormatError("File is empty")

    # Check first few non-empty lines for timestamp pattern
    valid_starts = 0
    checked = 0
    for line in lines[:20]:  # Check first 20 lines
        if not line.strip():
            continue
        checked += 1
        if is_message_start(line):
            valid_starts += 1

    if checked == 0:
        raise UnsupportedFormatError("File contains no content")

    # At least 50% of checked lines should match the pattern
    if valid_starts < checked * 0.5:
        raise UnsupportedFormatError(
            f"File does not appear to be a WhatsApp export. "
            f"Expected DD/MM/YYYY, HH:MM format. "
            f"Found {valid_starts}/{checked} valid message starts."
        )
