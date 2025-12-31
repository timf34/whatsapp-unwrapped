"""Award generation using Sonnet LLM."""

import logging
import re
from typing import Any

from exceptions import SynthesisError
from llm.providers.base import LLMProvider, LLMResponse
from llm.synthesis.prompts import SONNET_SYSTEM_PROMPT, get_retry_prompt
from models import Award

logger = logging.getLogger(__name__)


def generate_awards(
    prompt: str,
    provider: LLMProvider,
    participants: list[str],
    max_retries: int = 1,
) -> tuple[list[Award], LLMResponse, int, int]:
    """Generate awards using Sonnet.

    Args:
        prompt: Complete synthesis prompt
        provider: LLM provider (should be Sonnet)
        participants: List of participant names for validation
        max_retries: Maximum retry attempts if validation fails

    Returns:
        Tuple of (list of Awards, final LLMResponse, total input tokens, total output tokens)

    Raises:
        SynthesisError: If generation or parsing fails after retries
    """
    total_input_tokens = 0
    total_output_tokens = 0
    last_response = None

    for attempt in range(max_retries + 1):
        try:
            # Make the API call
            if attempt == 0:
                current_prompt = prompt
            else:
                # Retry with feedback
                issues = _get_issues(awards, participants) if 'awards' in dir() else ["Failed to parse response"]
                current_prompt = prompt + "\n\n" + get_retry_prompt(issues)

            data, response = provider.complete_json(
                prompt=current_prompt,
                system=SONNET_SYSTEM_PROMPT,
                max_tokens=4096,
            )

            total_input_tokens += response.input_tokens
            total_output_tokens += response.output_tokens
            last_response = response

            # Parse awards
            awards = _parse_awards(data)

            # Validate
            issues = _get_issues(awards, participants)

            if not issues:
                # All good!
                return awards, response, total_input_tokens, total_output_tokens

            if attempt < max_retries:
                logger.warning(f"Award validation issues (attempt {attempt + 1}): {issues}")
                continue

            # Final attempt, return what we have with warning
            logger.warning(f"Award validation issues after all retries: {issues}")
            return awards, response, total_input_tokens, total_output_tokens

        except SynthesisError:
            if attempt < max_retries:
                logger.warning(f"Synthesis error on attempt {attempt + 1}, retrying...")
                continue
            raise

        except Exception as e:
            raise SynthesisError(f"Failed to generate awards: {e}")

    # Should not reach here, but just in case
    raise SynthesisError("Failed to generate awards after all attempts")


def _parse_awards(data: dict[str, Any]) -> list[Award]:
    """Parse LLM response into Award objects.

    Args:
        data: Parsed JSON from LLM

    Returns:
        List of Award objects

    Raises:
        SynthesisError: If parsing fails
    """
    # Handle both {"awards": [...]} and direct [...]
    if isinstance(data, list):
        awards_data = data
    elif isinstance(data, dict):
        awards_data = data.get("awards", [])
        if not awards_data and len(data) > 0:
            # Maybe the response is a single award or weird format
            if "title" in data:
                awards_data = [data]
    else:
        raise SynthesisError(f"Unexpected response format: {type(data)}")

    if not awards_data:
        raise SynthesisError("No awards found in response")

    awards = []
    for i, award_data in enumerate(awards_data):
        if not isinstance(award_data, dict):
            logger.warning(f"Skipping non-dict award at index {i}")
            continue

        try:
            award = Award(
                title=str(award_data.get("title", "")).strip(),
                recipient=str(award_data.get("recipient", "")).strip(),
                evidence=str(award_data.get("evidence", "")).strip(),
                quip=str(award_data.get("quip", "")).strip(),
            )

            # Basic validation
            if award.title and award.recipient:
                awards.append(award)
            else:
                logger.warning(f"Skipping award missing title or recipient: {award_data}")

        except Exception as e:
            logger.warning(f"Failed to parse award at index {i}: {e}")
            continue

    if not awards:
        raise SynthesisError("No valid awards could be parsed from response")

    return awards


def _get_issues(awards: list[Award], participants: list[str]) -> list[str]:
    """Check awards for issues.

    Args:
        awards: List of generated awards
        participants: Expected participant names

    Returns:
        List of issue descriptions (empty if all good)
    """
    issues = []

    # Check count
    if len(awards) < 6:
        issues.append(f"Only {len(awards)} awards generated, need 6")
    elif len(awards) > 6:
        issues.append(f"Generated {len(awards)} awards, should be exactly 6")

    # Check balance
    recipient_counts = {}
    for award in awards:
        recipient_counts[award.recipient] = recipient_counts.get(award.recipient, 0) + 1

    for recipient, count in recipient_counts.items():
        if count > 4:
            issues.append(f"{recipient} has {count} awards, should have 2-4")

    # Check for unknown recipients
    normalized_participants = {p.lower(): p for p in participants}
    for award in awards:
        recipient_lower = award.recipient.lower()
        if recipient_lower not in normalized_participants:
            # Try partial match
            matched = False
            for p_lower, p in normalized_participants.items():
                if recipient_lower in p_lower or p_lower in recipient_lower:
                    matched = True
                    break
            if not matched:
                issues.append(f"Unknown recipient: {award.recipient}")

    # Check for specificity (must have numbers or quotes)
    for award in awards:
        if not _has_specific_evidence(award.evidence):
            issues.append(f"Award '{award.title}' lacks specific evidence (no numbers/quotes)")

    # Check quip length
    for award in awards:
        word_count = len(award.quip.split())
        if word_count > 20:
            issues.append(f"Award '{award.title}' quip too long ({word_count} words)")

    return issues


def _has_specific_evidence(evidence: str) -> bool:
    """Check if evidence contains specific data (numbers, quotes, times).

    Args:
        evidence: Evidence string to check

    Returns:
        True if evidence appears specific
    """
    # Check for numbers
    if re.search(r'\d+', evidence):
        return True

    # Check for quoted text
    if re.search(r'["\'].*?["\']', evidence):
        return True

    # Check for time references
    if re.search(r'\d{1,2}:\d{2}|\d{1,2}(am|pm)', evidence, re.IGNORECASE):
        return True

    # Check for percentage
    if re.search(r'\d+%', evidence):
        return True

    return False


def check_award_balance(awards: list[Award], participants: list[str]) -> dict[str, int]:
    """Get award count per participant.

    Args:
        awards: List of awards
        participants: List of participant names

    Returns:
        Dict of participant -> award count
    """
    counts = {p: 0 for p in participants}

    for award in awards:
        # Try exact match first
        if award.recipient in counts:
            counts[award.recipient] += 1
        else:
            # Try case-insensitive match
            for p in participants:
                if award.recipient.lower() == p.lower():
                    counts[p] += 1
                    break
                # Try partial match (e.g., "Tim" matches "Tim Farrelly")
                if award.recipient.lower() in p.lower() or p.lower() in award.recipient.lower():
                    counts[p] += 1
                    break

    return counts
