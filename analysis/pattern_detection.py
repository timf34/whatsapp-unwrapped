"""Pattern detection for LLM-powered Unwrapped feature.

Detects behavioral patterns in conversations using pure Python analysis.
These patterns serve as "anchors" for LLM-generated awards.
"""

import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Optional

from models import Conversation, DetectedPattern, Message, Statistics


# =============================================================================
# Configuration
# =============================================================================

# Minimum occurrences for a pattern to be considered
MIN_PATTERN_FREQUENCY = 3

# Minimum strength for a pattern to be included
MIN_PATTERN_STRENGTH = 0.3

# Time thresholds
LATE_MORNING_HOUR = 11  # "Good morning" after this hour is late
LATE_NIGHT_HOUR = 2  # "Goodnight" after this hour is late
MIDNIGHT_PHILOSOPHER_HOUR = 1  # Deep conversations start after this

# Common words to exclude from catchphrase detection
COMMON_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
    "from", "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "and", "but", "if", "or",
    "because", "until", "while", "although", "though", "after", "before",
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you",
    "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself",
    "she", "her", "hers", "herself", "it", "its", "itself", "they", "them",
    "their", "theirs", "themselves", "what", "which", "who", "whom", "this",
    "that", "these", "those", "am", "im", "ive", "dont", "didnt", "cant",
    "wont", "isnt", "arent", "wasnt", "werent", "hasnt", "havent", "hadnt",
    "doesnt", "didnt", "wont", "wouldnt", "couldnt", "shouldnt", "mightnt",
    "mustnt", "yeah", "yes", "no", "ok", "okay", "like", "got", "get",
    "know", "think", "want", "going", "go", "see", "come", "take", "make",
    "good", "well", "back", "now", "way", "even", "new", "also", "day",
    "time", "really", "much", "right", "still", "thing", "things",
}

# Phrases to exclude (system messages, placeholders)
EXCLUDED_PHRASES = {
    "media omitted",
    "image omitted",
    "video omitted",
    "audio omitted",
    "sticker omitted",
    "document omitted",
    "gif omitted",
    "contact card omitted",
    "location omitted",
    "this message was deleted",
    "you deleted this message",
    "message deleted",
}


# =============================================================================
# Main Entry Point
# =============================================================================


def detect_all_patterns(
    conversation: Conversation,
    stats: Statistics,
) -> list[DetectedPattern]:
    """Detect all behavioral patterns in the conversation.

    Args:
        conversation: Parsed conversation
        stats: Pre-computed statistics

    Returns:
        List of detected patterns, sorted by strength descending
    """
    patterns: list[DetectedPattern] = []

    # Get user messages only (exclude system messages)
    user_messages = [m for m in conversation.messages if not m.is_system and m.sender]

    if len(user_messages) < 10:
        return []  # Not enough data for meaningful patterns

    # Timing patterns
    if pattern := _detect_late_good_morning(user_messages):
        patterns.append(pattern)
    if pattern := _detect_late_goodnight(user_messages):
        patterns.append(pattern)
    patterns.extend(_detect_midnight_philosopher(user_messages))

    # Phrase patterns
    patterns.extend(_detect_catchphrase(user_messages).values())
    patterns.extend(_detect_laugh_style(user_messages).values())
    if pattern := _detect_apology_patterns(user_messages):
        patterns.append(pattern)

    # Punctuation and emoji patterns
    patterns.extend(_detect_punctuation_habits(user_messages).values())
    patterns.extend(_detect_emoji_signature(user_messages, stats).values())

    # Texting style patterns
    patterns.extend(_detect_triple_texter(user_messages).values())
    patterns.extend(_detect_message_length_style(user_messages, stats).values())

    # Interaction patterns
    if pattern := _detect_initiator_imbalance(conversation, stats):
        patterns.append(pattern)
    patterns.extend(_detect_question_asker(user_messages).values())

    # Filter by strength and sort
    patterns = [p for p in patterns if p.strength >= MIN_PATTERN_STRENGTH]
    patterns.sort(key=lambda p: p.strength, reverse=True)

    return patterns


# =============================================================================
# Timing Pattern Detectors
# =============================================================================


