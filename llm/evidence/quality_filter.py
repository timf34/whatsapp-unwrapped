"""Quality filtering of evidence using Haiku as a judge.

This module adds a quality gate between aggregation and synthesis.
Haiku evaluates each piece of evidence and only passes through the
genuinely funny, interesting, or memorable items.
"""

import json
import logging
from typing import Any, Optional

from models import ConversationEvidence
from llm.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


QUALITY_FILTER_SYSTEM_PROMPT = """You are a comedy editor for a "Spotify Wrapped"-style summary of friends' WhatsApp chats. Your job is to filter content - only the BEST stuff makes the cut.

You have HIGH STANDARDS. Most chat content is boring logistics, mundane scheduling, or generic conversation. We want only the gems - the stuff that makes this friendship special and will make readers laugh or smile.

KEEP content that is:
- Actually funny (would make someone laugh out loud)
- Genuinely memorable (participants would remember this moment fondly)
- Uniquely characteristic (reveals personality, quirks, or relationship dynamics)
- Specific and quotable (has a clear punchline or memorable line)
- Endearing or charming (shows real affection or vulnerability)

REJECT content that is:
- Boring logistics (scheduling, confirming plans, routine coordination)
- Generic interactions ("sounds good", "ok see you then", normal chitchat)
- Mundane observations that don't reveal anything interesting
- Content that's "fine" but wouldn't make someone smile
- Vague or forgettable moments

Be RUTHLESS. If something is just "okay" or "mildly amusing" - reject it. We only want content that would genuinely delight the users when they see their chat summary.

Return a JSON object with the filtered lists. Only include items that pass your quality bar."""


def build_quality_filter_prompt(evidence: ConversationEvidence) -> str:
    """Build prompt for quality filtering.

    Args:
        evidence: Aggregated evidence to filter

    Returns:
        Prompt string for Haiku
    """
    sections = []

    sections.append("Review the following evidence extracted from a WhatsApp chat.")
    sections.append("For each category, return ONLY the items that are genuinely funny, memorable, or interesting.")
    sections.append("Be ruthless - reject anything boring, generic, or forgettable.")
    sections.append("")

    # Notable quotes
    if evidence.notable_quotes:
        sections.append("## NOTABLE QUOTES")
        sections.append("Each quote should be genuinely funny, quotable, or revealing of personality.")
        sections.append("Reject: mundane statements, boring observations, generic messages.")
        sections.append(json.dumps(evidence.notable_quotes, indent=2))
        sections.append("")

    # Inside jokes
    if evidence.inside_jokes:
        sections.append("## INSIDE JOKES")
        sections.append("Each joke should be a real running joke/reference that would resonate with participants.")
        sections.append("Reject: one-off mentions, boring references, things that aren't actually funny.")
        sections.append(json.dumps(evidence.inside_jokes, indent=2))
        sections.append("")

    # Funny moments
    if evidence.funny_moments:
        sections.append("## FUNNY MOMENTS")
        sections.append("Each moment should be actually hilarious or memorable.")
        sections.append("Reject: mildly amusing things, mundane events, 'fine' moments.")
        sections.append(json.dumps(evidence.funny_moments, indent=2))
        sections.append("")

    # Conversation snippets
    if evidence.conversation_snippets:
        sections.append("## CONVERSATION SNIPPETS")
        sections.append("Each snippet should showcase genuinely funny back-and-forth or a memorable exchange.")
        sections.append("Reject: boring logistics, normal planning, generic conversations.")
        sections.append(json.dumps(evidence.conversation_snippets, indent=2))
        sections.append("")

    # Dynamics
    if evidence.dynamics:
        sections.append("## RELATIONSHIP DYNAMICS")
        sections.append("Each observation should reveal something interesting about the relationship.")
        sections.append("Reject: generic observations, obvious statements, boring notes.")
        sections.append(json.dumps(evidence.dynamics, indent=2))
        sections.append("")

    # Contradictions
    if evidence.contradictions:
        sections.append("## CONTRADICTIONS (Says X, Does Y)")
        sections.append("Each should show a genuinely funny gap between what someone says and does.")
        sections.append("Reject: minor inconsistencies, boring contradictions, anything not actually funny.")
        sections.append(json.dumps(evidence.contradictions, indent=2))
        sections.append("")

    # Roasts
    if evidence.roasts:
        sections.append("## ROASTS")
        sections.append("Each should be an affectionate roast they'd laugh at themselves about.")
        sections.append("Reject: anything mean-spirited, not funny, or that they'd be hurt by.")
        sections.append(json.dumps(evidence.roasts, indent=2))
        sections.append("")

    # Award ideas
    if evidence.award_ideas:
        sections.append("## AWARD IDEAS")
        sections.append("Each award should be funny, specific, and based on real evidence.")
        sections.append("Reject: generic awards, boring concepts, vague ideas.")
        sections.append(json.dumps(evidence.award_ideas, indent=2))
        sections.append("")

    # Instructions
    sections.append("---")
    sections.append("Return a JSON object with these keys (include all keys even if the array is empty):")
    sections.append("- notable_quotes: array of quotes that passed your quality bar")
    sections.append("- inside_jokes: array of jokes that passed your quality bar")
    sections.append("- funny_moments: array of moments that passed your quality bar")
    sections.append("- conversation_snippets: array of snippets that passed your quality bar")
    sections.append("- dynamics: array of dynamics that passed your quality bar")
    sections.append("- contradictions: array of contradictions that passed your quality bar")
    sections.append("- roasts: array of roasts that passed your quality bar")
    sections.append("- award_ideas: array of awards that passed your quality bar")
    sections.append("")
    sections.append("Remember: Be RUTHLESS. Only the genuinely good stuff gets through.")

    return "\n".join(sections)


