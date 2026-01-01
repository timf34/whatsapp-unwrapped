"""Evidence gathering using Haiku LLM."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Optional

from exceptions import EvidenceError
from llm.evidence.chunking import ConversationChunk
from llm.evidence.prompts import HAIKU_SYSTEM_PROMPT, build_haiku_prompt
from llm.providers.base import LLMProvider, LLMResponse
from models import EvidencePacket

logger = logging.getLogger(__name__)


@dataclass
class ChunkResult:
    """Result from processing a single chunk."""
    chunk_index: int
    packet: Optional[EvidencePacket]
    response: Optional[LLMResponse]
    error: Optional[str]
    raw_data: Optional[dict] = None


# Token limits for evidence gathering - start higher, retry with more if truncated
# Increased to handle both Anthropic and OpenAI models effectively
INITIAL_MAX_TOKENS = 6144
RETRY_MAX_TOKENS = 8192


def gather_evidence_from_chunk(
    chunk: ConversationChunk,
    provider: LLMProvider,
    chunk_index: int = 0,
) -> ChunkResult:
    """Extract evidence from a single conversation chunk.

    Includes retry logic for JSON truncation errors - if the response
    gets cut off, retry with higher max_tokens.

    Args:
        chunk: Conversation chunk to process
        provider: LLM provider (should be Haiku)
        chunk_index: Index of this chunk (for logging)

    Returns:
        ChunkResult with packet or error
    """
    prompt = build_haiku_prompt(chunk)

    # Try with initial token limit
    result = _try_gather_evidence(prompt, provider, chunk, chunk_index, INITIAL_MAX_TOKENS)

    # If JSON parsing failed (likely truncation), retry with higher limit
    if result.error and ("Unterminated string" in result.error or "Expecting" in result.error):
        logger.info(f"Chunk {chunk_index}: JSON truncated, retrying with higher token limit...")
        result = _try_gather_evidence(prompt, provider, chunk, chunk_index, RETRY_MAX_TOKENS)

    return result


def _try_gather_evidence(
    prompt: str,
    provider: LLMProvider,
    chunk: ConversationChunk,
    chunk_index: int,
    max_tokens: int,
) -> ChunkResult:
    """Try to gather evidence with specified token limit."""
    try:
        data, response = provider.complete_json(
            prompt=prompt,
            system=HAIKU_SYSTEM_PROMPT,
            max_tokens=max_tokens,
        )

        # Parse and validate the response
        packet = _parse_evidence_response(data, chunk.start_idx, chunk.end_idx)

        return ChunkResult(
            chunk_index=chunk_index,
            packet=packet,
            response=response,
            error=None,
            raw_data=data,
        )

    except Exception as e:
        return ChunkResult(
            chunk_index=chunk_index,
            packet=None,
            response=None,
            error=str(e),
        )


def gather_all_evidence(
    chunks: list[ConversationChunk],
    provider: LLMProvider,
    progress_callback: Callable[[int, int], None] | None = None,
    max_workers: int = 5,
    session_logger: Optional[Any] = None,
) -> tuple[list[EvidencePacket], int, int]:
    """Process all chunks and gather evidence with parallel processing.

    Args:
        chunks: All conversation chunks
        provider: LLM provider (should be Haiku)
        progress_callback: Optional callback for progress updates (current, total)
        max_workers: Maximum parallel requests (default 5 to respect rate limits)
        session_logger: Optional SessionLogger for debugging

    Returns:
        Tuple of (list of EvidencePackets, total input tokens, total output tokens)
    """
    if len(chunks) <= 3:
        # For small numbers, process sequentially
        return _gather_sequential(chunks, provider, progress_callback, session_logger)

    return _gather_parallel(chunks, provider, progress_callback, max_workers, session_logger)


def _gather_sequential(
    chunks: list[ConversationChunk],
    provider: LLMProvider,
    progress_callback: Callable[[int, int], None] | None,
    session_logger: Optional[Any],
) -> tuple[list[EvidencePacket], int, int]:
    """Process chunks sequentially (for small numbers)."""
    packets: list[EvidencePacket] = []
    total_input_tokens = 0
    total_output_tokens = 0

    for i, chunk in enumerate(chunks):
        result = gather_evidence_from_chunk(chunk, provider, i)

        if result.packet:
            packets.append(result.packet)
            if result.response:
                total_input_tokens += result.response.input_tokens
                total_output_tokens += result.response.output_tokens

            # Log to session
            if session_logger:
                session_logger.log_chunk_evidence(i, result.packet, result.raw_data)
        else:
            logger.warning(f"Failed to process chunk {i + 1}/{len(chunks)}: {result.error}")
            packets.append(_create_empty_packet(chunk.start_idx, chunk.end_idx))

        if progress_callback:
            progress_callback(i + 1, len(chunks))

    return packets, total_input_tokens, total_output_tokens


def _gather_parallel(
    chunks: list[ConversationChunk],
    provider: LLMProvider,
    progress_callback: Callable[[int, int], None] | None,
    max_workers: int,
    session_logger: Optional[Any],
) -> tuple[list[EvidencePacket], int, int]:
    """Process chunks in parallel with rate limiting."""

    results: dict[int, ChunkResult] = {}
    total_input_tokens = 0
    total_output_tokens = 0
    completed_count = 0
    count_lock = Lock()

    def process_chunk(chunk_data: tuple[int, ConversationChunk]) -> ChunkResult:
        idx, chunk = chunk_data
        return gather_evidence_from_chunk(chunk, provider, idx)

    # Process in parallel with limited workers
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_idx = {
            executor.submit(process_chunk, (i, chunk)): i
            for i, chunk in enumerate(chunks)
        }

        # Process results as they complete
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]

            try:
                result = future.result()
                results[idx] = result

                if result.response:
                    with count_lock:
                        total_input_tokens += result.response.input_tokens
                        total_output_tokens += result.response.output_tokens

            except Exception as e:
                results[idx] = ChunkResult(
                    chunk_index=idx,
                    packet=None,
                    response=None,
                    error=str(e),
                )

            # Update progress
            with count_lock:
                completed_count += 1
                if progress_callback:
                    progress_callback(completed_count, len(chunks))

    # Build ordered packet list
    packets: list[EvidencePacket] = []
    for i in range(len(chunks)):
        result = results.get(i)
        if result and result.packet:
            packets.append(result.packet)
            if session_logger:
                session_logger.log_chunk_evidence(i, result.packet, result.raw_data)
        else:
            error = result.error if result else "Unknown error"
            logger.warning(f"Failed to process chunk {i + 1}/{len(chunks)}: {error}")
            packets.append(_create_empty_packet(chunks[i].start_idx, chunks[i].end_idx))

    return packets, total_input_tokens, total_output_tokens


def _parse_evidence_response(
    data: dict[str, Any],
    start_idx: int,
    end_idx: int,
) -> EvidencePacket:
    """Parse LLM response into EvidencePacket.

    Args:
        data: Parsed JSON from LLM
        start_idx: Start message index in original conversation
        end_idx: End message index in original conversation

    Returns:
        EvidencePacket with validated data
    """
    return EvidencePacket(
        notable_quotes=_safe_list(data.get("notable_quotes")),
        inside_jokes=_safe_list(data.get("inside_jokes")),
        dynamics=_safe_string_list(data.get("dynamics")),
        funny_moments=_safe_list(data.get("funny_moments")),
        style_notes=_safe_dict_of_lists(data.get("style_notes")),
        award_ideas=_safe_list(data.get("award_ideas")),
        conversation_snippets=_safe_snippets(data.get("conversation_snippets")),
        contradictions=_safe_contradictions(data.get("contradictions")),
        roasts=_safe_list(data.get("roasts")),
        chunk_start_idx=start_idx,
        chunk_end_idx=end_idx,
    )


def _create_empty_packet(start_idx: int, end_idx: int) -> EvidencePacket:
    """Create an empty evidence packet for a chunk that failed processing."""
    return EvidencePacket(
        notable_quotes=[],
        inside_jokes=[],
        dynamics=[],
        funny_moments=[],
        style_notes={},
        award_ideas=[],
        conversation_snippets=[],
        contradictions=[],
        roasts=[],
        chunk_start_idx=start_idx,
        chunk_end_idx=end_idx,
    )


def _safe_list(value: Any) -> list[dict[str, Any]]:
    """Safely convert value to list of dicts."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _safe_string_list(value: Any) -> list[str]:
    """Safely convert value to list of strings."""
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item]


