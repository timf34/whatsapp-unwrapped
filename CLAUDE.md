# WhatsApp Unwrapped - Claude Context

## Project Overview
Python CLI tool for analyzing WhatsApp chat exports. See DESIGN.md for full specification.

## Code Style Preferences
- Python 3.10+
- Type hints on all public functions
- Dataclasses for models (not dicts)
- Small, composable functions over monoliths
- Consistent naming: parse_*, compute_*, render_*
- Private functions prefixed with _
- Docstrings on public APIs only

## Architecture Rules
- NEVER mix concerns: parser doesn't know about stats, stats don't know about output
- main.py stays thin - just orchestration
- Data flows one direction: parse → analyze → output
- No circular dependencies
- Each module returns data, doesn't mutate global state

## Don't Do This
- Don't pass around Dict[str, Any] - use explicit dataclasses
- Don't make huge monolithic functions
- Don't put business logic in main.py
- Don't make parser handle statistics
- Don't make output renderer parse files

## Testing Expectations
- Minimal but meaningful tests
- Test public APIs, not every private function
- Focus on "does the pipeline work end-to-end?"
- Use small test fixtures (10-50 messages)

## My Context
- Comfortable with Python, object-oriented design
- Want clean, maintainable, discoverable code
- Plan to extend this later (LLM analysis, web UI)
- This is v1 - keep scope tight