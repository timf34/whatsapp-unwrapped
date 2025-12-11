# WhatsApp Unwrapped - Design Document v3

## Project Overview

**WhatsApp Unwrapped** is a Python CLI tool that analyzes WhatsApp chat exports to generate comprehensive statistics and visualizations about conversation patterns. It handles both 1-on-1 and group chats, producing detailed analytical outputs.

**Core Philosophy:**
- Single, obvious entry point with thin orchestration logic
- Clear separation: parsing → analysis → output
- Small, composable functions over large monoliths
- Explicit data models (no dict soup)
- Consistent naming conventions throughout
- Type hints and docstrings for discoverability
- Graceful handling of messy real-world input

**V1 Scope:**
- Parse WhatsApp chat exports into clean data structures
- Generate comprehensive statistics
- Create publication-quality visualizations
- Export results as JSON + PNG files
- Support both 1-on-1 and group chats

**Explicitly Out of Scope for V1:**
- HTML report generation (defer to v2)
- LLM-powered analysis (defer to v2)
- Sentiment analysis
- Real-time WhatsApp integration
- Web interface
- Multi-language support (English only for v1)

---

## Architecture Principles

### 1. Single Entry Point

The entire application flow should be visible in one place:

```python
# main.py - The only entry point
def main():
    args = parse_cli_arguments()
    
    chat = load_chat(args.input_file, args.type)
    stats = run_analysis(chat, args)
    output_paths = render_outputs(chat, stats, args.output_dir)
    
    print_summary(stats, output_paths)
```

**Key principle:** Keep `main()` thin. It should read like a recipe, with all complexity delegated to well-named functions.

### 2. Clear Module Separation

```
whatsapp-unwrapped/
├── main.py                          # Entry point (thin orchestration)
├── __init__.py
├── models.py                    # Data models (Message, Conversation)
├── parser/
│   │   ├── __init__.py
│   │   ├── chat_parser.py          # load_chat() and helpers
│   │   └── format_utils.py         # Format detection, date parsing
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── engine.py               # run_analysis() coordinator
│   │   ├── basic_stats.py          # compute_basic_stats()
│   │   ├── temporal_stats.py       # compute_temporal_patterns()
│   │   ├── content_stats.py        # compute_content_metrics()
│   │   └── interaction_stats.py    # compute_interaction_patterns()
│   ├── output/
│   │   ├── __init__.py
│   │   ├── renderer.py             # render_outputs() coordinator
│   │   ├── json_export.py          # export_json()
│   │   └── visualizations.py       # render_charts()
│   └── utils/
│       ├── __init__.py
│       ├── text_utils.py           # extract_emojis(), clean_text()
│       └── date_utils.py           # parse_timestamp(), calculate_gap()
├── tests/
│   ├── fixtures/
│   │   ├── simple_1on1.txt
│   │   └── simple_group.txt
│   ├── test_parser.py
│   ├── test_analysis.py
│   └── test_output.py
├── requirements.txt
├── README.md
└── DESIGN.md
```

**Key principle:** Each module has one clear job. Parser knows nothing about stats. Stats know nothing about rendering. Output knows nothing about parsing.

### 3. Explicit Data Models

```python
# models.py
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum

class ChatType(Enum):
    ONE_ON_ONE = "1-on-1"
    GROUP = "group"

@dataclass
class Message:
    """A single WhatsApp message."""
    id: int
    timestamp: datetime
    sender: Optional[str]  # None for system messages
    text: str
    is_system: bool = False
    is_media: bool = False
    has_link: bool = False
    mentions: List[str] = field(default_factory=list)

@dataclass
class Conversation:
    """Complete conversation with metadata."""
    messages: List[Message]
    chat_type: ChatType
    participants: List[str]
    date_range: tuple[datetime, datetime]
    source_file: str
```

**Key principle:** Use dataclasses for immutability and clarity. No passing around `Dict[str, Any]` that could contain anything.

---

## Module Specifications

### 1. Parser Module

**Purpose:** Convert raw WhatsApp `.txt` → clean `Conversation` object