def filter_evidence_by_quality(
    evidence: ConversationEvidence,
    provider: LLMProvider,
) -> tuple[ConversationEvidence, int, int]:
    """Filter evidence to only include high-quality items.

    Uses Haiku as a judge to evaluate each piece of evidence and
    only pass through the genuinely funny/interesting/memorable items.

    Strategy:
    1. Try returning full filtered evidence
    2. On truncation/parse failure, retry asking for just indices to keep
    3. If that fails, fall back to unfiltered evidence

    Args:
        evidence: Aggregated evidence to filter
        provider: LLM provider (should be Haiku)

    Returns:
        Tuple of (filtered ConversationEvidence, input tokens, output tokens)
    """
    # Count items before filtering
    before_counts = _count_evidence(evidence)
    logger.info(f"Quality filter input: {before_counts}")

    # If very little evidence, skip filtering
    total_items = sum(before_counts.values())
    if total_items < 5:
        logger.info("Skipping quality filter - too few items")
        return evidence, 0, 0

    total_input_tokens = 0
    total_output_tokens = 0

    # Strategy 1: Try returning full filtered evidence
    prompt = build_quality_filter_prompt(evidence)

    try:
        data, response = provider.complete_json(
            prompt=prompt,
            system=QUALITY_FILTER_SYSTEM_PROMPT,
            max_tokens=8192,  # Large since we're returning filtered evidence as JSON
        )
        total_input_tokens += response.input_tokens
        total_output_tokens += response.output_tokens

        filtered = _parse_filtered_response(data, evidence)
        _log_filter_results(before_counts, filtered)
        return filtered, total_input_tokens, total_output_tokens

    except Exception as e:
        logger.warning(f"Full filter failed ({e}), trying index-based fallback...")

    # Strategy 2: Ask for just indices to keep (much smaller response)
    try:
        index_prompt = build_index_filter_prompt(evidence)
        data, response = provider.complete_json(
            prompt=index_prompt,
            system=QUALITY_FILTER_SYSTEM_PROMPT,
            max_tokens=2048,  # Indices are much smaller
        )
        total_input_tokens += response.input_tokens
        total_output_tokens += response.output_tokens

        filtered = _apply_index_filter(data, evidence)
        _log_filter_results(before_counts, filtered)
        return filtered, total_input_tokens, total_output_tokens

    except Exception as e:
        logger.warning(f"Index-based filter also failed ({e}), using unfiltered evidence")
        return evidence, total_input_tokens, total_output_tokens


