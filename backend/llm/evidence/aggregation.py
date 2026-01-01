"""Evidence aggregation across chunks."""

import random
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from typing import Any

from models import ConversationEvidence, EvidencePacket


# Aggregation limits - generous to capture the full conversation
MAX_QUOTES = 30
MAX_INSIDE_JOKES = 20
MAX_DYNAMICS = 15
MAX_FUNNY_MOMENTS = 20
MAX_STYLE_NOTES_PER_PERSON = 8
MAX_AWARD_IDEAS = 30
MAX_SNIPPETS = 15  # Conversation snippets are valuable context
MAX_CONTRADICTIONS = 10  # Says X, does Y moments
MAX_ROASTS = 15  # Affectionate roast material

# Similarity threshold for deduplication
SIMILARITY_THRESHOLD = 0.8


def aggregate_evidence(packets: list[EvidencePacket]) -> ConversationEvidence:
    """Aggregate evidence packets into unified evidence.

    Uses temporal-aware sampling to get diverse evidence from across the
    conversation, then deduplicates similar items.

    Args:
        packets: Evidence packets from all chunks

    Returns:
        Aggregated conversation evidence
    """
    if not packets:
        return _create_empty_evidence()

    # Collect items with chunk index for temporal diversity
    quotes_with_idx: list[tuple[int, dict]] = []
    jokes_with_idx: list[tuple[int, dict]] = []
    dynamics_with_idx: list[tuple[int, str]] = []
    funny_with_idx: list[tuple[int, dict]] = []
    awards_with_idx: list[tuple[int, dict]] = []
    snippets_with_idx: list[tuple[int, dict]] = []
    contradictions_with_idx: list[tuple[int, dict]] = []
    roasts_with_idx: list[tuple[int, dict]] = []
    all_style_notes: dict[str, list[str]] = defaultdict(list)

    for chunk_idx, packet in enumerate(packets):
        for item in packet.notable_quotes:
            quotes_with_idx.append((chunk_idx, item))
        for item in packet.inside_jokes:
            jokes_with_idx.append((chunk_idx, item))
        for item in packet.dynamics:
            dynamics_with_idx.append((chunk_idx, item))
        for item in packet.funny_moments:
            funny_with_idx.append((chunk_idx, item))
        for item in packet.award_ideas:
            awards_with_idx.append((chunk_idx, item))
        for item in packet.conversation_snippets:
            snippets_with_idx.append((chunk_idx, item))
        for item in packet.contradictions:
            contradictions_with_idx.append((chunk_idx, item))
        for item in packet.roasts:
            roasts_with_idx.append((chunk_idx, item))

        for person, notes in packet.style_notes.items():
            all_style_notes[person].extend(notes)

    # Apply temporal-aware sampling, then deduplicate
    sampled_quotes = _temporal_sample(quotes_with_idx, MAX_QUOTES * 2)
    sampled_jokes = _temporal_sample(jokes_with_idx, MAX_INSIDE_JOKES * 2)
    sampled_dynamics = _temporal_sample(dynamics_with_idx, MAX_DYNAMICS * 2)
    sampled_funny = _temporal_sample(funny_with_idx, MAX_FUNNY_MOMENTS * 2)
    sampled_awards = _temporal_sample(awards_with_idx, MAX_AWARD_IDEAS * 2)
    sampled_snippets = _temporal_sample(snippets_with_idx, MAX_SNIPPETS * 2)
    sampled_contradictions = _temporal_sample(contradictions_with_idx, MAX_CONTRADICTIONS * 2)
    sampled_roasts = _temporal_sample(roasts_with_idx, MAX_ROASTS * 2)

    # Deduplicate and rank (now working on temporally diverse sample)
    deduped_quotes = _deduplicate_quotes(sampled_quotes)[:MAX_QUOTES]
    ranked_jokes = _rank_inside_jokes(sampled_jokes)[:MAX_INSIDE_JOKES]
    deduped_dynamics = _deduplicate_strings(sampled_dynamics)[:MAX_DYNAMICS]
    deduped_funny = _deduplicate_by_field(sampled_funny, "description")[:MAX_FUNNY_MOMENTS]
    merged_style = _merge_style_notes(all_style_notes)
    ranked_awards = _rank_award_ideas(sampled_awards)[:MAX_AWARD_IDEAS]
    deduped_snippets = _deduplicate_snippets(sampled_snippets)[:MAX_SNIPPETS]
    deduped_contradictions = _deduplicate_by_field(sampled_contradictions, "punchline")[:MAX_CONTRADICTIONS]
    deduped_roasts = _deduplicate_by_field(sampled_roasts, "roast")[:MAX_ROASTS]

    return ConversationEvidence(
        notable_quotes=deduped_quotes,
        inside_jokes=ranked_jokes,
        dynamics=deduped_dynamics,
        funny_moments=deduped_funny,
        style_notes=merged_style,
        award_ideas=ranked_awards,
        conversation_snippets=deduped_snippets,
        contradictions=deduped_contradictions,
        roasts=deduped_roasts,
    )


def _temporal_sample(items_with_idx: list[tuple[int, Any]], max_count: int) -> list[Any]:
    """Sample items evenly across chunks to maintain temporal diversity.

    Divides chunks into buckets and samples evenly from each, ensuring
    evidence from later in the conversation isn't dropped.

    Args:
        items_with_idx: List of (chunk_index, item) tuples
        max_count: Maximum items to return

    Returns:
        Sampled items (without chunk index)
    """
    if not items_with_idx:
        return []

    if len(items_with_idx) <= max_count:
        return [item for _, item in items_with_idx]

    # Group by chunk index
    by_chunk: dict[int, list[Any]] = defaultdict(list)
    for chunk_idx, item in items_with_idx:
        by_chunk[chunk_idx].append(item)

    # Calculate items per chunk (round-robin allocation)
    chunk_indices = sorted(by_chunk.keys())
    num_chunks = len(chunk_indices)
    base_per_chunk = max_count // num_chunks
    extra = max_count % num_chunks

    result = []
    for i, chunk_idx in enumerate(chunk_indices):
        chunk_items = by_chunk[chunk_idx]
        # Earlier chunks get fewer, later chunks get slightly more to compensate for bias
        take = base_per_chunk + (1 if i >= num_chunks - extra else 0)

        if len(chunk_items) <= take:
            result.extend(chunk_items)
        else:
            # Randomly sample from this chunk
            result.extend(random.sample(chunk_items, take))

    return result


def _create_empty_evidence() -> ConversationEvidence:
    """Create empty aggregated evidence."""
    return ConversationEvidence(
        notable_quotes=[],
        inside_jokes=[],
        dynamics=[],
        funny_moments=[],
        style_notes={},
        award_ideas=[],
        conversation_snippets=[],
        contradictions=[],
        roasts=[],
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


def _deduplicate_snippets(snippets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate conversation snippets by similar context."""
    if not snippets:
        return []

    result = []
    for snippet in snippets:
        context = snippet.get("context", "")
        if not context:
            continue

        # Check if similar snippet already exists
        is_duplicate = False
        for existing in result:
            existing_context = existing.get("context", "")
            if _similarity(context, existing_context) > SIMILARITY_THRESHOLD:
                is_duplicate = True
                break

        if not is_duplicate:
            result.append(snippet)

    return result