def _safe_dict_of_lists(value: Any) -> dict[str, list[str]]:
    """Safely convert value to dict of string lists."""
    if not isinstance(value, dict):
        return {}
    result = {}
    for key, val in value.items():
        if isinstance(val, list):
            result[str(key)] = [str(v) for v in val if v]
        elif val:
            result[str(key)] = [str(val)]
    return result


def _safe_snippets(value: Any) -> list[dict[str, Any]]:
    """Safely convert value to list of conversation snippets.

    Each snippet should have:
    - context: str (brief setup)
    - exchange: list of {"sender": str, "text": str}
    - punchline: str (why it's funny)
    """
    if not isinstance(value, list):
        return []

    result = []
    for item in value:
        if not isinstance(item, dict):
            continue

        # Validate snippet structure
        context = item.get("context", "")
        exchange = item.get("exchange", [])
        punchline = item.get("punchline", "")

        # Must have at least context and some exchange
        if not context or not exchange:
            continue

        # Validate exchange is a list of message dicts
        if not isinstance(exchange, list):
            continue

        valid_messages = []
        for msg in exchange:
            if isinstance(msg, dict) and msg.get("sender") and msg.get("text"):
                valid_messages.append({
                    "sender": str(msg["sender"]),
                    "text": str(msg["text"]),
                })

        # Need at least 2 messages for it to be an exchange
        if len(valid_messages) >= 2:
            result.append({
                "context": str(context),
                "exchange": valid_messages,
                "punchline": str(punchline) if punchline else "",
            })

    return result


def _safe_contradictions(value: Any) -> list[dict[str, Any]]:
    """Safely convert value to list of contradictions.

    Each contradiction should have:
    - person: str
    - says: str (what they claimed)
    - does: str (what they actually did)
    - punchline: str (why it's funny)
    """
    if not isinstance(value, list):
        return []

    result = []
    for item in value:
        if not isinstance(item, dict):
            continue

        person = item.get("person", "")
        says = item.get("says", "")
        does = item.get("does", "")
        punchline = item.get("punchline", "")

        # Must have person, says, and does
        if not person or not says or not does:
            continue

        result.append({
            "person": str(person),
            "says": str(says),
            "does": str(does),
            "punchline": str(punchline) if punchline else "",
        })

    return result
