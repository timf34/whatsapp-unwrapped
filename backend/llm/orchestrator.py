"""Orchestrator for the three-pass Unwrapped pipeline.

Coordinates:
- Pass 0: Python pattern detection
- Pass 1: Haiku evidence gathering
- Pass 2: Sonnet award synthesis

Provides fallback logic when LLM calls fail.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from models import (
    Award,
    Conversation,
    ConversationEvidence,
    DetectedPattern,
    Statistics,
    UnwrappedResult,
)
from analysis.pattern_detection import detect_all_patterns
from llm.providers import (
    AnthropicProvider, HAIKU_MODEL, SONNET_MODEL,
    OpenAIProvider, GPT_MINI_MODEL, GPT_MAIN_MODEL,
    LLMProvider,
)
from llm.evidence import chunk_conversation, gather_all_evidence, aggregate_evidence, filter_evidence_by_quality
from llm.synthesis import build_synthesis_prompt, select_sample_messages, generate_awards
from llm.logging import SessionLogger, set_logger
from exceptions import ProviderError, EvidenceError, SynthesisError

# Supported providers
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_OPENAI = "openai"
SUPPORTED_PROVIDERS = [PROVIDER_ANTHROPIC, PROVIDER_OPENAI]

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Stages of the Unwrapped pipeline."""
    PATTERNS = "patterns"
    CHUNKING = "chunking"
    EVIDENCE = "evidence"
    SYNTHESIS = "synthesis"
    COMPLETE = "complete"


@dataclass
class ProgressUpdate:
    """Progress update for callbacks."""
    stage: PipelineStage
    message: str
    current: int = 0
    total: int = 0


# Type alias for progress callback
ProgressCallback = Callable[[ProgressUpdate], None]