**Public API:**
```python
def load_chat(filepath: str, explicit_type: Optional[str] = None) -> Conversation:
    """
    Load and parse WhatsApp chat export.
    
    Args:
        filepath: Path to .txt export file
        explicit_type: Override auto-detection ("1-on-1" or "group")
    
    Returns:
        Parsed Conversation object
    
    Raises:
        FileNotFoundError: File doesn't exist
        UnsupportedFormatError: Format not recognized
        ParseError: Malformed content
    """
```

**Internal structure:**
```python
# parser/chat_parser.py
def load_chat(filepath: str, explicit_type: Optional[str] = None) -> Conversation:
    """Main entry point."""
    lines = _read_file(filepath)
    _validate_format(lines)
    messages = _parse_messages(lines)
    chat_type = _detect_chat_type(messages) if not explicit_type else ChatType(explicit_type)
    return _build_conversation(messages, chat_type, filepath)

def _read_file(filepath: str) -> List[str]:
    """Read and validate file exists."""

def _validate_format(lines: List[str]) -> None:
    """Check if format is supported, raise UnsupportedFormatError if not."""

def _parse_messages(lines: List[str]) -> List[Message]:
    """Parse all lines into Message objects."""

def _parse_single_message(line: str, next_lines: List[str]) -> Message:
    """Parse one message, handling multi-line content."""

def _is_message_start(line: str) -> bool:
    """Check if line starts with timestamp pattern."""

def _extract_timestamp(line: str) -> datetime:
    """Parse DD/MM/YYYY, HH:MM format."""

def _extract_sender(line: str) -> Optional[str]:
    """Extract sender name, return None for system messages."""

def _is_system_message(text: str) -> bool:
    """Detect known system message patterns."""

def _extract_mentions(text: str) -> List[str]:
    """Extract @mentions from text."""

def _detect_chat_type(messages: List[Message]) -> ChatType:
    """Auto-detect based on unique sender count."""

def _build_conversation(messages: List[Message], chat_type: ChatType, source: str) -> Conversation:
    """Construct final Conversation object."""
```

**Key principles:**
- One function per logical step
- Private functions (prefixed `_`) for implementation details
- Clear error messages with context (show problematic line)
- Graceful handling of edge cases (empty lines, weird spacing, system messages)

---

### 2. Analysis Module

**Purpose:** Compute all statistics from `Conversation` object

**Public API:**
```python
def run_analysis(
    conversation: Conversation,
    gap_hours: float = 4.0,
    min_phrase_freq: int = 3,
    max_ngram: int = 3
) -> Statistics:
    """
    Compute all statistics for conversation.
    
    Args:
        conversation: Parsed conversation
        gap_hours: Hours to define conversation restart
        min_phrase_freq: Minimum frequency for n-grams
        max_ngram: Maximum n-gram size (2-4)
    
    Returns:
        Statistics object with all computed metrics
    """
```

