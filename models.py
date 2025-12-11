"""Data models for WhatsApp Unwrapped."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional


class ChatType(Enum):
    """Type of WhatsApp chat."""

    ONE_ON_ONE = "1-on-1"
    GROUP = "group"


@dataclass
class Message:
    """A single WhatsApp message."""

    id: int
    timestamp: datetime
    sender: Optional[str]  # None for system messages
    text: str
    is_system: bool = False
    is_media: bool = False
    is_deleted: bool = False
    has_link: bool = False
    mentions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "sender": self.sender,
            "text": self.text,
            "is_system": self.is_system,
            "is_media": self.is_media,
            "is_deleted": self.is_deleted,
            "has_link": self.has_link,
            "mentions": self.mentions,
        }


@dataclass
class Conversation:
    """Complete conversation with metadata."""

    messages: list[Message]
    chat_type: ChatType
    participants: list[str]
    date_range: tuple[datetime, datetime]
    source_file: str

    def to_dict(self) -> dict[str, Any]:
        """Convert conversation to dictionary for JSON serialization."""
        return {
            "chat_type": self.chat_type.value,
            "participants": self.participants,
            "date_range": {
                "start": self.date_range[0].isoformat(),
                "end": self.date_range[1].isoformat(),
            },
            "source_file": self.source_file,
            "message_count": len(self.messages),
            "messages": [msg.to_dict() for msg in self.messages],
        }


@dataclass
class BasicStats:
    """Basic message statistics."""

    messages_per_person: dict[str, int]
    words_per_person: dict[str, int]
    media_per_person: dict[str, int]
    total_messages: int
    total_words: int
    avg_message_length: dict[str, float]  # Average words per message

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "messages_per_person": self.messages_per_person,
            "words_per_person": self.words_per_person,
            "media_per_person": self.media_per_person,
            "total_messages": self.total_messages,
            "total_words": self.total_words,
            "avg_message_length": self.avg_message_length,
        }


@dataclass
class TemporalStats:
    """Time-based statistics."""

    messages_by_date: dict[str, int]  # YYYY-MM-DD -> count
    messages_by_hour: dict[int, int]  # 0-23 -> count
    messages_by_weekday: dict[int, int]  # 0=Monday, 6=Sunday -> count
    messages_by_person_by_date: dict[str, dict[str, int]]  # person -> date -> count
    conversation_count: int  # Number of conversation sessions
    first_message_date: datetime
    last_message_date: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "messages_by_date": self.messages_by_date,
            "messages_by_hour": self.messages_by_hour,
            "messages_by_weekday": self.messages_by_weekday,
            "messages_by_person_by_date": self.messages_by_person_by_date,
            "conversation_count": self.conversation_count,
            "first_message_date": self.first_message_date.isoformat(),
            "last_message_date": self.last_message_date.isoformat(),
        }


@dataclass
class ContentStats:
    """Content analysis statistics."""

    top_words: list[tuple[str, int]]  # (word, count) pairs
    top_words_per_person: dict[str, list[tuple[str, int]]]
    top_ngrams: dict[int, list[tuple[str, int]]]  # n -> list of (ngram, count)
    top_emojis: list[tuple[str, int]]  # (emoji, count) pairs
    top_emojis_per_person: dict[str, list[tuple[str, int]]]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "top_words": self.top_words,
            "top_words_per_person": self.top_words_per_person,
            "top_ngrams": {str(k): v for k, v in self.top_ngrams.items()},
            "top_emojis": self.top_emojis,
            "top_emojis_per_person": self.top_emojis_per_person,
        }


@dataclass
class InteractionStats:
    """Interaction pattern statistics."""

    response_times: dict[str, list[float]]  # person -> list of response times in minutes
    avg_response_time: dict[str, float]  # person -> average response time in minutes
    conversation_initiators: dict[str, int]  # person -> count of conversations started
    messages_per_conversation: float  # Average messages per conversation session

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "response_times": self.response_times,
            "avg_response_time": self.avg_response_time,
            "conversation_initiators": self.conversation_initiators,
            "messages_per_conversation": self.messages_per_conversation,
        }


@dataclass
class Statistics:
    """Complete statistics for a conversation."""

    chat_type: ChatType
    basic: BasicStats
    temporal: TemporalStats
    content: ContentStats
    interaction: InteractionStats

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "chat_type": self.chat_type.value,
            "basic": self.basic.to_dict(),
            "temporal": self.temporal.to_dict(),
            "content": self.content.to_dict(),
            "interaction": self.interaction.to_dict(),
        }


@dataclass
class OutputPaths:
    """Paths to generated output files."""

    json_file: str
    visualization_files: list[str]