def generate_unwrapped(
    conversation: Conversation,
    stats: Statistics,
    api_key: Optional[str] = None,
    progress_callback: Optional[ProgressCallback] = None,
    enable_logging: bool = True,
    provider: str = PROVIDER_ANTHROPIC,
) -> UnwrappedResult:
    """Generate Unwrapped awards using the full pipeline.

    This is the main entry point for the LLM-powered pipeline:
    1. Detect patterns (Python, no LLM)
    2. Gather evidence with Haiku/GPT-mini
    3. Synthesize awards with Sonnet/GPT-main

    Args:
        conversation: Parsed conversation
        stats: Computed statistics
        api_key: API key (falls back to env var based on provider)
        progress_callback: Optional callback for progress updates
        enable_logging: Whether to save debug logs to logs/ directory
        provider: LLM provider to use ("anthropic" or "openai")

    Returns:
        UnwrappedResult with awards, patterns, evidence, and metadata

    Raises:
        ProviderError: If API key is missing or invalid
    """
    def _progress(stage: PipelineStage, message: str, current: int = 0, total: int = 0):
        if progress_callback:
            progress_callback(ProgressUpdate(stage, message, current, total))

    participants = list(stats.basic.messages_per_person.keys())
    total_input_tokens = 0
    total_output_tokens = 0

    # Initialize session logger
    session_logger = SessionLogger(enabled=enable_logging, source_file=conversation.source_file)
    set_logger(session_logger)  # Make available globally for terminal output logging
    if session_logger.log_path:
        logger.info(f"Session logs: {session_logger.log_path}")

    # Pass 0: Pattern detection
    _progress(PipelineStage.PATTERNS, "Detecting behavioral patterns...")
    patterns = detect_all_patterns(conversation, stats)
    logger.info(f"Detected {len(patterns)} patterns")

    # Initialize providers based on selection
    try:
        if provider == PROVIDER_OPENAI:
            base_provider = OpenAIProvider(api_key=api_key)
            evidence_provider = base_provider.with_model(GPT_MINI_MODEL)
            synthesis_provider = base_provider.with_model(GPT_MAIN_MODEL)
            model_name = "gpt-mini+gpt-main"
            evidence_model_name = "GPT-5-mini"
            synthesis_model_name = "GPT-5.2"
        else:
            base_provider = AnthropicProvider(api_key=api_key)
            evidence_provider = base_provider.with_model(HAIKU_MODEL)
            synthesis_provider = base_provider.with_model(SONNET_MODEL)
            model_name = "haiku+sonnet"
            evidence_model_name = "Haiku"
            synthesis_model_name = "Sonnet"
    except ProviderError:
        raise

    # Pass 1: Evidence gathering
    _progress(PipelineStage.CHUNKING, "Chunking conversation...")
    chunks = chunk_conversation(conversation)
    logger.info(f"Created {len(chunks)} chunks")

    # Log session start
    session_logger.log_session_start(
        total_messages=len(conversation.messages),
        total_chunks=len(chunks),
        participants=participants,
    )

    _progress(PipelineStage.EVIDENCE, f"Gathering evidence with {evidence_model_name}...", 0, len(chunks))

    def chunk_progress(current: int, total: int):
        _progress(PipelineStage.EVIDENCE, f"Processing chunk {current}/{total}...", current, total)

    packets, evidence_input, evidence_output = gather_all_evidence(
        chunks, evidence_provider, chunk_progress, session_logger=session_logger
    )
    total_input_tokens += evidence_input
    total_output_tokens += evidence_output
    logger.info(f"Gathered {len(packets)} evidence packets")

    # Log pre-aggregation data
    session_logger.log_pre_aggregation(
        all_quotes=[q for p in packets for q in p.notable_quotes],
        all_jokes=[j for p in packets for j in p.inside_jokes],
        all_dynamics=[d for p in packets for d in p.dynamics],
        all_funny=[f for p in packets for f in p.funny_moments],
        all_awards=[a for p in packets for a in p.award_ideas],
        all_snippets=[s for p in packets for s in p.conversation_snippets],
        all_contradictions=[c for p in packets for c in p.contradictions],
        all_roasts=[r for p in packets for r in p.roasts],
    )

    evidence = aggregate_evidence(packets)
    logger.info(f"Aggregated: {len(evidence.notable_quotes)} quotes, {len(evidence.inside_jokes)} jokes")

    # Log post-aggregation data
    session_logger.log_post_aggregation(evidence)

    # Quality filter: Have the evidence model judge the evidence
    _progress(PipelineStage.EVIDENCE, "Filtering evidence by quality...")
    evidence, filter_input, filter_output = filter_evidence_by_quality(
        evidence, evidence_provider
    )
    total_input_tokens += filter_input
    total_output_tokens += filter_output
    logger.info(f"Quality filter: {len(evidence.notable_quotes)} quotes, {len(evidence.inside_jokes)} jokes")

    # Log post-filter data
    session_logger.log_quality_filter(evidence)

    # Pass 2: Award synthesis
    _progress(PipelineStage.SYNTHESIS, f"Generating awards with {synthesis_model_name}...")

    sample_messages = select_sample_messages(conversation, count=50)
    prompt = build_synthesis_prompt(
        stats=stats,
        patterns=patterns,
        evidence=evidence,
        sample_messages=sample_messages,
        participants=participants,
    )

    # Log the prompt sent to Sonnet
    session_logger.log_sonnet_prompt(prompt)

    awards, response, synthesis_input, synthesis_output = generate_awards(
        prompt=prompt,
        provider=synthesis_provider,
        participants=participants,
        max_retries=1,
    )
    total_input_tokens += synthesis_input
    total_output_tokens += synthesis_output

    # Log Sonnet response
    session_logger.log_sonnet_response(response or {}, awards)

    _progress(PipelineStage.COMPLETE, "Done!")

    result = UnwrappedResult(
        awards=awards,
        patterns_used=patterns,
        evidence=evidence,
        model_used=model_name,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
        success=True,
    )

    # Log final result
    session_logger.log_final_result(result)

    return result


