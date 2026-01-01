"""Tests for the parser module."""

import pytest

from models import ChatType
from parser import load_chat
from exceptions import ParseError, UnsupportedFormatError


class TestLoadChat:
    """Tests for load_chat function."""

    def test_load_simple_1on1(self, simple_1on1_path: str):
        """Parse a simple 1-on-1 chat."""
        conv = load_chat(simple_1on1_path)

        assert conv.chat_type == ChatType.ONE_ON_ONE
        assert len(conv.participants) == 2
        assert "Tim Farrelly" in conv.participants
        assert "Vita" in conv.participants
        # 10 lines total, 1 is system message, 2 are media
        assert len(conv.messages) == 10

    def test_load_detects_1on1_type(self, simple_1on1_path: str):
        """Auto-detect 1-on-1 chat type."""
        conv = load_chat(simple_1on1_path)
        assert conv.chat_type == ChatType.ONE_ON_ONE

    def test_load_with_explicit_type(self, simple_1on1_path: str):
        """Override chat type detection."""
        conv = load_chat(simple_1on1_path, explicit_type="group")
        assert conv.chat_type == ChatType.GROUP

    def test_file_not_found_raises(self):
        """Missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_chat("/nonexistent/path/chat.txt")

    def test_invalid_format_raises(self, tmp_path):
        """Invalid format raises UnsupportedFormatError."""
        bad_file = tmp_path / "bad.txt"
        bad_file.write_text("This is not a WhatsApp export\nJust some random text")

        with pytest.raises(UnsupportedFormatError):
            load_chat(str(bad_file))

    def test_empty_file_raises(self, tmp_path):
        """Empty file raises UnsupportedFormatError."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        with pytest.raises(UnsupportedFormatError):
            load_chat(str(empty_file))


class TestMultilineMessages:
    """Tests for multi-line message handling."""

    def test_multiline_messages_joined(self, multiline_path: str):
        """Messages spanning multiple lines are joined correctly."""
        conv = load_chat(multiline_path)

        # First message should span multiple lines
        first_msg = conv.messages[0]
        assert "To let you know my plan" in first_msg.text
        assert "Tmrw I have the run club" in first_msg.text
        assert "\n" in first_msg.text  # Should contain newlines


class TestSystemMessages:
    """Tests for system message detection."""

    def test_system_messages_detected(self, system_messages_path: str):
        """System messages are marked correctly."""
        conv = load_chat(system_messages_path)

        system_msgs = [m for m in conv.messages if m.is_system]
        # Encryption notice, group creation, add, left
        assert len(system_msgs) >= 4

        # Encryption notice should be system
        encryption_msg = conv.messages[0]
        assert encryption_msg.is_system
        assert encryption_msg.sender is None

    def test_group_detected_with_3_participants(self, system_messages_path: str):
        """Chat with 3+ participants detected as group."""
        conv = load_chat(system_messages_path)
        assert conv.chat_type == ChatType.GROUP
        assert len(conv.participants) >= 2


class TestEdgeCases:
    """Tests for edge cases: media, links, deleted messages."""

    def test_media_detected(self, edge_cases_path: str):
        """Media messages are marked correctly."""
        conv = load_chat(edge_cases_path)

        media_msgs = [m for m in conv.messages if m.is_media]
        assert len(media_msgs) == 1
        assert media_msgs[0].text == "<Media omitted>"

    def test_links_detected(self, edge_cases_path: str):
        """Messages with URLs have has_link=True."""
        conv = load_chat(edge_cases_path)

        link_msgs = [m for m in conv.messages if m.has_link]
        assert len(link_msgs) == 2

    def test_deleted_messages_detected(self, edge_cases_path: str):
        """Deleted messages are marked correctly."""
        conv = load_chat(edge_cases_path)

        deleted_msgs = [m for m in conv.messages if m.is_deleted]
        assert len(deleted_msgs) == 2

        # Check both patterns work
        texts = [m.text for m in deleted_msgs]
        assert "You deleted this message" in texts
        assert "This message was deleted" in texts


class TestDateRange:
    """Tests for date range computation."""

    def test_date_range_computed(self, simple_1on1_path: str):
        """Date range is computed from messages."""
        conv = load_chat(simple_1on1_path)

        start, end = conv.date_range
        assert start.year == 2024
        assert start.month == 10
        assert start.day == 10
        assert end.day == 19  # Last message is on 19th


class TestToDict:
    """Tests for serialization."""

    def test_conversation_to_dict(self, simple_1on1_path: str):
        """Conversation can be serialized to dict."""
        conv = load_chat(simple_1on1_path)
        data = conv.to_dict()

        assert data["chat_type"] == "1-on-1"
        assert len(data["participants"]) == 2
        assert "messages" in data
        assert data["message_count"] == len(conv.messages)

    def test_message_to_dict(self, simple_1on1_path: str):
        """Messages can be serialized to dict."""
        conv = load_chat(simple_1on1_path)
        msg_data = conv.messages[1].to_dict()

        assert "id" in msg_data
        assert "timestamp" in msg_data
        assert "sender" in msg_data
        assert "text" in msg_data
