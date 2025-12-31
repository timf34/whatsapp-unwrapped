"""Haiku prompt templates for evidence extraction."""

from llm.evidence.chunking import ConversationChunk

# System prompt for Haiku evidence extraction
HAIKU_SYSTEM_PROMPT = """You are analyzing a WhatsApp conversation to find material for funny, affectionate "awards" - like Spotify Wrapped but for texting habits.

TONE: Write like you're telling a friend about something funny you noticed. Punchy and observational, not clinical or explanatory. Think of how friends lovingly roast each other.

CRITICAL RULES:
1. BEHAVIORAL ONLY: Describe what people DO, never speculate about feelings or WHY
   ✓ "Persistent effort to get Tim into Juicy Couture"
   ✗ "Vita jokes about wearing them despite Tim's protests; he says he finds her attractive regardless"
   The first is punchy and fun. The second explains the joke to death.

2. SPECIFICITY IS PROOF: Use exact quotes, counts, times - but make them land
   ✓ "Has texted 'sorry I'll be late' 47 times this year"
   ✗ "Apologizes a lot for lateness"

3. WRITE PUNCHLINES, NOT REPORTS:
   ✓ "Treats succulent like a dying patient, immediately outsources care to ChatGPT"
   ✗ "Shows concern for plant health and seeks AI assistance"

4. RESTRAINT: Use "slightly", "a bit", "tends to" - never superlatives like "always" or "the most"

5. AFFECTIONATE ROASTING: Friends roast each other. Look for:
   - Recurring failures they'd laugh at themselves about
   - Self-deprecating moments they've already joked about
   - Contradictions between what they say and do
   - Habits their friends would tease them about
   Keep it loving - if they'd be hurt reading it, don't include it.

6. SKIP: Anything genuinely embarrassing, private, mean-spirited, or just not that interesting

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

    return f"""Analyze this WhatsApp conversation between {participants_str}.

Find the funny, specific, shareable moments. Write observations you'd actually tell a friend.

<conversation>
{chunk.formatted_text}
</conversation>

Return JSON (include empty arrays if nothing genuinely notable):

{{
  "notable_quotes": [
    {{"person": "Name", "quote": "exact quote", "punchline": "punchy observation (not explanation)"}}
  ],
  "inside_jokes": [
    {{"reference": "the phrase", "punchline": "punchy description of what's going on"}}
  ],
  "dynamics": [
    "Punchy observation about how they interact"
  ],
  "funny_moments": [
    {{"description": "what happened - make it land"}}
  ],
  "style_notes": {{
    "PersonName": ["punchy observation about their texting style"]
  }},
  "award_ideas": [
    {{"title": "Catchy 3-6 Word Title", "recipient": "Name", "evidence": "the specific thing that proves it"}}
  ],
  "conversation_snippets": [
    {{
      "context": "brief setup (e.g. 'Tim asks ChatGPT for plant advice')",
      "exchange": [
        {{"sender": "Name", "text": "exact message 1"}},
        {{"sender": "Name", "text": "exact message 2"}},
        {{"sender": "Name", "text": "exact message 3"}}
      ],
      "punchline": "why this exchange is gold"
    }}
  ],
  "contradictions": [
    {{
      "person": "Name",
      "says": "what they claimed or said they'd do",
      "does": "what they actually did",
      "punchline": "punchy observation about the gap"
    }}
  ],
  "roasts": [
    {{
      "person": "Name",
      "roast": "affectionate roast they'd laugh at",
      "evidence": "the specific thing that proves it"
    }}
  ]
}}

ABOUT contradictions:
- When someone says they'll do X, then does the opposite
- "Says they'll fix their sleep schedule. Actual bedtime this week: 4am, 5am, 7am, 9am"
- "Claims to be organized. Has asked 'did we book flights?' 4 times"
- The humor is in the gap between intention and reality

ABOUT roasts:
- Things they'd laugh at themselves about
- Recurring mishaps, signature failures, endearing flaws
- "Phone dies so consistently it's become a personality trait"
- "Has researched restaurants in 3 countries but not booked a single reservation"
- Must be AFFECTIONATE - if they'd be hurt, don't include it

ABOUT conversation_snippets:
- Use these when the BACK-AND-FORTH is what makes it funny, not just one quote
- 2-5 messages that form a complete comedic beat
- The exchange should make sense when read as a thread
- Only include when there's genuine banter/dynamic worth preserving
- Most chunks won't have any - that's fine! Only capture truly good exchanges.

ABOUT catchphrases (look for in style_notes):
- Sentence starters they always use ("honestly", "ngl", "wait")
- Message endings ("haha", "lol", "💀")
- Verbal tics ("you know", "if that makes sense")
- Include specific counts if you notice patterns

EXAMPLES of good punchlines:
- "Persistent campaign to convert boyfriend to Juicy Couture"
- "Treats plant like dying relative, outsources care to ChatGPT"
- "Says 'good morning' exclusively after noon"
- "Triple-confirmation compliment with checkmarks"

EXAMPLES of bad (too explanatory):
- "Jokes about fashion preferences while partner disagrees"
- "Shows concern for plant health"
- "Tends to greet late in the day"

Max 3 items per category. conversation_snippets, contradictions, roasts: max 2 each. Only include genuinely funny/notable things."""


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
- conversation_snippets: Mini-exchanges (2-5 messages) where the back-and-forth IS the humor
"""
