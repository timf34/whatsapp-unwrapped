#!/usr/bin/env python3
"""Test script for the Unwrapped orchestrator (Phase 5).

Tests the complete pipeline with progress callbacks.

Usage:
    python test_orchestrator.py [--offline]

Requires ANTHROPIC_API_KEY environment variable for full mode.
"""

import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from parser import load_chat
from analysis import run_analysis
from llm import (
    generate_unwrapped_with_fallback,
    PipelineStage,
    ProgressUpdate,
)


def progress_callback(update: ProgressUpdate):
    """Print progress updates."""
    stage_icons = {
        PipelineStage.PATTERNS: "🔍",
        PipelineStage.CHUNKING: "✂️",
        PipelineStage.EVIDENCE: "📝",
        PipelineStage.SYNTHESIS: "✨",
        PipelineStage.COMPLETE: "✅",
    }
    icon = stage_icons.get(update.stage, "•")

    if update.total > 0:
        print(f"  {icon} {update.message} [{update.current}/{update.total}]")
    else:
        print(f"  {icon} {update.message}")


def main():
    offline_mode = "--offline" in sys.argv

    print("=" * 60)
    print("WHATSAPP UNWRAPPED - ORCHESTRATOR TEST")
    print("=" * 60)

    if offline_mode:
        print("Mode: OFFLINE (no LLM calls)")
    else:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            print(f"Mode: FULL PIPELINE (API key: {api_key[:12]}...)")
        else:
            print("Mode: OFFLINE (no API key found)")
    print()

    # Load conversation
    print("Loading conversation...")
    conversation = load_chat("sample_conversation.txt")
    print(f"  Loaded {len(conversation.messages)} messages")

    # Run analysis
    print("\nRunning analysis...")
    stats = run_analysis(conversation)
    participants = list(stats.basic.messages_per_person.keys())
    print(f"  Participants: {', '.join(participants)}")

    # Generate unwrapped
    print("\nGenerating Unwrapped...")
    print("-" * 40)

    result = generate_unwrapped_with_fallback(
        conversation=conversation,
        stats=stats,
        offline=offline_mode,
        progress_callback=progress_callback,
    )

    print("-" * 40)

    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    print(f"\nSuccess: {result.success}")
    print(f"Model: {result.model_used}")
    if result.error:
        print(f"Error: {result.error}")
    print(f"Patterns detected: {len(result.patterns_used)}")
    print(f"Awards generated: {len(result.awards)}")
    print(f"Tokens: {result.input_tokens:,} in / {result.output_tokens:,} out")

    # Show awards
    print("\n" + "=" * 60)
    print("AWARDS")
    print("=" * 60)

    for i, award in enumerate(result.awards, 1):
        print(f"\n{i}. {award.title}")
        print(f"   Recipient: {award.recipient}")
        print(f"   Evidence: {award.evidence}")
        print(f"   Quip: {award.quip}")

    # Show award balance
    print("\n" + "-" * 40)
    print("Award Balance:")
    balance = {}
    for award in result.awards:
        balance[award.recipient] = balance.get(award.recipient, 0) + 1
    for person, count in sorted(balance.items()):
        print(f"  {person}: {count} awards")

    # Show evidence if available
    if result.evidence:
        print("\n" + "=" * 60)
        print("QUALITATIVE INSIGHTS (from Haiku)")
        print("=" * 60)

        if result.evidence.notable_quotes:
            print("\nNotable Quotes:")
            for q in result.evidence.notable_quotes[:5]:
                person = q.get("person", "?")
                quote = q.get("quote", "?")
                # Handle both old "why_notable" and new "punchline" field names
                punchline = q.get("punchline", q.get("why_notable", ""))
                print(f"  • {person}: \"{quote}\"")
                if punchline:
                    print(f"    ({punchline})")

        if result.evidence.inside_jokes:
            print("\nInside Jokes:")
            for j in result.evidence.inside_jokes[:5]:
                ref = j.get("reference", "?")
                # Handle both old "context" and new "punchline" field names
                punchline = j.get("punchline", j.get("context", ""))
                print(f"  • \"{ref}\"")
                if punchline:
                    print(f"    {punchline}")

        if result.evidence.funny_moments:
            print("\nFunny Moments:")
            for f in result.evidence.funny_moments[:5]:
                desc = f.get("description", "?")
                print(f"  • {desc}")

        if result.evidence.dynamics:
            print("\nRelationship Dynamics:")
            for d in result.evidence.dynamics[:3]:
                print(f"  • {d}")

    # Token usage summary
    if result.input_tokens > 0:
        print("\n" + "=" * 60)
        print("TOKEN USAGE")
        print("=" * 60)
        print(f"  Input tokens:  {result.input_tokens:,}")
        print(f"  Output tokens: {result.output_tokens:,}")

        # Cost estimate
        if result.model_used == "haiku+sonnet":
            # Rough split: assume 85% Haiku input, 15% Sonnet input
            haiku_in = int(result.input_tokens * 0.85)
            sonnet_in = result.input_tokens - haiku_in
            haiku_out = int(result.output_tokens * 0.85)
            sonnet_out = result.output_tokens - haiku_out

            haiku_cost = (haiku_in * 0.25 + haiku_out * 1.25) / 1_000_000
            sonnet_cost = (sonnet_in * 3 + sonnet_out * 15) / 1_000_000
            print(f"\n  Estimated cost: ~${haiku_cost + sonnet_cost:.4f}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