def generate_unwrapped_offline(
    conversation: Conversation,
    stats: Statistics,
) -> UnwrappedResult:
    """Generate Unwrapped using only local pattern detection (no LLM).

    This is the fallback mode when no API key is available or when
    explicitly requested with --offline.

    Args:
        conversation: Parsed conversation
        stats: Computed statistics

    Returns:
        UnwrappedResult with pattern-based awards (no evidence)
    """
    participants = list(stats.basic.messages_per_person.keys())

    # Pass 0 only: Pattern detection
    patterns = detect_all_patterns(conversation, stats)
    logger.info(f"Detected {len(patterns)} patterns (offline mode)")

    # Convert patterns to simple awards
    awards = _create_pattern_awards(patterns, participants)

    return UnwrappedResult(
        awards=awards,
        patterns_used=patterns,
        evidence=None,
        model_used="offline",
        input_tokens=0,
        output_tokens=0,
        success=True,
    )


def generate_unwrapped_with_fallback(
    conversation: Conversation,
    stats: Statistics,
    api_key: Optional[str] = None,
    offline: bool = False,
    progress_callback: Optional[ProgressCallback] = None,
    enable_logging: bool = True,
    provider: str = PROVIDER_ANTHROPIC,
) -> UnwrappedResult:
    """Generate Unwrapped with graceful fallback on errors.

    Fallback chain:
    1. Full pipeline (evidence + synthesis models)
    2. Skip evidence gathering, use synthesis with patterns only
    3. Offline mode (pattern-based awards)

    Args:
        conversation: Parsed conversation
        stats: Computed statistics
        api_key: API key (falls back to env var based on provider)
        offline: Force offline mode
        progress_callback: Optional callback for progress updates
        enable_logging: Whether to save debug logs to logs/ directory
        provider: LLM provider to use ("anthropic" or "openai")

    Returns:
        UnwrappedResult - always succeeds, may have degraded output
    """
    def _progress(stage: PipelineStage, message: str, current: int = 0, total: int = 0):
        if progress_callback:
            progress_callback(ProgressUpdate(stage, message, current, total))

    # Force offline mode if requested
    if offline:
        logger.info("Offline mode requested")
        return generate_unwrapped_offline(conversation, stats)

    # Check for API key early based on provider
    import os
    if provider == PROVIDER_OPENAI:
        env_key = "OPENAI_API_KEY"
    else:
        env_key = "ANTHROPIC_API_KEY"

    effective_key = api_key or os.environ.get(env_key)
    if not effective_key:
        logger.warning(f"No {env_key} available, using offline mode")
        _progress(PipelineStage.PATTERNS, "No API key - using offline mode...")
        return generate_unwrapped_offline(conversation, stats)

    # Try full pipeline
    try:
        return generate_unwrapped(
            conversation=conversation,
            stats=stats,
            api_key=api_key,
            progress_callback=progress_callback,
            enable_logging=enable_logging,
            provider=provider,
        )
    except ProviderError as e:
        logger.error(f"Provider error: {e}")
        # Could be rate limit, invalid key, etc.
        # Fall back to offline
        _progress(PipelineStage.PATTERNS, f"API error: {e}. Using offline mode...")
        result = generate_unwrapped_offline(conversation, stats)
        result.error = str(e)
        return result
    except EvidenceError as e:
        logger.warning(f"Evidence gathering failed: {e}")
        # Try without evidence (synthesis model with patterns only)
        return _generate_without_evidence(
            conversation, stats, api_key, progress_callback, str(e), provider
        )
    except SynthesisError as e:
        logger.error(f"Synthesis failed: {e}")
        # Fall back to offline
        _progress(PipelineStage.PATTERNS, f"Synthesis error: {e}. Using offline mode...")
        result = generate_unwrapped_offline(conversation, stats)
        result.error = str(e)
        return result
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        # Last resort: offline mode
        result = generate_unwrapped_offline(conversation, stats)
        result.error = f"Unexpected error: {e}"
        return result


