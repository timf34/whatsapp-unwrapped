"""Evidence gathering module for LLM-powered analysis.

This module handles Pass 1 of the Unwrapped pipeline:
- Chunking conversations for LLM processing
- Extracting qualitative evidence using Haiku
- Aggregating evidence across chunks
"""

from llm.evidence.chunking import ConversationChunk, chunk_conversation
from llm.evidence.gathering import gather_evidence_from_chunk, gather_all_evidence
from llm.evidence.aggregation import aggregate_evidence
from llm.evidence.quality_filter import filter_evidence_by_quality

__all__ = [
    "ConversationChunk",
    "chunk_conversation",
    "gather_evidence_from_chunk",
    "gather_all_evidence",
    "aggregate_evidence",
    "filter_evidence_by_quality",
]