**Internal structure:**
```python
# analysis/engine.py
def run_analysis(conversation: Conversation, **config) -> Statistics:
    """Coordinate all analysis."""
    basic = compute_basic_stats(conversation)
    temporal = compute_temporal_patterns(conversation, config['gap_hours'])
    content = compute_content_metrics(conversation, config['min_phrase_freq'], config['max_ngram'])
    interaction = compute_interaction_patterns(conversation, config['gap_hours'])
    
    return Statistics(
        chat_type=conversation.chat_type,
        basic=basic,
        temporal=temporal,
        content=content,
        interaction=interaction
    )

# analysis/basic_stats.py
def compute_basic_stats(conv: Conversation) -> Dict[str, Any]:
    """Compute message counts, word counts, averages."""
    return {
        'messages_per_person': _count_messages_per_person(conv),
        'words_per_person': _count_words_per_person(conv),
        'media_per_person': _count_media_per_person(conv),
        # ...
    }

def _count_messages_per_person(conv: Conversation) -> Dict[str, int]:
    """Count messages for each participant."""

def _count_words_per_person(conv: Conversation) -> Dict[str, int]:
    """Count words for each participant."""

# analysis/temporal_stats.py
def compute_temporal_patterns(conv: Conversation, gap_hours: float) -> Dict[str, Any]:
    """Compute time-based patterns."""
    return {
        'messages_by_date': _aggregate_by_date(conv),
        'messages_by_hour': _aggregate_by_hour(conv),
        'messages_by_weekday': _aggregate_by_weekday(conv),
        'conversation_starts': _find_conversation_starts(conv, gap_hours),
        # ...
    }

def _aggregate_by_date(conv: Conversation) -> Dict[str, int]:
    """Daily message counts."""

def _aggregate_by_hour(conv: Conversation) -> Dict[int, int]:
    """Hourly distribution (0-23)."""

def _find_conversation_starts(conv: Conversation, gap_hours: float) -> List[Message]:
    """Messages that start conversations after gaps."""

# analysis/content_stats.py
def compute_content_metrics(conv: Conversation, min_freq: int, max_ngram: int) -> Dict[str, Any]:
    """Analyze message content."""
    return {
        'top_words': _extract_top_words(conv, limit=20),
        'top_ngrams': _extract_ngrams(conv, min_freq, max_ngram),
        'top_emojis': _extract_emojis(conv, limit=10),
        # ...
    }

def _extract_top_words(conv: Conversation, limit: int) -> List[tuple[str, int]]:
    """Extract most common words with stopword filtering."""

def _extract_ngrams(conv: Conversation, min_freq: int, max_n: int) -> Dict[str, List[tuple]]:
    """Extract 2-grams, 3-grams, etc."""

def _extract_emojis(conv: Conversation, limit: int) -> List[tuple[str, int]]:
    """Extract most used emojis."""

# analysis/interaction_stats.py
def compute_interaction_patterns(conv: Conversation, gap_hours: float) -> Dict[str, Any]:
    """Analyze interaction patterns."""
    return {
        'response_times': _calculate_response_times(conv),
        'conversation_initiators': _count_initiators(conv, gap_hours),
        'mention_network': _build_mention_network(conv) if conv.chat_type == ChatType.GROUP else None,
        # ...
    }

def _calculate_response_times(conv: Conversation) -> Dict[str, List[float]]:
    """Calculate response times between participants."""

def _build_mention_network(conv: Conversation) -> Dict[str, Dict[str, int]]:
    """Build who-mentions-whom matrix for groups."""
```

**Key principles:**
- Pure functions: take data, return data (no side effects)
- Each compute function is self-contained
- Private helpers do one specific calculation
- Use descriptive names: `_count_X`, `_extract_Y`, `_calculate_Z`

---

### 3. Output Module

**Purpose:** Render analysis results as files (JSON, PNGs)

**Public API:**
```python
def render_outputs(
    conversation: Conversation,
    statistics: Statistics,
    output_dir: str
) -> OutputPaths:
    """
    Generate all output files.
    
    Args:
        conversation: Original conversation data
        statistics: Computed statistics
        output_dir: Where to save files
    
    Returns:
        OutputPaths with locations of generated files
    """

@dataclass
class OutputPaths:
    json_file: str
    visualization_files: List[str]
```