def _detect_late_good_morning(messages: list[Message]) -> Optional[DetectedPattern]:
    """Detect who says 'good morning' late in the day."""
    morning_pattern = re.compile(r"\b(good\s*morning|gm|morning)\b", re.IGNORECASE)

    late_mornings: dict[str, list[Message]] = defaultdict(list)

    for msg in messages:
        if morning_pattern.search(msg.text):
            hour = msg.timestamp.hour
            if hour >= LATE_MORNING_HOUR:
                late_mornings[msg.sender].append(msg)

    if not late_mornings:
        return None

    # Find the person with the most late mornings
    top_person = max(late_mornings.keys(), key=lambda p: len(late_mornings[p]))
    late_msgs = late_mornings[top_person]

    if len(late_msgs) < MIN_PATTERN_FREQUENCY:
        return None

    # Find the latest one
    latest = max(late_msgs, key=lambda m: m.timestamp.hour * 60 + m.timestamp.minute)
    latest_time = latest.timestamp.strftime("%I:%M %p")

    # Calculate strength based on frequency
    strength = min(1.0, len(late_msgs) / 15)

    evidence = [
        {
            "timestamp": m.timestamp.isoformat(),
            "time": m.timestamp.strftime("%I:%M %p"),
            "text": m.text[:100],
        }
        for m in late_msgs[:5]
    ]

    return DetectedPattern(
        pattern_type="late_good_morning",
        person=top_person,
        frequency=len(late_msgs),
        evidence=evidence,
        strength=strength,
        description=f"Said 'good morning' after {LATE_MORNING_HOUR}am {len(late_msgs)} times. Latest: {latest_time}",
    )


def _detect_late_goodnight(messages: list[Message]) -> Optional[DetectedPattern]:
    """Detect who says 'goodnight' very late (after 2am)."""
    night_pattern = re.compile(r"\b(good\s*night|gn|night|nighty?\s*night)\b", re.IGNORECASE)

    late_nights: dict[str, list[Message]] = defaultdict(list)

    for msg in messages:
        if night_pattern.search(msg.text):
            hour = msg.timestamp.hour
            # After midnight but before ~5am
            if 0 <= hour <= 5 and hour >= LATE_NIGHT_HOUR:
                late_nights[msg.sender].append(msg)

    if not late_nights:
        return None

    top_person = max(late_nights.keys(), key=lambda p: len(late_nights[p]))
    late_msgs = late_nights[top_person]

    if len(late_msgs) < MIN_PATTERN_FREQUENCY:
        return None

    latest = max(late_msgs, key=lambda m: m.timestamp.hour * 60 + m.timestamp.minute)
    latest_time = latest.timestamp.strftime("%I:%M %p")

    strength = min(1.0, len(late_msgs) / 10)

    evidence = [
        {
            "timestamp": m.timestamp.isoformat(),
            "time": m.timestamp.strftime("%I:%M %p"),
            "text": m.text[:100],
        }
        for m in late_msgs[:5]
    ]

    return DetectedPattern(
        pattern_type="late_goodnight",
        person=top_person,
        frequency=len(late_msgs),
        evidence=evidence,
        strength=strength,
        description=f"Said 'goodnight' after {LATE_NIGHT_HOUR}am {len(late_msgs)} times. Latest: {latest_time}",
    )


def _detect_midnight_philosopher(messages: list[Message]) -> list[DetectedPattern]:
    """Detect who sends substantive messages late at night."""
    patterns = []

    # Messages after 1am with significant length (>50 chars, >10 words)
    late_substantial: dict[str, list[Message]] = defaultdict(list)

    for msg in messages:
        hour = msg.timestamp.hour
        if 0 <= hour <= 4 and hour >= MIDNIGHT_PHILOSOPHER_HOUR:
            words = len(msg.text.split())
            if len(msg.text) > 50 and words > 10:
                late_substantial[msg.sender].append(msg)

    for person, msgs in late_substantial.items():
        if len(msgs) < MIN_PATTERN_FREQUENCY:
            continue

        strength = min(1.0, len(msgs) / 20)

        evidence = [
            {
                "timestamp": m.timestamp.isoformat(),
                "time": m.timestamp.strftime("%I:%M %p"),
                "preview": m.text[:80] + "..." if len(m.text) > 80 else m.text,
            }
            for m in msgs[:5]
        ]

        patterns.append(
            DetectedPattern(
                pattern_type="midnight_philosopher",
                person=person,
                frequency=len(msgs),
                evidence=evidence,
                strength=strength,
                description=f"Sent {len(msgs)} substantive messages after {MIDNIGHT_PHILOSOPHER_HOUR}am",
            )
        )

    return patterns


# =============================================================================
# Phrase Pattern Detectors
# =============================================================================


