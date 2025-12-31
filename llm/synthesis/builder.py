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
    sections.append(f"""Generate exactly 10 awards for {participants_str}.

Requirements:
- Balance: Aim for 5 awards per person (4-6 acceptable)
- Specificity: Every award must cite specific evidence (numbers, quotes, times)
- Tone: Celebratory and funny, never mean or critical
- Uniqueness: Each award should highlight a different behavioral pattern
- Pick the BEST award ideas from the evidence provided - the funniest, most specific ones

Output a JSON object with an "awards" array containing exactly 10 award objects.
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
    """Format qualitative evidence for the prompt.

    We pass ALL evidence to Sonnet so it has maximum context to work with.
    More evidence = more specific, accurate, and funny awards.
    """
    lines = []

    # Notable quotes - ALL of them for maximum context
    if evidence.notable_quotes:
        lines.append("### Notable Quotes")
        for q in evidence.notable_quotes:  # No limit - pass everything
            person = q.get("person", "?")
            quote = q.get("quote", "?")
            # Handle both old "why_notable" and new "punchline" field
            punchline = q.get("punchline", q.get("why_notable", ""))
            lines.append(f'- {person}: "{quote}"')
            if punchline:
                lines.append(f"  ({punchline})")
        lines.append("")

    # Inside jokes - ALL of them
    if evidence.inside_jokes:
        lines.append("### Inside Jokes/References")
        for j in evidence.inside_jokes:  # No limit
            ref = j.get("reference", "?")
            # Handle both old "context" and new "punchline" field
            punchline = j.get("punchline", j.get("context", ""))
            lines.append(f'- "{ref}"')
            if punchline:
                lines.append(f"  {punchline}")
        lines.append("")

    # Funny moments - ALL of them
    if evidence.funny_moments:
        lines.append("### Funny Moments")
        for f in evidence.funny_moments:  # No limit
            desc = f.get("description", "?")
            lines.append(f"- {desc}")
        lines.append("")

    # Dynamics - ALL of them
    if evidence.dynamics:
        lines.append("### Relationship Dynamics")
        for d in evidence.dynamics:  # No limit
            lines.append(f"- {d}")
        lines.append("")

    # Style notes - ALL of them
    if evidence.style_notes:
        lines.append("### Texting Style Notes")
        for person, notes in evidence.style_notes.items():
            lines.append(f"**{person}:**")
            for note in notes:  # No limit
                lines.append(f"- {note}")
        lines.append("")

    # Conversation snippets - these show the actual back-and-forth
    if evidence.conversation_snippets:
        lines.append("### Conversation Snippets (actual exchanges)")
        lines.append("These show the back-and-forth that makes moments funny. Use these for context and specific quotes:")
        for snippet in evidence.conversation_snippets:
            context = snippet.get("context", "?")
            exchange = snippet.get("exchange", [])
            punchline = snippet.get("punchline", "")
            lines.append(f"\n**{context}**")
            for msg in exchange:
                sender = msg.get("sender", "?")
                text = msg.get("text", "?")
                lines.append(f"  {sender}: {text}")
            if punchline:
                lines.append(f"  → {punchline}")
        lines.append("")

    # Award ideas from Haiku - ALL of them for Sonnet to pick from
    if evidence.award_ideas:
        lines.append("### Suggested Award Ideas (from analysis)")
        lines.append("These are award ideas extracted from the conversation. Pick the BEST and most specific ones, or combine/improve them:")
        for a in evidence.award_ideas:  # No limit - let Sonnet see everything
            title = a.get("title", "?")
            recipient = a.get("recipient", "?")
            ev = a.get("evidence", "")
            lines.append(f'- "{title}" for {recipient}')
            if ev:
                lines.append(f"  Evidence: {ev}")
        lines.append("")

    return "\n".join(lines)


def _format_sample_messages(messages: list[Message]) -> str:
    """Format sample messages for voice reference.

    Includes more messages to give Sonnet better context for
    the actual voice and personality of the conversation.
    """
    lines = []

    for msg in messages:  # No cap - include all selected samples
        timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M")
        sender = msg.sender or "System"
        # Allow longer snippets for better context
        text = msg.text[:300] + "..." if len(msg.text) > 300 else msg.text
        lines.append(f"[{timestamp}] {sender}: {text}")

    return "\n".join(lines)


def select_sample_messages(
    conversation: Conversation,
    count: int = 50,
) -> list[Message]:
    """Select representative sample messages from the conversation.

    Selects a generous mix of:
    - Recent messages (for current voice)
    - Messages with personality (longer, with emojis, questions, exclamations)
    - Spread across the conversation (for full picture)

    More samples = better context for Sonnet to understand the real
    personality and voice of the conversation.

    Args:
        conversation: Full conversation
        count: Number of samples to select (default 50 for good coverage)

    Returns:
        List of representative messages
    """
    # Filter to user messages only
    messages = [m for m in conversation.messages if not m.is_system and m.sender]

    if len(messages) <= count:
        return messages

    samples = []
    used_indices = set()

    # Get some recent messages (last 20%) - about 1/3 of samples
    recent_start = int(len(messages) * 0.8)
    recent = messages[recent_start:]
    recent_count = min(count // 3, len(recent))
    recent_samples = random.sample(range(len(recent)), recent_count)
    for idx in recent_samples:
        samples.append(recent[idx])
        used_indices.add(recent_start + idx)

    # Get messages with personality (longer ones, with emojis, punctuation) - about 1/3 of samples
    personality_msgs = [
        (i, m) for i, m in enumerate(messages)
        if i not in used_indices and (
            len(m.text) > 50 or "!" in m.text or "?" in m.text or "haha" in m.text.lower()
        )
    ]
    if personality_msgs:
        personality_count = min((count - len(samples)) // 2, len(personality_msgs))
        personality_samples = random.sample(personality_msgs, personality_count)
        for idx, msg in personality_samples:
            samples.append(msg)
            used_indices.add(idx)

    # Fill rest with spread across conversation for temporal coverage
    remaining = count - len(samples)
    if remaining > 0:
        step = max(1, len(messages) // remaining)
        for i in range(0, len(messages), step):
            if len(samples) >= count:
                break
            if i not in used_indices:
                samples.append(messages[i])
                used_indices.add(i)

    # Sort by timestamp
    samples.sort(key=lambda m: m.timestamp)

    return samples[:count]
