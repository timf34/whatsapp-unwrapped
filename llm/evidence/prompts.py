"""Haiku prompt templates for evidence extraction."""

from llm.evidence.chunking import ConversationChunk

# System prompt for Haiku evidence extraction
HAIKU_SYSTEM_PROMPT = """You are analyzing a WhatsApp conversation to find material for funny, affectionate "awards" - like Spotify Wrapped but for texting habits.

CRITICAL RULES:
1. BEHAVIORAL ONLY: Describe what people DO, never speculate about feelings or WHY they do it
   - Good: "Says 'does that make sense?' after explaining things"
   - Bad: "Seeks validation because they're insecure"

2. SPECIFICITY IS PROOF: Note exact quotes, counts, times when possible
   - Good: "'sorry I'll be late' appears frequently"
   - Bad: "Apologizes a lot"

3. POSITIVE FRAMING: This is a gift, not a roast. Find the endearing quirk in every pattern

4. SKIP SENSITIVE CONTENT: Don't note anything embarrassing, private, or mean-spirited

5. QUALITY OVER QUANTITY: Only note genuinely notable things, not filler

Output valid JSON only. No markdown code blocks, no explanation."""


# Expected JSON schema for evidence
EVIDENCE_SCHEMA = {
    "notable_quotes": [
        {"person": "string", "quote": "string", "why_notable": "string"}
    ],
    "inside_jokes": [
        {"reference": "string", "context": "string", "frequency_hint": "string"}
    ],
    "dynamics": ["string - short observation about how they interact"],
    "funny_moments": [
        {"description": "string", "evidence": "string"}
    ],
    "style_notes": {
        "PersonName": ["observation about their texting style"]
    },
    "award_ideas": [
        {"title": "string", "recipient": "string", "evidence": "string"}
    ]
}


def build_haiku_prompt(chunk: ConversationChunk) -> str:
    """Build the user prompt for Haiku evidence extraction.

    Args:
        chunk: Conversation chunk to analyze

    Returns:
        Formatted prompt string
    """
    # Get participant names from messages
    participants = set()
    for msg in chunk.messages:
        if msg.sender:
            participants.add(msg.sender)

    participants_str = ", ".join(sorted(participants))

    return f"""Analyze this WhatsApp conversation segment between {participants_str}.

Extract evidence for potential "awards" - funny, specific behavioral patterns.

<conversation>
{chunk.formatted_text}
</conversation>

Return JSON with these fields (include empty arrays if nothing found for a category):

{{
  "notable_quotes": [
    {{"person": "Name", "quote": "exact quote", "why_notable": "why it's funny/characteristic"}}
  ],
  "inside_jokes": [
    {{"reference": "the phrase/reference", "context": "what it seems to mean", "frequency_hint": "once/few times/recurring"}}
  ],
  "dynamics": [
    "Short observation about how they interact (max 3)"
  ],
  "funny_moments": [
    {{"description": "what happened", "evidence": "quote or timestamp"}}
  ],
  "style_notes": {{
    "{list(participants)[0] if participants else 'Person1'}": ["observation about their texting style"],
    "{list(participants)[1] if len(participants) > 1 else 'Person2'}": ["observation about their texting style"]
  }},
  "award_ideas": [
    {{"title": "Catchy Award Title", "recipient": "Name", "evidence": "specific evidence"}}
  ]
}}

IMPORTANT:
- Only include things directly observable in the text
- Max 3 items per category
- Be specific - use exact quotes and times
- Skip if nothing notable in this segment"""


def get_evidence_schema_description() -> str:
    """Get a human-readable description of the evidence schema."""
    return """
Evidence Schema:
- notable_quotes: Messages that perfectly capture someone's personality
- inside_jokes: Unusual phrases that recur and seem meaningful
- dynamics: Observable patterns in how they interact
- funny_moments: Anything that would make someone smile
- style_notes: How each person texts (per person)
- award_ideas: Suggested awards with specific evidence
"""