def _detect_catchphrase(messages: list[Message]) -> dict[str, DetectedPattern]:
    """Detect repeated phrases that could be catchphrases."""
    patterns = {}

    # Group messages by sender
    by_sender: dict[str, list[str]] = defaultdict(list)
    for msg in messages:
        if msg.sender and len(msg.text) > 3 and not msg.is_media:
            text_lower = msg.text.lower()
            # Skip excluded system-like phrases
            if any(excl in text_lower for excl in EXCLUDED_PHRASES):
                continue
            by_sender[msg.sender].append(text_lower)

    for person, texts in by_sender.items():
        # Extract 2-4 word phrases
        phrase_counts: Counter[str] = Counter()

        for text in texts:
            # Clean text
            words = re.findall(r"[a-z']+", text.lower())
            words = [w for w in words if w not in COMMON_WORDS and len(w) > 2]

            # Extract n-grams
            for n in [2, 3, 4]:
                for i in range(len(words) - n + 1):
                    phrase = " ".join(words[i : i + n])
                    # Skip if phrase contains excluded terms
                    if any(excl in phrase for excl in EXCLUDED_PHRASES):
                        continue
                    phrase_counts[phrase] += 1

        if not phrase_counts:
            continue

        # Find most common non-trivial phrase
        top_phrases = phrase_counts.most_common(10)
        for phrase, count in top_phrases:
            if count >= MIN_PATTERN_FREQUENCY:
                strength = min(1.0, count / 20)
                patterns[person] = DetectedPattern(
                    pattern_type="catchphrase",
                    person=person,
                    frequency=count,
                    evidence=[{"phrase": phrase, "count": count}],
                    strength=strength,
                    description=f"Uses '{phrase}' {count} times",
                )
                break

    return patterns


def _detect_laugh_style(messages: list[Message]) -> dict[str, DetectedPattern]:
    """Detect each person's laugh style (haha vs hahaha vs hehe)."""
    patterns = {}

    laugh_patterns = {
        "haha": re.compile(r"\bhaha\b", re.IGNORECASE),
        "hahaha+": re.compile(r"\b(hahaha+|hahahaha+)\b", re.IGNORECASE),
        "hehe": re.compile(r"\bhehe+\b", re.IGNORECASE),
        "lol": re.compile(r"\blol\b", re.IGNORECASE),
        "lmao": re.compile(r"\bl(m)?ao\b", re.IGNORECASE),
    }

    by_sender: dict[str, Counter[str]] = defaultdict(Counter)

    for msg in messages:
        if not msg.sender:
            continue
        for laugh_type, pattern in laugh_patterns.items():
            matches = pattern.findall(msg.text)
            if matches:
                by_sender[msg.sender][laugh_type] += len(matches)

    for person, counts in by_sender.items():
        if not counts:
            continue

        total = sum(counts.values())
        if total < MIN_PATTERN_FREQUENCY:
            continue

        # Find dominant laugh style
        top_laugh, top_count = counts.most_common(1)[0]
        percentage = (top_count / total) * 100

        # Only report if there's a clear preference (>35%)
        if percentage < 35:
            continue

        strength = min(1.0, total / 50) * (percentage / 100)

        patterns[person] = DetectedPattern(
            pattern_type="laugh_style",
            person=person,
            frequency=total,
            evidence=[{"style": top_laugh, "count": top_count, "percentage": round(percentage, 1)}],
            strength=strength,
            description=f"Laughs with '{top_laugh}' {round(percentage)}% of the time ({top_count} uses)",
        )

    return patterns


def _detect_apology_patterns(messages: list[Message]) -> Optional[DetectedPattern]:
    """Detect who apologizes for being late the most."""
    apology_patterns = [
        re.compile(r"sorry.{0,20}(late|delay|took so long)", re.IGNORECASE),
        re.compile(r"(running|gonna be|will be).{0,10}late", re.IGNORECASE),
        re.compile(r"apolog.{0,20}(late|delay)", re.IGNORECASE),
        re.compile(r"my bad.{0,20}(late|delay)", re.IGNORECASE),
    ]

    apologies: dict[str, list[Message]] = defaultdict(list)

    for msg in messages:
        if not msg.sender:
            continue
        for pattern in apology_patterns:
            if pattern.search(msg.text):
                apologies[msg.sender].append(msg)
                break

    if not apologies:
        return None

    top_person = max(apologies.keys(), key=lambda p: len(apologies[p]))
    msgs = apologies[top_person]

    if len(msgs) < MIN_PATTERN_FREQUENCY:
        return None

    strength = min(1.0, len(msgs) / 25)

    evidence = [
        {
            "timestamp": m.timestamp.isoformat(),
            "text": m.text[:100],
        }
        for m in msgs[:5]
    ]

    return DetectedPattern(
        pattern_type="apology_lateness",
        person=top_person,
        frequency=len(msgs),
        evidence=evidence,
        strength=strength,
        description=f"Apologized for being late or delayed {len(msgs)} times",
    )


