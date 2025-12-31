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
    media_count: int
    deleted_count: int
    link_count: int
    links_per_person: dict[str, int]
    deleted_per_person: dict[str, int]
    media_ratio_per_person: dict[str, float]  # Media messages / total messages
    link_ratio_per_person: dict[str, float]  # Link messages / total messages

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "messages_per_person": self.messages_per_person,
            "words_per_person": self.words_per_person,
            "media_per_person": self.media_per_person,
            "total_messages": self.total_messages,
            "total_words": self.total_words,
            "avg_message_length": self.avg_message_length,
            "media_count": self.media_count,
            "deleted_count": self.deleted_count,
            "link_count": self.link_count,
            "links_per_person": self.links_per_person,
            "deleted_per_person": self.deleted_per_person,
            "media_ratio_per_person": self.media_ratio_per_person,
            "link_ratio_per_person": self.link_ratio_per_person,
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
    days_active: int
    avg_messages_per_day: float  # total / total_days
    avg_messages_per_active_day: float  # total / days_active
    longest_streak_days: int
    longest_gap_days: int
    most_active_date: Optional[str]  # YYYY-MM-DD
    busiest_hour: Optional[int]  # 0-23

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
            "days_active": self.days_active,
            "avg_messages_per_day": self.avg_messages_per_day,
            "avg_messages_per_active_day": self.avg_messages_per_active_day,
            "longest_streak_days": self.longest_streak_days,
            "longest_gap_days": self.longest_gap_days,
            "most_active_date": self.most_active_date,
            "busiest_hour": self.busiest_hour,
        }


@dataclass
class ContentStats:
    """Content analysis statistics."""

    top_words: list[tuple[str, int]]  # (word, count) pairs
    top_words_per_person: dict[str, list[tuple[str, int]]]
    top_ngrams: dict[int, list[tuple[str, int]]]  # n -> list of (ngram, count)
    top_emojis: list[tuple[str, int]]  # (emoji, count) pairs
    top_emojis_per_person: dict[str, list[tuple[str, int]]]
    longest_messages: list[dict[str, Any]]  # top N by word count

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "top_words": self.top_words,
            "top_words_per_person": self.top_words_per_person,
            "top_ngrams": {str(k): v for k, v in self.top_ngrams.items()},
            "top_emojis": self.top_emojis,
            "top_emojis_per_person": self.top_emojis_per_person,
            "longest_messages": self.longest_messages,
        }


@dataclass
class InteractionStats:
    """Interaction pattern statistics."""

    response_times: dict[str, list[float]]  # person -> list of response times in minutes
    avg_response_time: dict[str, float]  # person -> average response time in minutes
    conversation_initiators: dict[str, int]  # person -> count of conversations started
    messages_per_conversation: float  # Average messages per conversation session
    response_time_buckets: dict[str, dict[str, int]]  # person -> bucket -> count

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "response_times": self.response_times,
            "avg_response_time": self.avg_response_time,
            "conversation_initiators": self.conversation_initiators,
            "messages_per_conversation": self.messages_per_conversation,
            "response_time_buckets": self.response_time_buckets,
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


# =============================================================================
# LLM Feature Models (Unwrapped)
# =============================================================================


@dataclass
class DetectedPattern:
    """A behavioral pattern found via Python analysis."""

    pattern_type: str  # e.g., "late_good_morning", "triple_texter"
    person: str  # Who exhibits this pattern
    frequency: int  # How often it occurs
    evidence: list[dict[str, Any]]  # Sample messages proving it
    strength: float  # 0-1, how distinctive/notable
    description: str  # Human-readable description for LLM

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "pattern_type": self.pattern_type,
            "person": self.person,
            "frequency": self.frequency,
            "evidence": self.evidence,
            "strength": self.strength,
            "description": self.description,
        }


@dataclass
class EvidencePacket:
    """Qualitative evidence from Haiku analysis of a chunk."""

    notable_quotes: list[dict[str, Any]]  # {"person", "quote", "why_notable"}
    inside_jokes: list[dict[str, Any]]  # {"reference", "context", "frequency_hint"}
    dynamics: list[str]  # Short observations about interaction
    funny_moments: list[dict[str, Any]]  # {"description", "evidence"}
    style_notes: dict[str, list[str]]  # {person: [observations]}
    award_ideas: list[dict[str, Any]]  # {"title", "recipient", "evidence"}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "notable_quotes": self.notable_quotes,
            "inside_jokes": self.inside_jokes,
            "dynamics": self.dynamics,
            "funny_moments": self.funny_moments,
            "style_notes": self.style_notes,
            "award_ideas": self.award_ideas,
        }


@dataclass
class ConversationEvidence:
    """Aggregated evidence from all chunks."""

    notable_quotes: list[dict[str, Any]]
    inside_jokes: list[dict[str, Any]]
    dynamics: list[str]
    funny_moments: list[dict[str, Any]]
    style_notes: dict[str, list[str]]
    award_ideas: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "notable_quotes": self.notable_quotes,
            "inside_jokes": self.inside_jokes,
            "dynamics": self.dynamics,
            "funny_moments": self.funny_moments,
            "style_notes": self.style_notes,
            "award_ideas": self.award_ideas,
        }


@dataclass
class Award:
    """A single generated award."""

    title: str  # Funny, specific award name (3-8 words)
    recipient: str  # Which person wins this
    evidence: str  # The specific data point that proves it
    quip: str  # One sentence that makes it funny (max 15 words)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.title,
            "recipient": self.recipient,
            "evidence": self.evidence,
            "quip": self.quip,
        }


@dataclass
class UnwrappedResult:
    """Complete result from the unwrapped generation."""

    awards: list[Award]
    patterns_used: list[DetectedPattern]
    evidence: Optional[ConversationEvidence]  # Qualitative insights from Haiku
    model_used: str  # "offline", "haiku+sonnet", etc.
    input_tokens: int
    output_tokens: int
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "awards": [a.to_dict() for a in self.awards],
            "patterns_used": [p.to_dict() for p in self.patterns_used],
            "evidence": self.evidence.to_dict() if self.evidence else None,
            "model_used": self.model_used,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "success": self.success,
            "error": self.error,
        }
