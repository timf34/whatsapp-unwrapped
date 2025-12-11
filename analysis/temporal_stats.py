"""Temporal statistics computation."""

from collections import Counter, defaultdict
from datetime import timedelta

from models import Conversation, Message, TemporalStats


def compute_temporal_patterns(conv: Conversation, gap_hours: float = 4.0) -> TemporalStats:
    """Compute time-based statistics.

    Args:
        conv: Parsed conversation
        gap_hours: Hours of inactivity to define a new conversation session

    Returns:
        TemporalStats with time-based patterns
    """
    messages_by_date = _aggregate_by_date(conv)
    messages_by_hour = _aggregate_by_hour(conv)
    messages_by_weekday = _aggregate_by_weekday(conv)
    messages_by_person_by_date = _aggregate_by_person_by_date(conv)
    conversation_count = _count_conversations(conv, gap_hours)

    return TemporalStats(
        messages_by_date=messages_by_date,
        messages_by_hour=messages_by_hour,
        messages_by_weekday=messages_by_weekday,
        messages_by_person_by_date=messages_by_person_by_date,
        conversation_count=conversation_count,
        first_message_date=conv.date_range[0],
        last_message_date=conv.date_range[1],
    )


def _aggregate_by_date(conv: Conversation) -> dict[str, int]:
    """Count messages per date (YYYY-MM-DD)."""
    counter: Counter[str] = Counter()
    for msg in conv.messages:
        if not msg.is_system:
            date_str = msg.timestamp.strftime("%Y-%m-%d")
            counter[date_str] += 1
    return dict(sorted(counter.items()))


def _aggregate_by_hour(conv: Conversation) -> dict[int, int]:
    """Count messages per hour (0-23)."""
    counter: Counter[int] = Counter()
    for msg in conv.messages:
        if not msg.is_system:
            counter[msg.timestamp.hour] += 1
    # Ensure all hours are present
    result = {h: counter.get(h, 0) for h in range(24)}
    return result


def _aggregate_by_weekday(conv: Conversation) -> dict[int, int]:
    """Count messages per weekday (0=Monday, 6=Sunday)."""
    counter: Counter[int] = Counter()
    for msg in conv.messages:
        if not msg.is_system:
            counter[msg.timestamp.weekday()] += 1
    # Ensure all weekdays are present
    result = {d: counter.get(d, 0) for d in range(7)}
    return result


def _aggregate_by_person_by_date(conv: Conversation) -> dict[str, dict[str, int]]:
    """Count messages per person per date."""
    result: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for msg in conv.messages:
        if msg.sender and not msg.is_system:
            date_str = msg.timestamp.strftime("%Y-%m-%d")
            result[msg.sender][date_str] += 1
    # Convert defaultdicts to regular dicts
    return {person: dict(sorted(dates.items())) for person, dates in result.items()}


def _count_conversations(conv: Conversation, gap_hours: float) -> int:
    """Count conversation sessions based on gap threshold.

    A new conversation starts when there's a gap of gap_hours or more
    between messages.
    """
    non_system_msgs = [m for m in conv.messages if not m.is_system]
    if len(non_system_msgs) < 2:
        return 1 if non_system_msgs else 0

    gap = timedelta(hours=gap_hours)
    count = 1  # First message starts a conversation

    for i in range(1, len(non_system_msgs)):
        prev_ts = non_system_msgs[i - 1].timestamp
        curr_ts = non_system_msgs[i].timestamp
        if curr_ts - prev_ts >= gap:
            count += 1

    return count


def find_conversation_starts(conv: Conversation, gap_hours: float) -> list[Message]:
    """Find messages that start new conversation sessions.

    Args:
        conv: Parsed conversation
        gap_hours: Hours of inactivity to define a new conversation session

    Returns:
        List of messages that started new conversations
    """
    non_system_msgs = [m for m in conv.messages if not m.is_system]
    if not non_system_msgs:
        return []

    gap = timedelta(hours=gap_hours)
    starters = [non_system_msgs[0]]  # First message is always a starter

    for i in range(1, len(non_system_msgs)):
        prev_ts = non_system_msgs[i - 1].timestamp
        curr_ts = non_system_msgs[i].timestamp
        if curr_ts - prev_ts >= gap:
            starters.append(non_system_msgs[i])

    return starters