**Internal structure:**
```python
# output/renderer.py
def render_outputs(conv: Conversation, stats: Statistics, output_dir: str) -> OutputPaths:
    """Coordinate all output generation."""
    _ensure_output_dir(output_dir)
    
    json_path = export_json(stats, output_dir)
    viz_paths = render_charts(conv, stats, output_dir)
    
    return OutputPaths(json_file=json_path, visualization_files=viz_paths)

def _ensure_output_dir(path: str) -> None:
    """Create output directory if doesn't exist."""

# output/json_export.py
def export_json(stats: Statistics, output_dir: str) -> str:
    """Export statistics to JSON file."""
    output_path = f"{output_dir}/statistics.json"
    _write_json(stats.to_dict(), output_path)
    return output_path

def _write_json(data: dict, filepath: str) -> None:
    """Write dictionary to JSON file with pretty formatting."""

# output/visualizations.py
def render_charts(conv: Conversation, stats: Statistics, output_dir: str) -> List[str]:
    """Generate all visualization PNGs."""
    viz_dir = f"{output_dir}/visualizations"
    _ensure_dir(viz_dir)
    
    paths = []
    paths.append(_render_timeline(stats.temporal, viz_dir))
    paths.append(_render_hour_heatmap(stats.temporal, viz_dir))
    paths.append(_render_wordclouds(stats.content, viz_dir))
    # ... more charts
    
    return paths

def _render_timeline(temporal_data: dict, output_dir: str) -> str:
    """Create timeline chart."""

def _render_hour_heatmap(temporal_data: dict, output_dir: str) -> str:
    """Create 24-hour activity heatmap."""

def _render_wordclouds(content_data: dict, output_dir: str) -> str:
    """Create word cloud for each participant."""
```

**Key principles:**
- Each render function returns its output path
- Consistent naming: `_render_X` for chart functions
- Each chart in its own function
- Error handling: log and skip if one chart fails, don't crash entire output

---

## Consistent Naming Conventions

Throughout the codebase:

**Function prefixes:**
- `load_*` - Read/parse external data
- `compute_*` - Calculate statistics/metrics
- `render_*` - Generate output files
- `extract_*` - Pull specific data from larger structures
- `aggregate_*` - Group/summarize data
- `build_*` - Construct complex objects
- `_` prefix - Private/internal functions

**Variable names:**
- `conv` - Short for conversation
- `stats` - Short for statistics
- `msg` - Short for message
- Avoid single letters except in loops (`i`, `j`) or lambdas

**File naming:**
- `snake_case` for all Python files
- Descriptive: `temporal_stats.py` not `stats2.py`
- Group related functions in same file

---

## Data Flow Diagram

```
┌─────────────────┐
│  chat.txt file  │
└────────┬────────┘
         │
         │ load_chat()
         ▼
┌─────────────────┐
│  Conversation   │  (clean data model)
└────────┬────────┘
         │
         │ run_analysis()
         ▼
┌─────────────────┐
│   Statistics    │  (computed metrics)
└────────┬────────┘
         │
         │ render_outputs()
         ▼
┌─────────────────┐
│ JSON + PNGs     │  (files on disk)
└─────────────────┘
```

**Key principle:** Data flows in one direction. No circular dependencies. Each stage is testable independently.

---

## Error Handling Strategy

### Custom Exceptions

```python
# models.py
class WhatsAppUnwrappedError(Exception):
    """Base exception."""
    pass

class UnsupportedFormatError(WhatsAppUnwrappedError):
    """File format not recognized."""
    pass

class ParseError(WhatsAppUnwrappedError):
    """Parsing failed."""
    pass
```

### Graceful Degradation

```python
# Example: If one visualization fails, log and continue
def render_charts(conv, stats, output_dir):
    paths = []
    
    try:
        paths.append(_render_timeline(stats, output_dir))
    except Exception as e:
        logger.warning(f"Failed to render timeline: {e}")
    
    try:
        paths.append(_render_heatmap(stats, output_dir))
    except Exception as e:
        logger.warning(f"Failed to render heatmap: {e}")
    
    return paths
```

**Key principle:** Parser fails fast (bad input → clear error). Output degrades gracefully (one chart fails → others still generated).

---

## Testing Strategy

### Minimal Test Surface

**test_parser.py:**
```python
def test_parse_simple_1on1():
    """Parse a 10-message 1-on-1 chat."""
    conv = load_chat("tests/fixtures/simple_1on1.txt")
    assert len(conv.messages) == 10
    assert conv.chat_type == ChatType.ONE_ON_ONE
    assert len(conv.participants) == 2

def test_parse_handles_multiline():
    """Messages spanning multiple lines parsed correctly."""
    
def test_parse_rejects_invalid_format():
    """Unsupported format raises UnsupportedFormatError."""
```

