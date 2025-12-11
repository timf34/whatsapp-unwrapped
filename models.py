"""Data models for WhatsApp Unwrapped."""

from dataclasses import dataclass, field
from datetime import datetime
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
