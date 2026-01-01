"""Logging and debugging utilities for LLM pipeline."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from models import ConversationEvidence, EvidencePacket, UnwrappedResult


class SessionLogger:
    """Logger for a single Unwrapped generation session.

    Creates a timestamped directory with:
    - chunks/chunk_XX.json - Raw Haiku output for each chunk
    - aggregated_evidence.json - Combined evidence before/after dedup
    - sonnet_prompt.txt - Full prompt sent to Sonnet
    - sonnet_response.json - Raw Sonnet output
    - result.json - Final UnwrappedResult
    - session_info.json - Metadata about the session
    """

    def __init__(self, base_dir: str = "logs", enabled: bool = True, source_file: Optional[str] = None):
        """Initialize session logger.

        Args:
            base_dir: Base directory for logs
            enabled: Whether logging is enabled
            source_file: Path to source file (used to group logs by filename)
        """
        self.enabled = enabled
        if not enabled:
            self.session_dir = None
            return

        # Create directory structure: logs/{filename}/{timestamp}/
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if source_file:
            # Extract filename without extension
            filename_stem = Path(source_file).stem
            self.session_dir = Path(base_dir) / filename_stem / timestamp
        else:
            # Fallback to just timestamp if no source file provided
            self.session_dir = Path(base_dir) / timestamp

        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.session_dir / "chunks").mkdir(exist_ok=True)

        self.session_info = {
            "timestamp": timestamp,
            "started_at": datetime.now().isoformat(),
            "chunks_processed": 0,
            "total_chunks": 0,
        }

    def log_session_start(
        self,
        total_messages: int,
        total_chunks: int,
        participants: list[str],
    ) -> None:
        """Log session start info."""
        if not self.enabled:
            return

        self.session_info.update({
            "total_messages": total_messages,
            "total_chunks": total_chunks,
            "participants": participants,
        })
        self._save_session_info()

    def log_chunk_evidence(
        self,
        chunk_index: int,
        packet: EvidencePacket,
        raw_response: Optional[dict] = None,
    ) -> None:
        """Log evidence extracted from a single chunk."""
        if not self.enabled:
            return

        chunk_data = {
            "chunk_index": chunk_index,
            "start_idx": packet.chunk_start_idx,
            "end_idx": packet.chunk_end_idx,
            "notable_quotes": packet.notable_quotes,
            "inside_jokes": packet.inside_jokes,
            "dynamics": packet.dynamics,
            "funny_moments": packet.funny_moments,
            "style_notes": packet.style_notes,
            "award_ideas": packet.award_ideas,
            "conversation_snippets": packet.conversation_snippets,
        }

        if raw_response:
            chunk_data["raw_response"] = raw_response

        chunk_file = self.session_dir / "chunks" / f"chunk_{chunk_index:03d}.json"
        self._write_json(chunk_data, chunk_file)

        self.session_info["chunks_processed"] = chunk_index + 1
        self._save_session_info()

    def log_pre_aggregation(
        self,
        all_quotes: list,
        all_jokes: list,
        all_dynamics: list,
        all_funny: list,
        all_awards: list,
        all_snippets: list = None,
        all_contradictions: list = None,
        all_roasts: list = None,
    ) -> None:
        """Log all evidence before aggregation/deduplication."""
        if not self.enabled:
            return

        if all_snippets is None:
            all_snippets = []
        if all_contradictions is None:
            all_contradictions = []
        if all_roasts is None:
            all_roasts = []

        pre_agg = {
            "stage": "pre_aggregation",
            "counts": {
                "quotes": len(all_quotes),
                "jokes": len(all_jokes),
                "dynamics": len(all_dynamics),
                "funny_moments": len(all_funny),
                "award_ideas": len(all_awards),
                "snippets": len(all_snippets),
                "contradictions": len(all_contradictions),
                "roasts": len(all_roasts),
            },
            "all_quotes": all_quotes,
            "all_jokes": all_jokes,
            "all_dynamics": all_dynamics,
            "all_funny_moments": all_funny,
            "all_award_ideas": all_awards,
            "all_snippets": all_snippets,
            "all_contradictions": all_contradictions,
            "all_roasts": all_roasts,
        }

        self._write_json(pre_agg, self.session_dir / "pre_aggregation.json")

    def log_post_aggregation(self, evidence: ConversationEvidence) -> None:
        """Log aggregated evidence after deduplication."""
        if not self.enabled:
            return

        post_agg = {
            "stage": "post_aggregation",
            "counts": {
                "quotes": len(evidence.notable_quotes),
                "jokes": len(evidence.inside_jokes),
                "dynamics": len(evidence.dynamics),
                "funny_moments": len(evidence.funny_moments),
                "award_ideas": len(evidence.award_ideas),
                "snippets": len(evidence.conversation_snippets),
                "contradictions": len(evidence.contradictions),
                "roasts": len(evidence.roasts),
            },
            "evidence": evidence.to_dict(),
        }

        self._write_json(post_agg, self.session_dir / "post_aggregation.json")

    def log_quality_filter(self, evidence: ConversationEvidence) -> None:
        """Log evidence after quality filtering."""
        if not self.enabled:
            return

        filtered = {
            "stage": "post_quality_filter",
            "counts": {
                "quotes": len(evidence.notable_quotes),
                "jokes": len(evidence.inside_jokes),
                "dynamics": len(evidence.dynamics),
                "funny_moments": len(evidence.funny_moments),
                "award_ideas": len(evidence.award_ideas),
                "snippets": len(evidence.conversation_snippets),
                "contradictions": len(evidence.contradictions),
                "roasts": len(evidence.roasts),
            },
            "evidence": evidence.to_dict(),
        }

        self._write_json(filtered, self.session_dir / "post_quality_filter.json")

    def log_sonnet_prompt(self, prompt: str) -> None:
        """Log the full prompt sent to Sonnet."""
        if not self.enabled:
            return

        prompt_file = self.session_dir / "sonnet_prompt.txt"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)

    def log_sonnet_response(self, response: dict, awards: list) -> None:
        """Log Sonnet's raw response and parsed awards."""
        if not self.enabled:
            return

        response_data = {
            "raw_response": response,
            "parsed_awards": [a.to_dict() for a in awards],
        }
        self._write_json(response_data, self.session_dir / "sonnet_response.json")

    def log_final_result(self, result: UnwrappedResult) -> None:
        """Log the final UnwrappedResult."""
        if not self.enabled:
            return

        self._write_json(result.to_dict(), self.session_dir / "result.json")

        self.session_info["completed_at"] = datetime.now().isoformat()
        self.session_info["success"] = result.success
        self.session_info["total_input_tokens"] = result.input_tokens
        self.session_info["total_output_tokens"] = result.output_tokens
        self._save_session_info()

    def log_terminal_output(self, output: str) -> None:
        """Log the terminal output that the user sees."""
        if not self.enabled:
            return

        output_file = self.session_dir / "terminal_output.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)

    def _save_session_info(self) -> None:
        """Save session info to file."""
        if self.enabled and self.session_dir:
            self._write_json(self.session_info, self.session_dir / "session_info.json")

    def _write_json(self, data: Any, path: Path) -> None:
        """Write data to JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    @property
    def log_path(self) -> Optional[str]:
        """Get the session log directory path."""
        return str(self.session_dir) if self.session_dir else None


# Global session logger instance
_current_logger: Optional[SessionLogger] = None


def get_logger() -> Optional[SessionLogger]:
    """Get the current session logger."""
    return _current_logger


def set_logger(logger: SessionLogger) -> None:
    """Set the current session logger."""
    global _current_logger
    _current_logger = logger


def create_session_logger(enabled: bool = True) -> SessionLogger:
    """Create and set a new session logger."""
    logger = SessionLogger(enabled=enabled)
    set_logger(logger)
    return logger
