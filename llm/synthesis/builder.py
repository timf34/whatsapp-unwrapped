"""Prompt builder for Sonnet synthesis."""

import json
import random
from typing import Any

from models import (
    Conversation,
    ConversationEvidence,
    DetectedPattern,
    Message,
    Statistics,
)
from llm.synthesis.prompts import EXAMPLE_AWARDS


def build_synthesis_prompt(
    stats: Statistics,
    patterns: list[DetectedPattern],
    evidence: ConversationEvidence | None,
    sample_messages: list[Message],
    participants: list[str],
) -> str:
    """Build the prompt for Sonnet to generate awards.

    Args:
        stats: Computed statistics
        patterns: Detected patterns from Python analysis
        evidence: Aggregated evidence from Haiku (can be None for offline mode)
        sample_messages: Representative messages for voice/style
        participants: List of participant names

    Returns:
        Complete prompt string for Sonnet
    """
    sections = []

    # Header
    participants_str = " and ".join(participants)
    sections.append(f"Create 6 funny, specific awards for the WhatsApp conversation between {participants_str}.")
    sections.append("")

    # Statistics summary
    sections.append("## Conversation Statistics")
    sections.append(_format_stats_summary(stats))
    sections.append("")

    # Detected patterns
    if patterns:
        sections.append("## Detected Behavioral Patterns")
        sections.append(_format_patterns(patterns))
        sections.append("")

    # Qualitative evidence (from Haiku)
    if evidence:
        evidence_section = _format_evidence(evidence)
        if evidence_section.strip():
            sections.append("## Qualitative Evidence")
            sections.append(evidence_section)
            sections.append("")

    # Sample messages for voice
    if sample_messages:
        sections.append("## Sample Messages (for voice/style reference)")
        sections.append(_format_sample_messages(sample_messages))
        sections.append("")

    # Examples
    sections.append("## Examples of Good Awards")
    sections.append(EXAMPLE_AWARDS)
    sections.append("")

    # Instructions
    sections.append("## Your Task")
    sections.append(f"""Generate exactly 6 awards for {participants_str}.

Requirements:
- Balance: Aim for 3 awards per person (2-4 acceptable)
- Specificity: Every award must cite specific evidence (numbers, quotes, times)
- Tone: Celebratory and funny, never mean or critical
- Uniqueness: Each award should highlight a different behavioral pattern

Output a JSON object with an "awards" array containing exactly 6 award objects.
Each award object must have: "title", "recipient", "evidence", "quip".""")

    return "\n".join(sections)


def _format_stats_summary(stats: Statistics) -> str:
    """Format key statistics for the prompt."""
    lines = []

    # Basic counts
    basic = stats.basic
    lines.append(f"- Total messages: {basic.total_messages:,}")
    lines.append(f"- Total words: {basic.total_words:,}")

    # Per-person breakdown
    lines.append("- Messages per person:")
    for person, count in sorted(basic.messages_per_person.items(), key=lambda x: -x[1]):
        pct = (count / basic.total_messages) * 100 if basic.total_messages > 0 else 0
        avg_len = basic.avg_message_length.get(person, 0)
        lines.append(f"  - {person}: {count:,} messages ({pct:.0f}%), avg {avg_len:.1f} words/message")

    # Temporal
    temporal = stats.temporal
    lines.append(f"- Date range: {temporal.first_message_date.strftime('%b %d, %Y')} to {temporal.last_message_date.strftime('%b %d, %Y')}")
    lines.append(f"- Conversation sessions: {temporal.conversation_count}")
    if temporal.busiest_hour is not None:
        lines.append(f"- Busiest hour: {temporal.busiest_hour}:00")

    # Interaction
    interaction = stats.interaction
    if interaction.conversation_initiators:
        lines.append("- Conversation initiators:")
        for person, count in sorted(interaction.conversation_initiators.items(), key=lambda x: -x[1]):
            lines.append(f"  - {person}: {count} times")

    if interaction.avg_response_time:
        lines.append("- Average response times:")
        for person, avg_time in interaction.avg_response_time.items():
            if avg_time < 60:
                lines.append(f"  - {person}: {avg_time:.0f} minutes")
            else:
                lines.append(f"  - {person}: {avg_time / 60:.1f} hours")

    # Top emojis (if any)
    content = stats.content
    if content.top_emojis:
        top_3 = content.top_emojis[:3]
        emoji_str = ", ".join(f"{e} ({c}x)" for e, c in top_3)
        lines.append(f"- Top emojis: {emoji_str}")

    return "\n".join(lines)