**test_analysis.py:**
```python
def test_compute_basic_stats():
    """Basic stats computed correctly."""
    conv = _create_test_conversation(messages=50)
    stats = run_analysis(conv)
    assert stats.basic['messages_per_person']['Alice'] == 25
    assert stats.basic['messages_per_person']['Bob'] == 25

def test_temporal_aggregation():
    """Messages aggregated by date correctly."""
```

**test_output.py:**
```python
def test_render_outputs_creates_files():
    """All expected files are created."""
    conv = _create_test_conversation()
    stats = run_analysis(conv)
    paths = render_outputs(conv, stats, "/tmp/test_output")
    
    assert os.path.exists(paths.json_file)
    assert len(paths.visualization_files) > 0
```

**Key principle:** Test the public APIs. Don't test every private function. Focus on "does the pipeline work end-to-end?"

---

## CLI Design

```bash
# Basic usage
python main.py chat.txt

# With options
python main.py chat.txt --type group --output-dir ./results

# All options
python main.py <input_file> \
    --type {auto,1-on-1,group} \
    --output-dir DIR \
    --date-from YYYY-MM-DD \
    --date-to YYYY-MM-DD \
    --gap-hours FLOAT \
    --min-phrase-freq INT \
    --max-ngram INT
```

**Implementation:**
```python
# main.py
def parse_cli_arguments() -> argparse.Namespace:
    """Parse and validate command-line arguments."""

def main():
    args = parse_cli_arguments()
    
    try:
        chat = load_chat(args.input_file, args.type)
        stats = run_analysis(chat, gap_hours=args.gap_hours, ...)
        output_paths = render_outputs(chat, stats, args.output_dir)
        
        print_summary(stats, output_paths)
        
    except WhatsAppUnwrappedError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(2)

def print_summary(stats: Statistics, paths: OutputPaths) -> None:
    """Print human-readable summary to console."""
    print(f"\n✓ Analysis complete!")
    print(f"  Messages analyzed: {stats.basic['total_messages']}")
    print(f"  Date range: {stats.date_range[0]} to {stats.date_range[1]}")
    print(f"\n✓ Results saved:")
    print(f"  Statistics: {paths.json_file}")
    print(f"  Visualizations: {len(paths.visualization_files)} charts")
```

---

## Type Hints & Docstrings

**All public functions should have:**

```python
def load_chat(filepath: str, explicit_type: Optional[str] = None) -> Conversation:
    """
    Load and parse WhatsApp chat export.
    
    Args:
        filepath: Path to WhatsApp .txt export file
        explicit_type: Override auto-detection ("1-on-1" or "group"), optional
    
    Returns:
        Parsed Conversation object with messages and metadata
    
    Raises:
        FileNotFoundError: If filepath doesn't exist
        UnsupportedFormatError: If file format not recognized
        ParseError: If file is malformed
    
    Example:
        >>> conv = load_chat("my_chat.txt")
        >>> print(f"Found {len(conv.messages)} messages")
    """
```

**Private functions can be lighter:**

```python
def _count_messages_per_person(conv: Conversation) -> Dict[str, int]:
    """Count messages for each participant."""
```

**Key principle:** Public APIs get full docstrings. Internal functions get one-line descriptions. Always use type hints.

---

## Implementation Phases

### Phase 1: Parser (Day 1-2)
- [ ] Implement `models.py` (Message, Conversation dataclasses)
- [ ] Implement `parser/chat_parser.py` (load_chat + helpers)
- [ ] Implement `parser/format_utils.py` (validation, timestamps)
- [ ] Write `test_parser.py`
- [ ] CLI skeleton (argument parsing only)

**Success criteria:** Can load a .txt file and get clean Conversation object

### Phase 2: Basic Analysis (Day 3-4)
- [ ] Implement `analysis/engine.py` (run_analysis coordinator)
- [ ] Implement `analysis/basic_stats.py` (counts, averages)
- [ ] Implement `analysis/temporal_stats.py` (time patterns)
- [ ] Write `test_analysis.py`

**Success criteria:** Can compute all core statistics from Conversation

