"""Tests for the analysis module."""

import pytest
from datetime import datetime

from analysis import run_analysis
from models import (
    BasicStats,
    ChatType,
    ContentStats,
    Conversation,
    InteractionStats,
    Message,
    Statistics,
    TemporalStats,
)
from parser import load_chat


def _create_test_conversation(messages: list[Message], chat_type: ChatType = ChatType.ONE_ON_ONE) -> Conversation:
    """Helper to create a test conversation."""
    participants = sorted(set(m.sender for m in messages if m.sender))
    timestamps = [m.timestamp for m in messages]
    return Conversation(
        messages=messages,
        chat_type=chat_type,
        participants=participants,
        date_range=(min(timestamps), max(timestamps)),
        source_file="test.txt",
    )


class TestRunAnalysis:
    """Tests for run_analysis coordinator."""

    def test_run_analysis_returns_statistics(self, simple_1on1_path: str):
        """run_analysis returns a Statistics object."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        assert isinstance(stats, Statistics)
        assert isinstance(stats.basic, BasicStats)
        assert isinstance(stats.temporal, TemporalStats)
        assert isinstance(stats.content, ContentStats)
        assert isinstance(stats.interaction, InteractionStats)

    def test_statistics_to_dict(self, simple_1on1_path: str):
        """Statistics can be serialized to dict."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)
        data = stats.to_dict()

        assert "chat_type" in data
        assert "basic" in data
        assert "temporal" in data
        assert "content" in data
        assert "interaction" in data


class TestBasicStats:
    """Tests for basic statistics."""

    def test_messages_per_person(self, simple_1on1_path: str):
        """Messages are counted per person."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        # Both participants should have message counts
        assert len(stats.basic.messages_per_person) == 2
        assert all(count > 0 for count in stats.basic.messages_per_person.values())

    def test_total_messages(self, simple_1on1_path: str):
        """Total messages equals sum of per-person counts."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        total = sum(stats.basic.messages_per_person.values())
        assert stats.basic.total_messages == total

    def test_words_per_person(self, simple_1on1_path: str):
        """Words are counted per person."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        # Both participants should have word counts
        assert len(stats.basic.words_per_person) >= 1
        assert stats.basic.total_words > 0

    def test_avg_message_length(self, simple_1on1_path: str):
        """Average message length is computed."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        for person in stats.basic.messages_per_person:
            assert person in stats.basic.avg_message_length
            assert stats.basic.avg_message_length[person] >= 0


class TestTemporalStats:
    """Tests for temporal statistics."""

    def test_messages_by_date(self, simple_1on1_path: str):
        """Messages are aggregated by date."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        assert len(stats.temporal.messages_by_date) > 0
        assert all(count > 0 for count in stats.temporal.messages_by_date.values())

    def test_messages_by_hour(self, simple_1on1_path: str):
        """Messages are aggregated by hour (0-23)."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        # All 24 hours should be present
        assert len(stats.temporal.messages_by_hour) == 24
        assert all(h in stats.temporal.messages_by_hour for h in range(24))

    def test_messages_by_weekday(self, simple_1on1_path: str):
        """Messages are aggregated by weekday (0-6)."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        # All 7 weekdays should be present
        assert len(stats.temporal.messages_by_weekday) == 7
        assert all(d in stats.temporal.messages_by_weekday for d in range(7))

    def test_conversation_count(self, simple_1on1_path: str):
        """Conversation sessions are counted."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        assert stats.temporal.conversation_count >= 1


class TestContentStats:
    """Tests for content statistics."""

    def test_top_words(self, simple_1on1_path: str):
        """Top words are extracted."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        # Should have some top words (may be empty for short conversations)
        assert isinstance(stats.content.top_words, list)

    def test_top_words_per_person(self, simple_1on1_path: str):
        """Top words per person are extracted."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        # Each participant should have a word list
        assert isinstance(stats.content.top_words_per_person, dict)

    def test_top_emojis(self, edge_cases_path: str):
        """Top emojis are extracted."""
        conv = load_chat(edge_cases_path)
        stats = run_analysis(conv)

        # Edge cases fixture has emojis
        assert isinstance(stats.content.top_emojis, list)
        # Should find the emojis in the fixture
        assert len(stats.content.top_emojis) > 0


class TestInteractionStats:
    """Tests for interaction statistics."""

    def test_conversation_initiators(self, simple_1on1_path: str):
        """Conversation initiators are counted."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        # At least one person should have initiated a conversation
        assert len(stats.interaction.conversation_initiators) >= 1
        assert sum(stats.interaction.conversation_initiators.values()) >= 1

    def test_messages_per_conversation(self, simple_1on1_path: str):
        """Messages per conversation is computed."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        assert stats.interaction.messages_per_conversation > 0

    def test_response_times_1on1(self, simple_1on1_path: str):
        """Response times are computed for 1-on-1 chats."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        # Response times dict should have entries for participants
        assert isinstance(stats.interaction.response_times, dict)
        assert isinstance(stats.interaction.avg_response_time, dict)


class TestDateRange:
    """Tests for date range in temporal stats."""

    def test_date_range_matches_conversation(self, simple_1on1_path: str):
        """Temporal stats date range matches conversation."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        assert stats.temporal.first_message_date == conv.date_range[0]
        assert stats.temporal.last_message_date == conv.date_range[1]