def _generate_without_evidence(
    conversation: Conversation,
    stats: Statistics,
    api_key: Optional[str],
    progress_callback: Optional[ProgressCallback],
    evidence_error: str,
    provider_name: str = PROVIDER_ANTHROPIC,
) -> UnwrappedResult:
    """Generate awards using synthesis model but without evidence.

    Used when evidence gathering fails but we still want to try synthesis.
    """
    def _progress(stage: PipelineStage, message: str, current: int = 0, total: int = 0):
        if progress_callback:
            progress_callback(ProgressUpdate(stage, message, current, total))

    participants = list(stats.basic.messages_per_person.keys())

    # Pattern detection
    _progress(PipelineStage.PATTERNS, "Detecting patterns (evidence gathering failed)...")
    patterns = detect_all_patterns(conversation, stats)

    # Try synthesis model without evidence
    try:
        if provider_name == PROVIDER_OPENAI:
            base_provider = OpenAIProvider(api_key=api_key)
            synthesis_provider = base_provider.with_model(GPT_MAIN_MODEL)
            model_name = "gpt-main-only"
        else:
            base_provider = AnthropicProvider(api_key=api_key)
            synthesis_provider = base_provider.with_model(SONNET_MODEL)
            model_name = "sonnet-only"

        _progress(PipelineStage.SYNTHESIS, "Generating awards (without evidence)...")

        sample_messages = select_sample_messages(conversation, count=50)
        prompt = build_synthesis_prompt(
            stats=stats,
            patterns=patterns,
            evidence=None,  # No evidence available
            sample_messages=sample_messages,
            participants=participants,
        )

        awards, response, input_tokens, output_tokens = generate_awards(
            prompt=prompt,
            provider=synthesis_provider,
            participants=participants,
            max_retries=1,
        )

        _progress(PipelineStage.COMPLETE, "Done (without evidence)")

        return UnwrappedResult(
            awards=awards,
            patterns_used=patterns,
            evidence=None,
            model_used=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            success=True,
            error=f"Evidence gathering failed: {evidence_error}",
        )

    except Exception as e:
        logger.error(f"Synthesis also failed: {e}")
        # Ultimate fallback
        result = generate_unwrapped_offline(conversation, stats)
        result.error = f"Evidence: {evidence_error}; Synthesis: {e}"
        return result


def _create_pattern_awards(
    patterns: list[DetectedPattern],
    participants: list[str],
) -> list[Award]:
    """Convert detected patterns to simple awards for offline mode.

    Creates awards from the top patterns without LLM creativity.
    """
    awards = []

    # Map pattern types to award titles
    title_templates = {
        "late_good_morning": "The Late Riser Award",
        "late_goodnight": "The Night Owl Award",
        "midnight_philosopher": "The Midnight Philosopher",
        "catchphrase": "The Catchphrase Champion",
        "laugh_style": "The Signature Laugh Award",
        "apology_patterns": "The Apology Artist",
        "punctuation_habits": "The Punctuation Enthusiast",
        "emoji_signature": "The Emoji Expert",
        "triple_texter": "The Triple Texter",
        "message_length_style": "The Word Count Champion",
        "initiator_imbalance": "The Conversation Starter",
        "question_asker": "The Curious One",
    }

    # Track awards per person to balance
    awards_per_person = {p: 0 for p in participants}
    max_per_person = 4

    for pattern in patterns:
        if len(awards) >= 6:
            break

        # Skip if this person already has enough awards
        if awards_per_person.get(pattern.person, 0) >= max_per_person:
            continue

        title = title_templates.get(pattern.pattern_type, f"The {pattern.pattern_type.replace('_', ' ').title()}")

        # Build evidence from pattern
        evidence = pattern.description
        if pattern.evidence and len(pattern.evidence) > 0:
            first_ev = pattern.evidence[0]
            if isinstance(first_ev, dict):
                ev_parts = [f"{k}: {v}" for k, v in list(first_ev.items())[:2]]
                evidence += f" ({', '.join(ev_parts)})"

        award = Award(
            title=title,
            recipient=pattern.person,
            evidence=evidence,
            quip="(Generated in offline mode)",
        )
        awards.append(award)
        awards_per_person[pattern.person] = awards_per_person.get(pattern.person, 0) + 1

    # If we don't have enough awards, create generic ones
    while len(awards) < 6 and participants:
        # Find person with fewest awards
        min_person = min(participants, key=lambda p: awards_per_person.get(p, 0))
        awards.append(Award(
            title="Active Participant Award",
            recipient=min_person,
            evidence="Consistently engaged in conversation",
            quip="(Generated in offline mode)",
        ))
        awards_per_person[min_person] = awards_per_person.get(min_person, 0) + 1

    return awards[:6]
