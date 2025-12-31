"""Evidence aggregation across chunks."""

from collections import Counter, defaultdict
from difflib import SequenceMatcher
from typing import Any

from models import ConversationEvidence, EvidencePacket


# Aggregation limits
MAX_QUOTES = 15
MAX_INSIDE_JOKES = 10
MAX_DYNAMICS = 10
MAX_FUNNY_MOMENTS = 10
MAX_STYLE_NOTES_PER_PERSON = 5
MAX_AWARD_IDEAS = 15

# Similarity threshold for deduplication
SIMILARITY_THRESHOLD = 0.8


def aggregate_evidence(packets: list[EvidencePacket]) -> ConversationEvidence:
    """Aggregate evidence packets into unified evidence.

    Deduplicates similar items, ranks by frequency/importance,
    and caps each category to prevent prompt bloat.

    Args:
        packets: Evidence packets from all chunks

    Returns:
        Aggregated conversation evidence
    """
    if not packets:
        return _create_empty_evidence()

    # Aggregate each category
    all_quotes = []
    all_inside_jokes = []
    all_dynamics = []
    all_funny_moments = []
    all_style_notes: dict[str, list[str]] = defaultdict(list)
    all_award_ideas = []

    for packet in packets:
        all_quotes.extend(packet.notable_quotes)
        all_inside_jokes.extend(packet.inside_jokes)
        all_dynamics.extend(packet.dynamics)
        all_funny_moments.extend(packet.funny_moments)
        all_award_ideas.extend(packet.award_ideas)

        for person, notes in packet.style_notes.items():
            all_style_notes[person].extend(notes)

    # Deduplicate and rank
    deduped_quotes = _deduplicate_quotes(all_quotes)[:MAX_QUOTES]
    ranked_jokes = _rank_inside_jokes(all_inside_jokes)[:MAX_INSIDE_JOKES]
    deduped_dynamics = _deduplicate_strings(all_dynamics)[:MAX_DYNAMICS]
    deduped_funny = _deduplicate_by_field(all_funny_moments, "description")[:MAX_FUNNY_MOMENTS]
    merged_style = _merge_style_notes(all_style_notes)
    ranked_awards = _rank_award_ideas(all_award_ideas)[:MAX_AWARD_IDEAS]

    return ConversationEvidence(
        notable_quotes=deduped_quotes,
        inside_jokes=ranked_jokes,
        dynamics=deduped_dynamics,
        funny_moments=deduped_funny,
        style_notes=merged_style,
        award_ideas=ranked_awards,
    )


def _create_empty_evidence() -> ConversationEvidence:
    """Create empty aggregated evidence."""
    return ConversationEvidence(
        notable_quotes=[],
        inside_jokes=[],
        dynamics=[],
        funny_moments=[],
        style_notes={},
        award_ideas=[],
    )


def _similarity(a: str, b: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _deduplicate_quotes(quotes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate quotes by similar quote text."""
    if not quotes:
        return []

    result = []
    for quote in quotes:
        quote_text = quote.get("quote", "")
        if not quote_text:
            continue

        # Check if similar quote already exists
        is_duplicate = False
        for existing in result:
            existing_text = existing.get("quote", "")
            if _similarity(quote_text, existing_text) > SIMILARITY_THRESHOLD:
                is_duplicate = True
                break

        if not is_duplicate:
            result.append(quote)

    return result


def _deduplicate_strings(strings: list[str]) -> list[str]:
    """Deduplicate similar strings."""
    if not strings:
        return []

    result = []
    for s in strings:
        if not s:
            continue

        is_duplicate = False
        for existing in result:
            if _similarity(s, existing) > SIMILARITY_THRESHOLD:
                is_duplicate = True
                break

        if not is_duplicate:
            result.append(s)

    return result


def _deduplicate_by_field(
    items: list[dict[str, Any]], field: str
) -> list[dict[str, Any]]:
    """Deduplicate dicts by similarity of a specific field."""
    if not items:
        return []

    result = []
    for item in items:
        value = item.get(field, "")
        if not value:
            continue

        is_duplicate = False
        for existing in result:
            existing_value = existing.get(field, "")
            if _similarity(str(value), str(existing_value)) > SIMILARITY_THRESHOLD:
                is_duplicate = True
                break

        if not is_duplicate:
            result.append(item)

    return result


def _rank_inside_jokes(jokes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank inside jokes by frequency of mention across chunks."""
    if not jokes:
        return []

    # Count occurrences of each reference
    reference_counts: Counter[str] = Counter()
    reference_to_joke: dict[str, dict[str, Any]] = {}

    for joke in jokes:
        ref = joke.get("reference", "").lower().strip()
        if not ref:
            continue

        # Check for similar references
        found_match = False
        for existing_ref in reference_counts:
            if _similarity(ref, existing_ref) > SIMILARITY_THRESHOLD:
                reference_counts[existing_ref] += 1
                found_match = True
                break

        if not found_match:
            reference_counts[ref] = 1
            reference_to_joke[ref] = joke

    # Sort by count and return
    ranked_refs = reference_counts.most_common()
    return [reference_to_joke[ref] for ref, _ in ranked_refs if ref in reference_to_joke]


def _merge_style_notes(
    style_notes: dict[str, list[str]]
) -> dict[str, list[str]]:
    """Merge and deduplicate style notes per person."""
    result = {}

    for person, notes in style_notes.items():
        deduped = _deduplicate_strings(notes)
        result[person] = deduped[:MAX_STYLE_NOTES_PER_PERSON]

    return result


def _rank_award_ideas(awards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank award ideas, preferring unique titles."""
    if not awards:
        return []

    # Deduplicate by title similarity
    deduped = _deduplicate_by_field(awards, "title")

    # Could add more sophisticated ranking here (e.g., by evidence quality)
    return deduped
