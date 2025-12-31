"""Synthesis module for LLM-powered award generation.

This module handles Pass 2 of the Unwrapped pipeline:
- Building prompts from statistics, patterns, and evidence
- Generating awards using Sonnet
- Validating and balancing award output
"""

from llm.synthesis.builder import build_synthesis_prompt, select_sample_messages
from llm.synthesis.generator import generate_awards

__all__ = [
    "build_synthesis_prompt",
    "select_sample_messages",
    "generate_awards",
]
