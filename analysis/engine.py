"""Analysis engine coordinator."""

from models import Conversation, Statistics
from analysis.basic_stats import compute_basic_stats
from analysis.content_stats import compute_content_metrics
from analysis.interaction_stats import compute_interaction_patterns
from analysis.temporal_stats import compute_temporal_patterns


def run_analysis(
    conversation: Conversation,
    gap_hours: float = 4.0,
    min_phrase_freq: int = 3,
    max_ngram: int = 3,
) -> Statistics:
    """Compute all statistics for conversation.

    Args:
        conversation: Parsed conversation
        gap_hours: Hours of inactivity to define conversation restart
        min_phrase_freq: Minimum frequency for n-grams
        max_ngram: Maximum n-gram size (2-4)

    Returns:
        Statistics object with all computed metrics
    """
    basic = compute_basic_stats(conversation)
    temporal = compute_temporal_patterns(conversation, gap_hours)
    content = compute_content_metrics(conversation, min_phrase_freq, max_ngram)
    interaction = compute_interaction_patterns(conversation, gap_hours)

    return Statistics(
        chat_type=conversation.chat_type,
        basic=basic,
        temporal=temporal,
        content=content,
        interaction=interaction,
    )
