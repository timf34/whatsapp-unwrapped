"""Basic statistics computation."""

from collections import Counter

from models import BasicStats, Conversation, Message


def compute_basic_stats(conv: Conversation) -> BasicStats:
    """Compute basic message statistics.

    Args:
        conv: Parsed conversation

    Returns:
        BasicStats with message counts, word counts, and averages
    """
    messages_per_person = _count_messages_per_person(conv)
    words_per_person = _count_words_per_person(conv)
    media_per_person = _count_media_per_person(conv)
    avg_message_length = _compute_avg_message_length(messages_per_person, words_per_person)
    
    # New stats
    links_per_person = _count_links_per_person(conv)
    deleted_per_person = _count_deleted_per_person(conv)
    media_count = sum(media_per_person.values())
    deleted_count = sum(deleted_per_person.values())
    link_count = sum(links_per_person.values())
    
    media_ratio_per_person = _compute_media_ratio(messages_per_person, media_per_person)
    link_ratio_per_person = _compute_link_ratio(messages_per_person, links_per_person)

    return BasicStats(
        messages_per_person=messages_per_person,
        words_per_person=words_per_person,
        media_per_person=media_per_person,
        total_messages=sum(messages_per_person.values()),
        total_words=sum(words_per_person.values()),
        avg_message_length=avg_message_length,
        media_count=media_count,
        deleted_count=deleted_count,
        link_count=link_count,
        links_per_person=links_per_person,
        deleted_per_person=deleted_per_person,
        media_ratio_per_person=media_ratio_per_person,
        link_ratio_per_person=link_ratio_per_person,
    )


def _count_messages_per_person(conv: Conversation) -> dict[str, int]:
    """Count messages for each participant."""
    counter: Counter[str] = Counter()
    for msg in conv.messages:
        if msg.sender and not msg.is_system:
            counter[msg.sender] += 1
    return dict(counter)


def _count_words_per_person(conv: Conversation) -> dict[str, int]:
    """Count words for each participant."""
    counter: Counter[str] = Counter()
    for msg in conv.messages:
        if msg.sender and not msg.is_system and not msg.is_media:
            word_count = _count_words(msg.text)
            counter[msg.sender] += word_count
    return dict(counter)


def _count_words(text: str) -> int:
    """Count words in text, excluding empty strings."""
    words = text.split()
    return len(words)


def _count_media_per_person(conv: Conversation) -> dict[str, int]:
    """Count media messages for each participant."""
    counter: Counter[str] = Counter()
    for msg in conv.messages:
        if msg.sender and msg.is_media:
            counter[msg.sender] += 1
    return dict(counter)


def _compute_avg_message_length(
    messages_per_person: dict[str, int], words_per_person: dict[str, int]
) -> dict[str, float]:
    """Compute average words per message for each participant."""
    result: dict[str, float] = {}
    for person in messages_per_person:
        msg_count = messages_per_person.get(person, 0)
        word_count = words_per_person.get(person, 0)
        if msg_count > 0:
            result[person] = round(word_count / msg_count, 2)
        else:
            result[person] = 0.0
    return result


def _count_links_per_person(conv: Conversation) -> dict[str, int]:
    """Count messages with links for each participant."""
    counter: Counter[str] = Counter()
    for msg in conv.messages:
        if msg.sender and msg.has_link:
            counter[msg.sender] += 1
    return dict(counter)


def _count_deleted_per_person(conv: Conversation) -> dict[str, int]:
    """Count deleted messages for each participant."""
    counter: Counter[str] = Counter()
    for msg in conv.messages:
        if msg.sender and msg.is_deleted:
            counter[msg.sender] += 1
    return dict(counter)


def _compute_media_ratio(
    messages_per_person: dict[str, int], media_per_person: dict[str, int]
) -> dict[str, float]:
    """Compute ratio of media messages to total messages for each participant."""
    result: dict[str, float] = {}
    for person in messages_per_person:
        msg_count = messages_per_person.get(person, 0)
        media_count = media_per_person.get(person, 0)
        if msg_count > 0:
            result[person] = round(media_count / msg_count, 4)
        else:
            result[person] = 0.0
    return result


def _compute_link_ratio(
    messages_per_person: dict[str, int], links_per_person: dict[str, int]
) -> dict[str, float]:
    """Compute ratio of link messages to total messages for each participant."""
    result: dict[str, float] = {}
    for person in messages_per_person:
        msg_count = messages_per_person.get(person, 0)
        link_count = links_per_person.get(person, 0)
        if msg_count > 0:
            result[person] = round(link_count / msg_count, 4)
        else:
            result[person] = 0.0
    return result