### Phase 3: Content Analysis (Day 5-6)
- [ ] Implement `analysis/content_stats.py` (words, n-grams, emojis)
- [ ] Implement `analysis/interaction_stats.py` (responses, mentions)
- [ ] Implement `utils/text_utils.py` (emoji extraction, cleaning)
- [ ] Add tests for content analysis

**Success criteria:** All statistics computed correctly

### Phase 4: Output (Day 7-8)
- [ ] Implement `output/renderer.py` (render_outputs coordinator)
- [ ] Implement `output/json_export.py` (export_json)
- [ ] Implement `output/visualizations.py` (all charts)
- [ ] Write `test_output.py`

**Success criteria:** Can generate JSON + PNG files

### Phase 5: Integration (Day 9-10)
- [ ] Complete `main.py` (wire everything together)
- [ ] Write integration test (full pipeline)
- [ ] Error handling and logging
- [ ] CLI polish (help text, validation)
- [ ] README with examples

**Success criteria:** Full end-to-end pipeline works

---

## Configuration Reference

### Supported WhatsApp Format (V1)

**Format details:**
- Date: `DD/MM/YYYY` (two digits each)
- Time: `HH:MM` (24-hour, two digits each)
- Separator: ` - ` (space-dash-space)
- Example: `10/10/2024, 14:05 - Alice: Hello world`

**Multi-line messages:**
- Continuation lines have no timestamp
- Joined with newlines: `\n`

**System messages:**
- May lack sender entirely
- Detected by pattern matching known phrases
- Kept in conversation but marked `is_system=True`

**Media:**
- Represented as `<Media omitted>`
- Creates message with `is_media=True`

**Mentions (group chats):**
- Format: `@⁨Name⁩` (special Unicode characters)
- Extracted and stored in `message.mentions` list

### Default Parameters

```python
gap_hours = 4.0          # Hours to define conversation restart
min_phrase_freq = 3      # Minimum occurrences for n-grams
max_ngram = 3            # Maximum n-gram size (2-4 supported)
```

### Output Structure

```
output/
├── statistics.json           # All computed metrics
└── visualizations/
    ├── timeline.png
    ├── hour_heatmap.png
    ├── weekday_distribution.png
    ├── wordcloud_alice.png
    ├── wordcloud_bob.png
    ├── top_emojis.png
    ├── top_phrases.png
    └── ...
```

---

## Dependencies

```
# requirements.txt
pandas>=2.0.0              # Data manipulation
matplotlib>=3.7.0          # Plotting
seaborn>=0.12.0            # Statistical visualizations
wordcloud>=1.9.0           # Word cloud generation
emoji>=2.8.0               # Emoji detection
nltk>=3.8.0                # Stopwords
python-dateutil>=2.8.0     # Date utilities
```

---

## Success Criteria

**Must Have (V1):**
- ✅ Single obvious entry point (`main.py`)
- ✅ Clear separation: parser → analysis → output
- ✅ Explicit data models (Message, Conversation, Statistics)
- ✅ Small, composable functions with clear names
- ✅ Consistent naming (parse_*, compute_*, render_*)
- ✅ Type hints on public functions
- ✅ Docstrings on public APIs
- ✅ Graceful handling of weird input (formats, system messages)
- ✅ Minimal test coverage (parser, analysis, output, integration)
- ✅ Parse standard WhatsApp exports correctly
- ✅ Compute all statistics accurately
- ✅ Generate all visualizations
- ✅ Export clean JSON

**Should Have:**
- Well-commented code where non-obvious
- Clear error messages with context
- Performance within targets (see below)

**Nice To Have (V2):**
- HTML report generation
- LLM-powered insights
- Multi-format support
- Sentiment analysis

---

## Performance Targets

- **Small chats** (<1,000 messages): <1 second
- **Medium chats** (1,000-10,000 messages): <5 seconds
- **Large chats** (10,000-100,000 messages): <30 seconds

**Optimization strategies if needed:**
- Use pandas for temporal aggregations
- Apply frequency thresholds early
- Limit word clouds to top N participants in large groups
