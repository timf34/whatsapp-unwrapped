# WhatsApp Unwrapped - TODO

## Phase 1: Project Setup
- [ ] Create `whatsapp_unwrapped/` package directory
- [ ] Create `__init__.py` files for all subpackages (parser, analysis, output, utils)
- [ ] Create empty module files as placeholders
- [ ] Fix requirements.txt (remove anthropic/jinja2/plotly, add wordcloud/emoji)
- [ ] Create requirements-dev.txt (pytest, pytest-cov)
- [ ] Create tests/ directory structure
- [ ] Create tests/conftest.py with shared fixtures
- [ ] Create tests/fixtures/ directory
- [ ] Update .gitignore (add output/, .mypy_cache/, *.egg-info/)
- [ ] Implement base exceptions in exceptions.py
- [ ] Verify venv and install dependencies
- [ ] Run pytest to verify setup (0 tests should pass)

## Phase 2: Data Models & Parser

### 2.1 Data Models
- [ ] Implement ChatType enum
- [ ] Implement Message dataclass (with is_deleted field)
- [ ] Implement Conversation dataclass
- [ ] Add to_dict() methods for JSON serialization

### 2.2 Format Utilities
- [ ] Define timestamp regex pattern (DD/MM/YYYY, HH:MM)
- [ ] Implement is_message_start()
- [ ] Implement parse_timestamp()
- [ ] Define SYSTEM_MESSAGE_PATTERNS constant
- [ ] Define DELETED_MESSAGE_PATTERNS constant
- [ ] Implement is_system_message()
- [ ] Implement validate_format()

### 2.3 Text Utilities
- [ ] Implement extract_mentions() with Unicode handling
- [ ] Implement detect_links()
- [ ] Implement is_media_placeholder()
- [ ] Implement is_deleted_message()

### 2.4 Chat Parser
- [ ] Implement _read_file() with UTF-8/BOM handling
- [ ] Implement _parse_messages() with multi-line support
- [ ] Implement _parse_single_line()
- [ ] Implement _detect_chat_type()
- [ ] Implement _build_conversation()
- [ ] Implement load_chat() main entry point

### 2.5 Parser Tests
- [ ] Create test fixtures from user's WhatsApp export
- [ ] test_load_simple_1on1()
- [ ] test_load_simple_group()
- [ ] test_multiline_messages()
- [ ] test_system_messages_detected()
- [ ] test_deleted_messages_detected()
- [ ] test_media_detected()
- [ ] test_mentions_extracted()
- [ ] test_links_detected()
- [ ] test_invalid_format_raises()
- [ ] test_file_not_found_raises()

### 2.6 Package Exports
- [ ] Update whatsapp_unwrapped/__init__.py exports
- [ ] Update whatsapp_unwrapped/parser/__init__.py exports

## Phase 3: Analysis Engine
- [ ] Implement Statistics dataclass hierarchy (BasicStats, TemporalStats, etc.)
- [ ] Implement run_analysis() coordinator
- [ ] Implement basic stats (counts, averages)
- [ ] Implement temporal stats (dates, hours, weekdays)
- [ ] Implement content stats (words, n-grams, emojis)
- [ ] Implement interaction stats (response times, mentions)
- [ ] Write analysis tests

## Phase 4: Output Renderer
- [ ] Implement OutputPaths dataclass
- [ ] Implement render_outputs() coordinator
- [ ] Implement JSON export
- [ ] Implement timeline visualization
- [ ] Implement hour heatmap
- [ ] Implement weekday chart
- [ ] Implement word clouds
- [ ] Implement emoji chart
- [ ] Implement phrase chart
- [ ] Implement group-specific charts
- [ ] Write output tests

## Phase 5: CLI & Integration
- [ ] Implement main.py entry point
- [ ] Implement argument parsing
- [ ] Implement print_summary()
- [ ] Error handling
- [ ] Integration test (full pipeline)
- [ ] Write comprehensive README
- [ ] Manual testing on real exports

## Phase 6: Polish
- [ ] Add logging
- [ ] Performance testing
- [ ] Code review for consistency
- [ ] Documentation review