# =============================================================================
# Punctuation and Emoji Detectors
# =============================================================================


def _detect_punctuation_habits(messages: list[Message]) -> dict[str, DetectedPattern]:
    """Detect excessive punctuation usage (!!!, ???)."""
    patterns = {}

    exclaim_pattern = re.compile(r"!{3,}")
    question_pattern = re.compile(r"\?{3,}")

    by_sender: dict[str, dict[str, int]] = defaultdict(lambda: {"!!!": 0, "???": 0})

    for msg in messages:
        if not msg.sender:
            continue
        by_sender[msg.sender]["!!!"] += len(exclaim_pattern.findall(msg.text))
        by_sender[msg.sender]["???"] += len(question_pattern.findall(msg.text))

    for person, counts in by_sender.items():
        # Check for exclamation enthusiasm
        if counts["!!!"] >= MIN_PATTERN_FREQUENCY:
            strength = min(1.0, counts["!!!"] / 30)
            patterns[f"{person}_exclaim"] = DetectedPattern(
                pattern_type="punctuation_exclaim",
                person=person,
                frequency=counts["!!!"],
                evidence=[{"punctuation": "!!!", "count": counts["!!!"]}],
                strength=strength,
                description=f"Uses '!!!' {counts['!!!']} times (enthusiastic!)",
            )

        # Check for question confusion
        if counts["???"] >= MIN_PATTERN_FREQUENCY:
            strength = min(1.0, counts["???"] / 20)
            patterns[f"{person}_question"] = DetectedPattern(
                pattern_type="punctuation_question",
                person=person,
                frequency=counts["???"],
                evidence=[{"punctuation": "???", "count": counts["???"]}],
                strength=strength,
                description=f"Uses '???' {counts['???']} times (confused???)",
            )

    return patterns


def _detect_emoji_signature(
    messages: list[Message], stats: Statistics
) -> dict[str, DetectedPattern]:
    """Detect each person's signature emoji."""
    patterns = {}

    # Use pre-computed emoji stats
    top_emojis = stats.content.top_emojis_per_person

    for person, emojis in top_emojis.items():
        if not emojis:
            continue

        top_emoji, count = emojis[0]

        if count < MIN_PATTERN_FREQUENCY:
            continue

        # Check if this person uses it significantly more than others
        other_counts = []
        for other_person, other_emojis in top_emojis.items():
            if other_person != person:
                emoji_dict = dict(other_emojis)
                other_counts.append(emoji_dict.get(top_emoji, 0))

        avg_other = sum(other_counts) / len(other_counts) if other_counts else 0

        # Only interesting if they use it 2x more than average
        if avg_other > 0 and count < avg_other * 1.5:
            continue

        strength = min(1.0, count / 50)

        patterns[person] = DetectedPattern(
            pattern_type="emoji_signature",
            person=person,
            frequency=count,
            evidence=[{"emoji": top_emoji, "count": count}],
            strength=strength,
            description=f"Champion of the {top_emoji} emoji - used {count} times",
        )

    return patterns


# =============================================================================
# Texting Style Detectors
# =============================================================================


def _detect_triple_texter(messages: list[Message]) -> dict[str, DetectedPattern]:
    """Detect who sends 3+ messages in a row before getting a response."""
    patterns = {}

    triple_text_counts: dict[str, int] = defaultdict(int)
    triple_text_examples: dict[str, list[list[Message]]] = defaultdict(list)

    current_sender = None
    current_streak: list[Message] = []

    for msg in messages:
        if msg.is_system or not msg.sender:
            continue

        if msg.sender == current_sender:
            current_streak.append(msg)
        else:
            # Streak ended
            if len(current_streak) >= 3 and current_sender:
                triple_text_counts[current_sender] += 1
                if len(triple_text_examples[current_sender]) < 3:
                    triple_text_examples[current_sender].append(current_streak[:5])
            current_sender = msg.sender
            current_streak = [msg]

    # Don't forget the last streak
    if len(current_streak) >= 3 and current_sender:
        triple_text_counts[current_sender] += 1

    for person, count in triple_text_counts.items():
        if count < MIN_PATTERN_FREQUENCY:
            continue

        strength = min(1.0, count / 50)

        # Build evidence from examples
        evidence = []
        for streak in triple_text_examples[person]:
            evidence.append(
                {
                    "streak_length": len(streak),
                    "messages": [{"text": m.text[:50]} for m in streak[:3]],
                }
            )

        patterns[person] = DetectedPattern(
            pattern_type="triple_texter",
            person=person,
            frequency=count,
            evidence=evidence,
            strength=strength,
            description=f"Sent 3+ messages in a row {count} times before getting a response",
        )

    return patterns


