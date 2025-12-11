"""Interaction pattern statistics."""

from collections import Counter, defaultdict
from datetime import timedelta

from models import ChatType, Conversation, InteractionStats
from analysis.temporal_stats import find_conversation_starts


def compute_interaction_patterns(conv: Conversation, gap_hours: float = 4.0) -> InteractionStats:
    """Analyze interaction patterns.

    Args:
        conv: Parsed conversation
        gap_hours: Hours of inactivity to define a new conversation session

    Returns:
        InteractionStats with response times and interaction patterns
    """
    response_times = _calculate_response_times(conv, gap_hours)
    avg_response_time = _compute_avg_response_times(response_times)
    conversation_initiators = _count_initiators(conv, gap_hours)
    messages_per_conversation = _compute_messages_per_conversation(conv, gap_hours)

    return InteractionStats(
        response_times=response_times,
        avg_response_time=avg_response_time,
        conversation_initiators=conversation_initiators,
        messages_per_conversation=messages_per_conversation,
    )


def _calculate_response_times(
    conv: Conversation, gap_hours: float
) -> dict[str, list[float]]:
    """Calculate response times for each participant.

    For 1-on-1 chats: Time between person A's message and person B's response.
    For groups: Not computed (returns empty dict).

    Response times are in minutes.
    """
    # Only calculate for 1-on-1 chats
    if conv.chat_type != ChatType.ONE_ON_ONE:
        return {p: [] for p in conv.participants}

    gap = timedelta(hours=gap_hours)
    result: dict[str, list[float]] = defaultdict(list)
    non_system_msgs = [m for m in conv.messages if not m.is_system and m.sender]

    for i in range(1, len(non_system_msgs)):
        prev_msg = non_system_msgs[i - 1]
        curr_msg = non_system_msgs[i]

        # Skip if same sender or if it's a new conversation
        if prev_msg.sender == curr_msg.sender:
            continue
        if curr_msg.timestamp - prev_msg.timestamp >= gap:
            continue

        # Calculate response time in minutes
        delta = curr_msg.timestamp - prev_msg.timestamp
        minutes = delta.total_seconds() / 60

        # Only count reasonable response times (< 24 hours)
        if 0 < minutes < 1440:
            result[curr_msg.sender].append(round(minutes, 2))

    return dict(result)


def _compute_avg_response_times(response_times: dict[str, list[float]]) -> dict[str, float]:
    """Compute average response time for each participant."""
    result: dict[str, float] = {}
    for person, times in response_times.items():
        if times:
            result[person] = round(sum(times) / len(times), 2)
        else:
            result[person] = 0.0
    return result


def _count_initiators(conv: Conversation, gap_hours: float) -> dict[str, int]:
    """Count how often each participant starts a conversation."""
    starters = find_conversation_starts(conv, gap_hours)
    counter: Counter[str] = Counter()
    for msg in starters:
        if msg.sender:
            counter[msg.sender] += 1
    return dict(counter)


def _compute_messages_per_conversation(conv: Conversation, gap_hours: float) -> float:
    """Compute average messages per conversation session."""
    gap = timedelta(hours=gap_hours)
    non_system_msgs = [m for m in conv.messages if not m.is_system]

    if not non_system_msgs:
        return 0.0

    conversation_count = 1
    for i in range(1, len(non_system_msgs)):
        prev_ts = non_system_msgs[i - 1].timestamp
        curr_ts = non_system_msgs[i].timestamp
        if curr_ts - prev_ts >= gap:
            conversation_count += 1

    return round(len(non_system_msgs) / conversation_count, 2)