def _format_patterns(patterns: list[DetectedPattern]) -> str:
    """Format detected patterns for the prompt.

    Note: We intentionally keep this concise - the raw stats are already
    in the description. The evidence dict is mostly for validation, not
    for Sonnet to copy verbatim. We want Sonnet to write engaging prose,
    not dump these stats.
    """
    lines = []

    for i, pattern in enumerate(patterns[:10], 1):  # Cap at 10 patterns
        lines.append(f"{i}. **{pattern.pattern_type.replace('_', ' ').title()}** ({pattern.person})")
        lines.append(f"   {pattern.description}")
        lines.append("")

    return "\n".join(lines)


def _format_evidence(evidence: ConversationEvidence) -> str:
    """Format qualitative evidence for the prompt."""
    lines = []

    # Notable quotes
    if evidence.notable_quotes:
        lines.append("### Notable Quotes")
        for q in evidence.notable_quotes[:5]:
            person = q.get("person", "?")
            quote = q.get("quote", "?")
            # Handle both old "why_notable" and new "punchline" field
            punchline = q.get("punchline", q.get("why_notable", ""))
            lines.append(f'- {person}: "{quote}"')
            if punchline:
                lines.append(f"  ({punchline})")
        lines.append("")

    # Inside jokes
    if evidence.inside_jokes:
        lines.append("### Inside Jokes/References")
        for j in evidence.inside_jokes[:5]:
            ref = j.get("reference", "?")
            # Handle both old "context" and new "punchline" field
            punchline = j.get("punchline", j.get("context", ""))
            lines.append(f'- "{ref}"')
            if punchline:
                lines.append(f"  {punchline}")
        lines.append("")

    # Funny moments
    if evidence.funny_moments:
        lines.append("### Funny Moments")
        for f in evidence.funny_moments[:5]:
            desc = f.get("description", "?")
            lines.append(f"- {desc}")
        lines.append("")

    # Dynamics
    if evidence.dynamics:
        lines.append("### Relationship Dynamics")
        for d in evidence.dynamics[:3]:
            lines.append(f"- {d}")
        lines.append("")

    # Style notes
    if evidence.style_notes:
        lines.append("### Texting Style Notes")
        for person, notes in evidence.style_notes.items():
            lines.append(f"**{person}:**")
            for note in notes[:3]:
                lines.append(f"- {note}")
        lines.append("")

    # Award ideas from Haiku
    if evidence.award_ideas:
        lines.append("### Suggested Award Ideas (from analysis)")
        for a in evidence.award_ideas[:5]:
            title = a.get("title", "?")
            recipient = a.get("recipient", "?")
            ev = a.get("evidence", "")
            lines.append(f'- "{title}" for {recipient}')
            if ev:
                lines.append(f"  Evidence: {ev}")
        lines.append("")

    return "\n".join(lines)


def _format_sample_messages(messages: list[Message]) -> str:
    """Format sample messages for voice reference."""
    lines = []

    for msg in messages[:15]:  # Cap at 15 samples
        timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M")
        sender = msg.sender or "System"
        text = msg.text[:200] + "..." if len(msg.text) > 200 else msg.text
        lines.append(f"[{timestamp}] {sender}: {text}")

    return "\n".join(lines)


def select_sample_messages(
    conversation: Conversation,
    count: int = 20,
) -> list[Message]:
    """Select representative sample messages from the conversation.

    Selects a mix of:
    - Recent messages
    - Messages with personality (longer, with emojis, etc.)
    - Spread across the conversation

    Args:
        conversation: Full conversation
        count: Number of samples to select

    Returns:
        List of representative messages
    """
    # Filter to user messages only
    messages = [m for m in conversation.messages if not m.is_system and m.sender]

    if len(messages) <= count:
        return messages

    samples = []

    # Get some recent messages (last 20%)
    recent_start = int(len(messages) * 0.8)
    recent = messages[recent_start:]
    samples.extend(random.sample(recent, min(count // 3, len(recent))))

    # Get messages with personality (longer ones, with emojis, punctuation)
    personality_msgs = [
        m for m in messages
        if len(m.text) > 50 or "!" in m.text or "?" in m.text
    ]
    if personality_msgs:
        remaining = count - len(samples)
        samples.extend(random.sample(
            personality_msgs,
            min(remaining // 2, len(personality_msgs))
        ))

    # Fill rest with spread across conversation
    remaining = count - len(samples)
    if remaining > 0:
        step = len(messages) // remaining
        for i in range(0, len(messages), max(1, step)):
            if len(samples) >= count:
                break
            if messages[i] not in samples:
                samples.append(messages[i])

    # Sort by timestamp
    samples.sort(key=lambda m: m.timestamp)

    return samples[:count]