def _detect_message_length_style(
    messages: list[Message], stats: Statistics
) -> dict[str, DetectedPattern]:
    """Detect if someone is a 'paragraph person' or 'rapid-fire texter'."""
    patterns = {}

    avg_lengths = stats.basic.avg_message_length

    if len(avg_lengths) < 2:
        return patterns

    # Calculate the average across all participants
    overall_avg = sum(avg_lengths.values()) / len(avg_lengths)

    for person, avg_len in avg_lengths.items():
        # Paragraph person: avg > 2x overall average and > 15 words
        if avg_len > overall_avg * 1.8 and avg_len > 15:
            strength = min(1.0, (avg_len / overall_avg - 1) / 2)
            patterns[person] = DetectedPattern(
                pattern_type="paragraph_person",
                person=person,
                frequency=stats.basic.messages_per_person.get(person, 0),
                evidence=[{"avg_words_per_message": round(avg_len, 1)}],
                strength=strength,
                description=f"Writes {round(avg_len, 1)} words per message on average (the paragraph person)",
            )

        # Rapid-fire: avg < 0.5x overall average and < 5 words
        elif avg_len < overall_avg * 0.6 and avg_len < 6:
            strength = min(1.0, (1 - avg_len / overall_avg) / 0.5)
            patterns[person] = DetectedPattern(
                pattern_type="rapid_fire",
                person=person,
                frequency=stats.basic.messages_per_person.get(person, 0),
                evidence=[{"avg_words_per_message": round(avg_len, 1)}],
                strength=strength,
                description=f"Averages just {round(avg_len, 1)} words per message (the rapid-fire texter)",
            )

    return patterns


# =============================================================================
# Interaction Pattern Detectors
# =============================================================================


def _detect_initiator_imbalance(
    conversation: Conversation, stats: Statistics
) -> Optional[DetectedPattern]:
    """Detect if one person initiates conversations much more than the other."""
    initiators = stats.interaction.conversation_initiators

    if len(initiators) < 2:
        return None

    total = sum(initiators.values())
    if total < 5:
        return None

    top_person = max(initiators.keys(), key=lambda p: initiators[p])
    top_count = initiators[top_person]
    percentage = (top_count / total) * 100

    # Only flag if significant imbalance (>65%)
    if percentage < 65:
        return None

    strength = min(1.0, (percentage - 50) / 40)

    return DetectedPattern(
        pattern_type="conversation_initiator",
        person=top_person,
        frequency=top_count,
        evidence=[{"percentage": round(percentage, 1), "total_conversations": total}],
        strength=strength,
        description=f"Initiates {round(percentage)}% of conversations ({top_count} of {total})",
    )


def _detect_question_asker(messages: list[Message]) -> dict[str, DetectedPattern]:
    """Detect who asks the most questions relative to statements."""
    patterns = {}

    question_counts: dict[str, int] = defaultdict(int)
    statement_counts: dict[str, int] = defaultdict(int)

    for msg in messages:
        if not msg.sender:
            continue

        # Count sentences ending with ? vs .
        questions = msg.text.count("?")
        periods = msg.text.count(".")

        question_counts[msg.sender] += questions
        statement_counts[msg.sender] += periods

    for person in question_counts:
        questions = question_counts[person]
        statements = statement_counts[person]
        total = questions + statements

        if total < 20:
            continue

        question_ratio = questions / total if total > 0 else 0

        # Only interesting if > 40% questions
        if question_ratio < 0.4:
            continue

        strength = min(1.0, (question_ratio - 0.3) / 0.4)

        patterns[person] = DetectedPattern(
            pattern_type="question_asker",
            person=person,
            frequency=questions,
            evidence=[
                {
                    "questions": questions,
                    "statements": statements,
                    "ratio": round(question_ratio * 100, 1),
                }
            ],
            strength=strength,
            description=f"Asks questions {round(question_ratio * 100)}% of the time ({questions} questions)",
        )

    return patterns
