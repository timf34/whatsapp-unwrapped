"""Content analysis statistics."""

import re
from collections import Counter, defaultdict

import emoji

from models import ContentStats, Conversation

# Common English stopwords (minimal set for efficiency)
STOPWORDS = frozenset([
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "this", "that", "these",
    "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their", "what", "which",
    "who", "when", "where", "why", "how", "all", "each", "every", "both",
    "few", "more", "most", "other", "some", "such", "no", "not", "only",
    "same", "so", "than", "too", "very", "just", "also", "now", "here",
    "there", "then", "if", "about", "into", "through", "during", "before",
    "after", "above", "below", "up", "down", "out", "off", "over", "under",
    "again", "further", "once", "any", "am", "being", "because", "until",
    "while", "get", "got", "like", "yeah", "yes", "no", "ok", "okay", "oh",
    "im", "dont", "cant", "wont", "youre", "thats", "its", "ive", "ill",
    "haha", "hahaha", "lol", "omg", "gonna", "wanna", "gotta",
])

# Pattern to clean text for word extraction
WORD_PATTERN = re.compile(r"[a-zA-Z]+")


def compute_content_metrics(
    conv: Conversation, min_phrase_freq: int = 3, max_ngram: int = 3
) -> ContentStats:
    """Analyze message content.

    Args:
        conv: Parsed conversation
        min_phrase_freq: Minimum frequency for n-grams to be included
        max_ngram: Maximum n-gram size (2-4)

    Returns:
        ContentStats with word, n-gram, and emoji statistics
    """
    top_words = _extract_top_words(conv, limit=20)
    top_words_per_person = _extract_top_words_per_person(conv, limit=15)
    top_ngrams = _extract_ngrams(conv, min_phrase_freq, max_ngram)
    top_emojis = _extract_emojis(conv, limit=15)
    top_emojis_per_person = _extract_emojis_per_person(conv, limit=10)
    longest_messages = _extract_longest_messages(conv, limit=5)

    return ContentStats(
        top_words=top_words,
        top_words_per_person=top_words_per_person,
        top_ngrams=top_ngrams,
        top_emojis=top_emojis,
        top_emojis_per_person=top_emojis_per_person,
        longest_messages=longest_messages,
    )


def _extract_top_words(conv: Conversation, limit: int = 20) -> list[tuple[str, int]]:
    """Extract most common words with stopword filtering."""
    counter: Counter[str] = Counter()
    for msg in conv.messages:
        if msg.sender and not msg.is_system and not msg.is_media:
            words = _tokenize(msg.text)
            counter.update(words)
    return counter.most_common(limit)


def _extract_top_words_per_person(
    conv: Conversation, limit: int = 15
) -> dict[str, list[tuple[str, int]]]:
    """Extract top words for each participant."""
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for msg in conv.messages:
        if msg.sender and not msg.is_system and not msg.is_media:
            words = _tokenize(msg.text)
            counters[msg.sender].update(words)
    return {person: counter.most_common(limit) for person, counter in counters.items()}


def _tokenize(text: str) -> list[str]:
    """Tokenize text into words, filtering stopwords and short words."""
    # Extract only alphabetic words
    words = WORD_PATTERN.findall(text.lower())
    # Filter stopwords and very short words
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def _extract_ngrams(
    conv: Conversation, min_freq: int, max_n: int
) -> dict[int, list[tuple[str, int]]]:
    """Extract n-grams (2-grams through max_n-grams)."""
    result: dict[int, list[tuple[str, int]]] = {}

    # Collect all tokenized messages
    all_words: list[list[str]] = []
    for msg in conv.messages:
        if msg.sender and not msg.is_system and not msg.is_media:
            words = _tokenize(msg.text)
            if words:
                all_words.append(words)

    # Generate n-grams for each n from 2 to max_n
    for n in range(2, max_n + 1):
        counter: Counter[str] = Counter()
        for words in all_words:
            if len(words) >= n:
                for i in range(len(words) - n + 1):
                    ngram = " ".join(words[i : i + n])
                    counter[ngram] += 1

        # Filter by minimum frequency
        filtered = [(ng, count) for ng, count in counter.most_common(30) if count >= min_freq]
        result[n] = filtered[:15]  # Keep top 15

    return result


def _extract_emojis(conv: Conversation, limit: int = 15) -> list[tuple[str, int]]:
    """Extract most used emojis."""
    counter: Counter[str] = Counter()
    for msg in conv.messages:
        if msg.sender and not msg.is_system:
            emojis = _get_emojis(msg.text)
            counter.update(emojis)
    return counter.most_common(limit)


def _extract_emojis_per_person(
    conv: Conversation, limit: int = 10
) -> dict[str, list[tuple[str, int]]]:
    """Extract top emojis for each participant."""
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for msg in conv.messages:
        if msg.sender and not msg.is_system:
            emojis = _get_emojis(msg.text)
            counters[msg.sender].update(emojis)
    return {person: counter.most_common(limit) for person, counter in counters.items()}


def _get_emojis(text: str) -> list[str]:
    """Extract full emoji sequences from text (handles multi-codepoint emojis)."""
    return [item["emoji"] for item in emoji.emoji_list(text)]


def _extract_longest_messages(conv: Conversation, limit: int = 5) -> list[dict[str, any]]:
    """Extract longest messages by word count.
    
    Args:
        conv: Parsed conversation
        limit: Number of longest messages to return
        
    Returns:
        List of dicts with message info (sender, timestamp, word_count, text)
    """
    message_data = []
    
    for msg in conv.messages:
        if msg.sender and not msg.is_system and not msg.is_media and msg.text.strip():
            words = msg.text.split()
            word_count = len(words)
            
            # Only include messages with at least 10 words
            if word_count >= 10:
                message_data.append({
                    "sender": msg.sender,
                    "timestamp": msg.timestamp.isoformat(),
                    "word_count": word_count,
                    "text": msg.text[:500]  # Truncate very long messages for JSON
                })
    
    # Sort by word count descending and return top N
    message_data.sort(key=lambda x: x["word_count"], reverse=True)
    return message_data[:limit]