def _log_filter_results(before_counts: dict[str, int], filtered: ConversationEvidence) -> None:
    """Log the filtering results."""
    after_counts = _count_evidence(filtered)
    logger.info(f"Quality filter output: {after_counts}")

    for key in before_counts:
        before = before_counts[key]
        after = after_counts[key]
        if before > 0:
            pct = (1 - after / before) * 100 if before > 0 else 0
            logger.info(f"  {key}: {before} -> {after} ({pct:.0f}% filtered out)")


def build_index_filter_prompt(evidence: ConversationEvidence) -> str:
    """Build a compact prompt asking for just indices to keep.

    This is the fallback when full evidence return gets truncated.

    Args:
        evidence: Aggregated evidence to filter

    Returns:
        Prompt string for Haiku
    """
    sections = []

    sections.append("Review the evidence below. For each category, return ONLY the indices (0-based) of items worth keeping.")
    sections.append("Be ruthless - only keep genuinely funny, memorable, or interesting items.")
    sections.append("")

    # Number each item so Haiku can reference by index
    if evidence.notable_quotes:
        sections.append("## NOTABLE QUOTES")
        for i, q in enumerate(evidence.notable_quotes):
            person = q.get("person", "?")
            quote = q.get("quote", "?")[:100]
            sections.append(f"  [{i}] {person}: \"{quote}\"")
        sections.append("")

    if evidence.inside_jokes:
        sections.append("## INSIDE JOKES")
        for i, j in enumerate(evidence.inside_jokes):
            ref = j.get("reference", "?")[:100]
            sections.append(f"  [{i}] \"{ref}\"")
        sections.append("")

    if evidence.funny_moments:
        sections.append("## FUNNY MOMENTS")
        for i, f in enumerate(evidence.funny_moments):
            desc = f.get("description", "?")[:100]
            sections.append(f"  [{i}] {desc}")
        sections.append("")

    if evidence.conversation_snippets:
        sections.append("## CONVERSATION SNIPPETS")
        for i, s in enumerate(evidence.conversation_snippets):
            context = s.get("context", "?")[:80]
            sections.append(f"  [{i}] {context}")
        sections.append("")

    if evidence.dynamics:
        sections.append("## DYNAMICS")
        for i, d in enumerate(evidence.dynamics):
            sections.append(f"  [{i}] {d[:100]}")
        sections.append("")

    if evidence.contradictions:
        sections.append("## CONTRADICTIONS")
        for i, c in enumerate(evidence.contradictions):
            person = c.get("person", "?")
            says = c.get("says", "?")[:50]
            sections.append(f"  [{i}] {person}: says '{says}...'")
        sections.append("")

    if evidence.roasts:
        sections.append("## ROASTS")
        for i, r in enumerate(evidence.roasts):
            person = r.get("person", "?")
            roast = r.get("roast", "?")[:60]
            sections.append(f"  [{i}] {person}: {roast}")
        sections.append("")

    if evidence.award_ideas:
        sections.append("## AWARD IDEAS")
        for i, a in enumerate(evidence.award_ideas):
            title = a.get("title", "?")
            recipient = a.get("recipient", "?")
            sections.append(f"  [{i}] \"{title}\" for {recipient}")
        sections.append("")

    sections.append("---")
    sections.append("Return a JSON object with arrays of indices to KEEP for each category:")
    sections.append("{")
    sections.append("  \"notable_quotes\": [0, 2, 5],  // indices of quotes to keep")
    sections.append("  \"inside_jokes\": [1, 3],")
    sections.append("  \"funny_moments\": [0, 4, 7],")
    sections.append("  \"conversation_snippets\": [2],")
    sections.append("  \"dynamics\": [0, 1],")
    sections.append("  \"contradictions\": [0],")
    sections.append("  \"roasts\": [1, 2],")
    sections.append("  \"award_ideas\": [1, 3, 5]")
    sections.append("}")

    return "\n".join(sections)


