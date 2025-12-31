"""Evidence gathering using Haiku LLM."""

import logging
from typing import Any, Callable

from exceptions import EvidenceError
from llm.evidence.chunking import ConversationChunk
from llm.evidence.prompts import HAIKU_SYSTEM_PROMPT, build_haiku_prompt
from llm.providers.base import LLMProvider, LLMResponse
from models import EvidencePacket

logger = logging.getLogger(__name__)


def gather_evidence_from_chunk(
    chunk: ConversationChunk,
    provider: LLMProvider,
) -> tuple[EvidencePacket, LLMResponse]:
    """Extract evidence from a single conversation chunk.

    Args:
        chunk: Conversation chunk to process
        provider: LLM provider (should be Haiku)

    Returns:
        Tuple of (EvidencePacket, LLMResponse)

    Raises:
        EvidenceError: If extraction or parsing fails
    """
    prompt = build_haiku_prompt(chunk)

    try:
        data, response = provider.complete_json(
            prompt=prompt,
            system=HAIKU_SYSTEM_PROMPT,
            max_tokens=2048,
        )
    except Exception as e:
        raise EvidenceError(f"Failed to get evidence from LLM: {e}")

    # Parse and validate the response
    packet = _parse_evidence_response(data)

    return packet, response


def gather_all_evidence(
    chunks: list[ConversationChunk],
    provider: LLMProvider,
    progress_callback: Callable[[int, int], None] | None = None,
) -> tuple[list[EvidencePacket], int, int]:
    """Process all chunks and gather evidence.

    Args:
        chunks: All conversation chunks
        provider: LLM provider (should be Haiku)
        progress_callback: Optional callback for progress updates (current, total)

    Returns:
        Tuple of (list of EvidencePackets, total input tokens, total output tokens)
    """
    packets: list[EvidencePacket] = []
    total_input_tokens = 0
    total_output_tokens = 0

    for i, chunk in enumerate(chunks):
        try:
            packet, response = gather_evidence_from_chunk(chunk, provider)
            packets.append(packet)
            total_input_tokens += response.input_tokens
            total_output_tokens += response.output_tokens

        except EvidenceError as e:
            # Log warning but continue with other chunks
            logger.warning(f"Failed to process chunk {i + 1}/{len(chunks)}: {e}")
            # Add empty packet to maintain chunk correspondence
            packets.append(_create_empty_packet())

        if progress_callback:
            progress_callback(i + 1, len(chunks))

    return packets, total_input_tokens, total_output_tokens


def _parse_evidence_response(data: dict[str, Any]) -> EvidencePacket:
    """Parse LLM response into EvidencePacket.

    Args:
        data: Parsed JSON from LLM

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
    )


def _create_empty_packet() -> EvidencePacket:
    """Create an empty evidence packet."""
    return EvidencePacket(
        notable_quotes=[],
        inside_jokes=[],
        dynamics=[],
        funny_moments=[],
        style_notes={},
        award_ideas=[],
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
