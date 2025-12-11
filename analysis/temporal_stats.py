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
    
    # Compute new stats
    days_active = len(messages_by_date)
    total_days = (conv.date_range[1] - conv.date_range[0]).days + 1
    non_system_count = sum(1 for m in conv.messages if not m.is_system)
    
    avg_messages_per_day = round(non_system_count / total_days, 2) if total_days > 0 else 0.0
    avg_messages_per_active_day = round(non_system_count / days_active, 2) if days_active > 0 else 0.0
    
    longest_streak_days = _compute_longest_streak(messages_by_date)
    longest_gap_days = _compute_longest_gap(messages_by_date, conv.date_range)
    most_active_date = max(messages_by_date, key=messages_by_date.get) if messages_by_date else None
    busiest_hour = max(messages_by_hour, key=messages_by_hour.get) if messages_by_hour else None

    return TemporalStats(
        messages_by_date=messages_by_date,
        messages_by_hour=messages_by_hour,
        messages_by_weekday=messages_by_weekday,
        messages_by_person_by_date=messages_by_person_by_date,
        conversation_count=conversation_count,
        first_message_date=conv.date_range[0],
        last_message_date=conv.date_range[1],
        days_active=days_active,
        avg_messages_per_day=avg_messages_per_day,
        avg_messages_per_active_day=avg_messages_per_active_day,
        longest_streak_days=longest_streak_days,
        longest_gap_days=longest_gap_days,
        most_active_date=most_active_date,
        busiest_hour=busiest_hour,
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


def _compute_longest_streak(messages_by_date: dict[str, int]) -> int:
    """Compute longest streak of consecutive days with messages.
    
    Args:
        messages_by_date: Dict mapping YYYY-MM-DD strings to message counts
        
    Returns:
        Longest streak in days
    """
    if not messages_by_date:
        return 0
        
    from datetime import datetime
    
    dates = sorted(messages_by_date.keys())
    if not dates:
        return 0
    
    max_streak = 1
    current_streak = 1
    
    for i in range(1, len(dates)):
        prev_date = datetime.strptime(dates[i-1], "%Y-%m-%d")
        curr_date = datetime.strptime(dates[i], "%Y-%m-%d")
        
        # Check if consecutive days
        if (curr_date - prev_date).days == 1:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    
    return max_streak


def _compute_longest_gap(messages_by_date: dict[str, int], date_range: tuple) -> int:
    """Compute longest gap between messages in days.
    
    Args:
        messages_by_date: Dict mapping YYYY-MM-DD strings to message counts
        date_range: Tuple of (first_date, last_date)
        
    Returns:
        Longest gap in days
    """
    if not messages_by_date or len(messages_by_date) < 2:
        return 0
    
    from datetime import datetime
    
    dates = sorted(messages_by_date.keys())
    max_gap = 0
    
    for i in range(1, len(dates)):
        prev_date = datetime.strptime(dates[i-1], "%Y-%m-%d")
        curr_date = datetime.strptime(dates[i], "%Y-%m-%d")
        
        gap = (curr_date - prev_date).days - 1  # -1 because consecutive days = 0 gap
        max_gap = max(max_gap, gap)
    
    return max_gap