def _apply_index_filter(
    data: dict[str, Any],
    original: ConversationEvidence,
) -> ConversationEvidence:
    """Apply index-based filter to original evidence.

    Args:
        data: Dict with arrays of indices to keep
        original: Original evidence

    Returns:
        Filtered ConversationEvidence
    """
    def filter_by_indices(items: list, indices: Any) -> list:
        """Keep only items at specified indices."""
        if not isinstance(indices, list):
            return items  # Fall back to keeping all
        valid_indices = [i for i in indices if isinstance(i, int) and 0 <= i < len(items)]
        return [items[i] for i in valid_indices]

    return ConversationEvidence(
        notable_quotes=filter_by_indices(
            original.notable_quotes,
            data.get("notable_quotes")
        ),
        inside_jokes=filter_by_indices(
            original.inside_jokes,
            data.get("inside_jokes")
        ),
        funny_moments=filter_by_indices(
            original.funny_moments,
            data.get("funny_moments")
        ),
        conversation_snippets=filter_by_indices(
            original.conversation_snippets,
            data.get("conversation_snippets")
        ),
        dynamics=filter_by_indices(
            original.dynamics,
            data.get("dynamics")
        ),
        contradictions=filter_by_indices(
            original.contradictions,
            data.get("contradictions")
        ),
        roasts=filter_by_indices(
            original.roasts,
            data.get("roasts")
        ),
        award_ideas=filter_by_indices(
            original.award_ideas,
            data.get("award_ideas")
        ),
        style_notes=original.style_notes,  # Keep all style notes
    )


def _count_evidence(evidence: ConversationEvidence) -> dict[str, int]:
    """Count items in each evidence category."""
    return {
        "quotes": len(evidence.notable_quotes),
        "jokes": len(evidence.inside_jokes),
        "moments": len(evidence.funny_moments),
        "snippets": len(evidence.conversation_snippets),
        "dynamics": len(evidence.dynamics),
        "contradictions": len(evidence.contradictions),
        "roasts": len(evidence.roasts),
        "awards": len(evidence.award_ideas),
    }


def _parse_filtered_response(
    data: dict[str, Any],
    original: ConversationEvidence,
) -> ConversationEvidence:
    """Parse Haiku's filtered response.

    Falls back to original data for any category that fails parsing.

    Args:
        data: Parsed JSON from Haiku
        original: Original evidence (fallback)

    Returns:
        Filtered ConversationEvidence
    """
    def safe_list(key: str, original_list: list) -> list:
        """Get list from data or fall back to original."""
        value = data.get(key)
        if isinstance(value, list):
            return value
        return original_list

    def safe_string_list(key: str, original_list: list[str]) -> list[str]:
        """Get string list from data or fall back to original."""
        value = data.get(key)
        if isinstance(value, list):
            return [str(item) for item in value if item]
        return original_list

    return ConversationEvidence(
        notable_quotes=safe_list("notable_quotes", original.notable_quotes),
        inside_jokes=safe_list("inside_jokes", original.inside_jokes),
        funny_moments=safe_list("funny_moments", original.funny_moments),
        conversation_snippets=safe_list("conversation_snippets", original.conversation_snippets),
        dynamics=safe_string_list("dynamics", original.dynamics),
        contradictions=safe_list("contradictions", original.contradictions),
        roasts=safe_list("roasts", original.roasts),
        award_ideas=safe_list("award_ideas", original.award_ideas),
        style_notes=original.style_notes,  # Don't filter style notes - they're descriptive
    )
