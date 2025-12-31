"""Test script for Haiku evidence gathering.

Run with: python test_haiku_evidence.py

Requires ANTHROPIC_API_KEY environment variable to be set.
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()
key = os.environ.get("ANTHROPIC_API_KEY")
print("ANTHROPIC_API_KEY loaded:", repr(key[:12] + "..." if key else None))


sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def main():
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print()
        print("To run this test:")
        print("  1. Get an API key from https://console.anthropic.com/")
        print("  2. Set it: export ANTHROPIC_API_KEY=sk-ant-...")
        print("  3. Run again: python test_haiku_evidence.py")
        return 1

    from parser import load_chat
    from analysis import run_analysis
    from llm.evidence import chunk_conversation, gather_evidence_from_chunk, aggregate_evidence
    from llm.providers import AnthropicProvider, HAIKU_MODEL

    print("Loading sample_conversation.txt...")
    conv = load_chat("sample_conversation.txt")
    print(f"  {len(conv.messages)} messages")

    print()
    print("Chunking conversation...")
    chunks = chunk_conversation(conv)
    print(f"  {len(chunks)} chunks")

    print()
    print("Initializing Haiku provider...")
    provider = AnthropicProvider(model=HAIKU_MODEL)

    print()
    print("=" * 70)
    print("GATHERING EVIDENCE FROM CHUNK 1")
    print("=" * 70)

    # Just test on first chunk to save cost
    chunk = chunks[0]
    print(f"Processing chunk with {chunk.message_count} messages (~{chunk.token_estimate} tokens)...")
    print()

    try:
        packet, response = gather_evidence_from_chunk(chunk, provider)

        print(f"API Response:")
        print(f"  Model: {response.model}")
        print(f"  Input tokens: {response.input_tokens}")
        print(f"  Output tokens: {response.output_tokens}")
        print()

        print("Notable Quotes:")
        for q in packet.notable_quotes:
            print(f"  - {q.get('person', '?')}: \"{q.get('quote', '?')}\"")
            print(f"    Why: {q.get('why_notable', '?')}")

        print()
        print("Inside Jokes:")
        for j in packet.inside_jokes:
            print(f"  - \"{j.get('reference', '?')}\" - {j.get('context', '?')}")

        print()
        print("Dynamics:")
        for d in packet.dynamics:
            print(f"  - {d}")

        print()
        print("Funny Moments:")
        for f in packet.funny_moments:
            print(f"  - {f.get('description', '?')}")

        print()
        print("Style Notes:")
        for person, notes in packet.style_notes.items():
            print(f"  {person}:")
            for note in notes:
                print(f"    - {note}")

        print()
        print("Award Ideas:")
        for a in packet.award_ideas:
            print(f"  - \"{a.get('title', '?')}\" for {a.get('recipient', '?')}")
            print(f"    Evidence: {a.get('evidence', '?')}")

        print()
        print("=" * 70)
        print("SUCCESS! Evidence gathering is working.")
        print("=" * 70)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
