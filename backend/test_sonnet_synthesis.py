#!/usr/bin/env python3
"""Test script for Sonnet synthesis (Phase 4).

This tests the complete Pass 2 pipeline:
1. Build synthesis prompt from stats, patterns, evidence, and sample messages
2. Call Sonnet to generate 6 awards
3. Validate and display results

Usage:
    python test_sonnet_synthesis.py

Requires ANTHROPIC_API_KEY environment variable.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from parser import load_chat
from analysis import run_analysis
from analysis.pattern_detection import detect_all_patterns
from llm.providers import AnthropicProvider, SONNET_MODEL
from llm.evidence import chunk_conversation, gather_all_evidence, aggregate_evidence
from llm.synthesis import build_synthesis_prompt, select_sample_messages, generate_awards


def main():
    # Load and parse conversation
    print("Loading conversation...")
    conversation = load_chat("sample_conversation.txt")
    print(f"  Loaded {len(conversation.messages)} messages")

    # Compute statistics
    print("\nComputing statistics...")
    stats = run_analysis(conversation)
    participants = list(stats.basic.messages_per_person.keys())
    print(f"  Participants: {', '.join(participants)}")

    # Detect patterns (Pass 0)
    print("\nDetecting patterns (Pass 0)...")
    patterns = detect_all_patterns(conversation, stats)
    print(f"  Found {len(patterns)} patterns")
    for p in patterns[:5]:
        print(f"    - {p.pattern_type} ({p.person}): {p.strength:.0%}")

    # Create provider
    print("\nInitializing Anthropic provider...")
    try:
        provider = AnthropicProvider()
        haiku_provider = provider  # Default is Haiku
        sonnet_provider = provider.with_model(SONNET_MODEL)
        print(f"  Using Sonnet model: {SONNET_MODEL}")
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  Make sure ANTHROPIC_API_KEY is set in your environment or .env file")
        return

    # Gather evidence (Pass 1) - optional, can skip for quick testing
    print("\nGathering evidence with Haiku (Pass 1)...")
    chunks = chunk_conversation(conversation)
    print(f"  Created {len(chunks)} chunks")

    def progress_callback(current, total):
        print(f"  Processing chunk {current}/{total}...")

    packets, haiku_input_tokens, haiku_output_tokens = gather_all_evidence(
        chunks, haiku_provider, progress_callback
    )
    print(f"  Gathered {len(packets)} evidence packets")
    print(f"  Haiku tokens: {haiku_input_tokens:,} input, {haiku_output_tokens:,} output")

    evidence = aggregate_evidence(packets)
    print(f"  Aggregated: {len(evidence.notable_quotes)} quotes, {len(evidence.inside_jokes)} jokes")

    # Select sample messages
    print("\nSelecting sample messages...")
    sample_messages = select_sample_messages(conversation, count=15)
    print(f"  Selected {len(sample_messages)} samples")

    # Build synthesis prompt
    print("\nBuilding synthesis prompt...")
    prompt = build_synthesis_prompt(
        stats=stats,
        patterns=patterns,
        evidence=evidence,
        sample_messages=sample_messages,
        participants=participants,
    )
    print(f"  Prompt length: {len(prompt):,} characters (~{len(prompt)//4:,} tokens)")

    # Show prompt preview
    print("\n" + "="*60)
    print("PROMPT PREVIEW (first 1500 chars):")
    print("="*60)
    print(prompt[:1500])
    print("..." if len(prompt) > 1500 else "")
    print("="*60)

    # Generate awards (Pass 2)
    print("\nGenerating awards with Sonnet (Pass 2)...")
    print("  (This may take 10-30 seconds)")

    awards, response, sonnet_input_tokens, sonnet_output_tokens = generate_awards(
        prompt=prompt,
        provider=sonnet_provider,
        participants=participants,
        max_retries=1,
    )

    print(f"  Generated {len(awards)} awards")
    print(f"  Sonnet tokens: {sonnet_input_tokens:,} input, {sonnet_output_tokens:,} output")

    # Display awards
    print("\n" + "="*60)
    print("GENERATED AWARDS")
    print("="*60)

    for i, award in enumerate(awards, 1):
        print(f"\n{i}. {award.title}")
        print(f"   Recipient: {award.recipient}")
        print(f"   Evidence: {award.evidence}")
        print(f"   Quip: {award.quip}")

    # Show balance
    print("\n" + "="*60)
    print("AWARD BALANCE")
    print("="*60)
    from llm.synthesis.generator import check_award_balance
    balance = check_award_balance(awards, participants)
    for person, count in balance.items():
        print(f"  {person}: {count} awards")

    # Token summary
    print("\n" + "="*60)
    print("TOKEN USAGE SUMMARY")
    print("="*60)
    total_input = haiku_input_tokens + sonnet_input_tokens
    total_output = haiku_output_tokens + sonnet_output_tokens
    print(f"  Haiku:  {haiku_input_tokens:,} in / {haiku_output_tokens:,} out")
    print(f"  Sonnet: {sonnet_input_tokens:,} in / {sonnet_output_tokens:,} out")
    print(f"  Total:  {total_input:,} in / {total_output:,} out")

    # Rough cost estimate (as of late 2024)
    # Haiku: $0.25/1M input, $1.25/1M output
    # Sonnet: $3/1M input, $15/1M output
    haiku_cost = (haiku_input_tokens * 0.25 + haiku_output_tokens * 1.25) / 1_000_000
    sonnet_cost = (sonnet_input_tokens * 3 + sonnet_output_tokens * 15) / 1_000_000
    print(f"\n  Estimated cost: ~${haiku_cost + sonnet_cost:.4f}")
    print(f"    (Haiku: ${haiku_cost:.4f}, Sonnet: ${sonnet_cost:.4f})")


if __name__ == "__main__":
    main()
