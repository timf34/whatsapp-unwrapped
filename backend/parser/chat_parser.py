"""Main chat parsing logic."""

from pathlib import Path
from typing import Optional

from exceptions import ParseError
from models import ChatType, Conversation, Message
from utils.text_utils import (
    detect_links,
    extract_mentions,
    is_deleted_message,
    is_media_placeholder,
    is_system_message,
)
from parser.format_utils import (
    extract_sender_and_text,
    is_message_start,
    parse_message_line,
    validate_format,
)


def load_chat(filepath: str, explicit_type: Optional[str] = None) -> Conversation:
    """Load and parse a WhatsApp chat export.

    Args:
        filepath: Path to the .txt export file
        explicit_type: Override auto-detection ("1-on-1" or "group")

    Returns:
        Parsed Conversation object

    Raises:
        FileNotFoundError: If file doesn't exist
        UnsupportedFormatError: If format is not recognized
        ParseError: If file is malformed
    """
    lines = _read_file(filepath)
    validate_format(lines)
    messages = _parse_messages(lines)

    if not messages:
        raise ParseError("No messages found in file")

    if explicit_type:
        chat_type = ChatType(explicit_type)
    else:
        chat_type = _detect_chat_type(messages)

    return _build_conversation(messages, chat_type, filepath)


def _read_file(filepath: str) -> list[str]:
    """Read file and return lines.

    Handles UTF-8 and UTF-8-BOM encodings.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Try UTF-8-BOM first (common in Windows exports), then UTF-8
    for encoding in ["utf-8-sig", "utf-8"]:
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.readlines()
        except UnicodeDecodeError:
            continue

    # If both fail, try with errors='replace'
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()


def _parse_messages(lines: list[str]) -> list[Message]:
    """Parse all lines into Message objects.

    Handles multi-line messages by accumulating continuation lines.
    """
    messages: list[Message] = []
    current_timestamp = None
    current_sender: Optional[str] = None
    current_text_lines: list[str] = []
    message_id = 0

    def finalize_message():
        """Create message from accumulated data."""
        nonlocal message_id
        if current_timestamp is None:
            return

        text = "\n".join(current_text_lines).strip()
        if not text:
            return

        # Determine message flags
        is_system = current_sender is None or is_system_message(text)
        is_media = is_media_placeholder(text)
        is_deleted = is_deleted_message(text)
        has_link = detect_links(text)
        mentions = extract_mentions(text)

        messages.append(
            Message(
                id=message_id,
                timestamp=current_timestamp,
                sender=current_sender,
                text=text,
                is_system=is_system,
                is_media=is_media,
                is_deleted=is_deleted,
                has_link=has_link,
                mentions=mentions,
            )
        )
        message_id += 1

    for line in lines:
        line = line.rstrip("\n\r")

        if is_message_start(line):
            # Finalize previous message
            finalize_message()

            # Start new message
            result = parse_message_line(line)
            if result:
                timestamp, content = result
                sender, text = extract_sender_and_text(content)
                current_timestamp = timestamp
                current_sender = sender
                current_text_lines = [text]
        else:
            # Continuation line for multi-line message
            if current_timestamp is not None:
                current_text_lines.append(line)

    # Don't forget the last message
    finalize_message()

    return messages


def _detect_chat_type(messages: list[Message]) -> ChatType:
    """Detect chat type based on unique sender count.

    - 2 unique senders -> ONE_ON_ONE
    - 3+ unique senders -> GROUP
    - 1 unique sender -> GROUP (edge case: you're the only one talking)
    """
    senders = set()
    for msg in messages:
        if msg.sender is not None and not msg.is_system:
            senders.add(msg.sender)

    if len(senders) == 2:
        return ChatType.ONE_ON_ONE
    return ChatType.GROUP


def _build_conversation(
    messages: list[Message], chat_type: ChatType, filepath: str
) -> Conversation:
    """Build Conversation object from parsed messages."""
    # Extract unique participants (non-system message senders)
    participants = sorted(
        set(msg.sender for msg in messages if msg.sender and not msg.is_system)
    )

    # Compute date range
    timestamps = [msg.timestamp for msg in messages]
    date_range = (min(timestamps), max(timestamps))

    return Conversation(
        messages=messages,
        chat_type=chat_type,
        participants=participants,
        date_range=date_range,
        source_file=filepath,
    )
