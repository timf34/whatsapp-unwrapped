"""Conversation chunking for LLM processing."""

from dataclasses import dataclass, field
from datetime import datetime

from models import Conversation, Message


# Token estimation: ~4 characters per token (conservative)
CHARS_PER_TOKEN = 4

# Default chunk settings
DEFAULT_TARGET_TOKENS = 8000
DEFAULT_OVERLAP_TOKENS = 200


@dataclass
class ConversationChunk:
    """A chunk of conversation for LLM processing."""

    messages: list[Message]
    start_idx: int
    end_idx: int
    token_estimate: int
    formatted_text: str = field(default="", repr=False)

    @property
    def message_count(self) -> int:
        """Number of messages in this chunk."""
        return len(self.messages)

    @property
    def date_range(self) -> tuple[datetime, datetime]:
        """Date range covered by this chunk."""
        if not self.messages:
            raise ValueError("Empty chunk has no date range")
        return (self.messages[0].timestamp, self.messages[-1].timestamp)


def chunk_conversation(
    conversation: Conversation,
    target_tokens: int = DEFAULT_TARGET_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[ConversationChunk]:
    """Split conversation into chunks for LLM processing.

    Args:
        conversation: Full conversation to chunk
        target_tokens: Target tokens per chunk (default 8000)
        overlap_tokens: Overlap between chunks for context (default 200)

    Returns:
        List of ConversationChunk objects
    """
    # Filter to user messages only
    messages = [m for m in conversation.messages if not m.is_system and m.sender]

    if not messages:
        return []

    # Estimate total tokens
    total_text = _format_messages(messages)
    total_tokens = _estimate_tokens(total_text)

    # If small enough, return single chunk
    if total_tokens <= target_tokens:
        return [
            ConversationChunk(
                messages=messages,
                start_idx=0,
                end_idx=len(messages) - 1,
                token_estimate=total_tokens,
                formatted_text=total_text,
            )
        ]

    # Split into multiple chunks
    chunks = []
    current_start = 0
    overlap_chars = overlap_tokens * CHARS_PER_TOKEN

    while current_start < len(messages):
        # Find end of this chunk
        current_messages = []
        current_text = ""
        current_end = current_start

        for i in range(current_start, len(messages)):
            msg = messages[i]
            msg_text = _format_single_message(msg)
            new_text = current_text + msg_text

            if _estimate_tokens(new_text) > target_tokens and current_messages:
                # Would exceed target, stop here
                break

            current_messages.append(msg)
            current_text = new_text
            current_end = i

        if not current_messages:
            # Single message exceeds target, include it anyway
            current_messages = [messages[current_start]]
            current_text = _format_single_message(messages[current_start])
            current_end = current_start

        chunks.append(
            ConversationChunk(
                messages=current_messages,
                start_idx=current_start,
                end_idx=current_end,
                token_estimate=_estimate_tokens(current_text),
                formatted_text=current_text,
            )
        )

        # Move to next chunk, with overlap
        # Find where to start next chunk to get overlap
        next_start = current_end + 1
        if next_start < len(messages) and overlap_tokens > 0:
            # Back up to create overlap
            overlap_text = ""
            for i in range(current_end, current_start - 1, -1):
                msg_text = _format_single_message(messages[i])
                if _estimate_tokens(overlap_text + msg_text) > overlap_tokens:
                    break
                overlap_text = msg_text + overlap_text
                next_start = i

        current_start = next_start

        # Safety check to prevent infinite loop
        if current_start <= chunks[-1].start_idx:
            current_start = chunks[-1].end_idx + 1

    return chunks


def _format_messages(messages: list[Message]) -> str:
    """Format a list of messages for LLM input."""
    return "\n".join(_format_single_message(m) for m in messages)


def _format_single_message(message: Message) -> str:
    """Format a single message for LLM input."""
    timestamp = message.timestamp.strftime("%Y-%m-%d %H:%M")
    sender = message.sender or "System"
    text = message.text

    # Truncate very long messages
    if len(text) > 500:
        text = text[:500] + "..."

    return f"[{timestamp}] {sender}: {text}\n"


def _estimate_tokens(text: str) -> int:
    """Estimate token count for text."""
    return len(text) // CHARS_PER_TOKEN
