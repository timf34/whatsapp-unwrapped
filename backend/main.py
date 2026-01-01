"""Main entry point for WhatsApp Unwrapped."""

import argparse
import io
import logging
import sys
from pathlib import Path
from typing import Optional

from analysis import run_analysis
from exceptions import WhatsAppUnwrappedError
from models import Conversation, OutputPaths, Statistics, UnwrappedResult
from output import render_outputs
from output.presentation import get_fun_facts
from output.unwrapped import format_unwrapped
from parser import load_chat
from dotenv import load_dotenv

load_dotenv()


class TeeOutput:
    """Captures output while still printing to terminal."""

    def __init__(self, original_stdout):
        self.original = original_stdout
        self.buffer = io.StringIO()

    def write(self, text):
        self.original.write(text)
        self.buffer.write(text)

    def flush(self):
        self.original.flush()

    def getvalue(self):
        return self.buffer.getvalue()

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def parse_cli_arguments() -> argparse.Namespace:
    """Parse and validate command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="whatsapp-unwrapped",
        description="Analyze WhatsApp chat exports and generate statistics and visualizations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py chat.txt
  python main.py chat.txt --output-dir ./results
  python main.py chat.txt --type group --gap-hours 6
        """,
    )

    parser.add_argument(
        "input_file",
        help="Path to WhatsApp chat export file (.txt)",
    )

    parser.add_argument(
        "--type",
        choices=["auto", "1-on-1", "group"],
        default="auto",
        help="Chat type: auto-detect (default), 1-on-1, or group",
    )

    parser.add_argument(
        "--output-dir",
        "-o",
        default=None,
        help="Directory for output files (default: output_data/<filename>)",
    )

    parser.add_argument(
        "--gap-hours",
        type=float,
        default=8.0,
        help="Hours of inactivity to define conversation restart (default: 4.0)",
    )

    parser.add_argument(
        "--min-phrase-freq",
        type=int,
        default=3,
        help="Minimum frequency for n-grams (default: 3)",
    )

    parser.add_argument(
        "--max-ngram",
        type=int,
        default=3,
        choices=[2, 3, 4],
        help="Maximum n-gram size (default: 3)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Only export JSON, skip visualizations",
    )

    # Unwrapped (LLM) arguments
    parser.add_argument(
        "--unwrapped",
        action="store_true",
        help="Generate AI-powered 'Unwrapped' awards (requires API key)",
    )

    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai"],
        default="anthropic",
        help="LLM provider to use: anthropic (default) or openai",
    )

    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use offline mode for Unwrapped (pattern-based awards, no LLM)",
    )

    parser.add_argument(
        "--export-frontend",
        action="store_true",
        help="Export JSON for frontend (creates {filename}_frontend.json)",
    )

    args = parser.parse_args()

    # Validate: --offline requires --unwrapped
    if args.offline and not args.unwrapped:
        parser.error("--offline requires --unwrapped")

    # Validate: --export-frontend requires --unwrapped
    if args.export_frontend and not args.unwrapped:
        parser.error("--export-frontend requires --unwrapped (for awards)")

    return args


def run_unwrapped(
    chat: Conversation,
    stats: Statistics,
    offline: bool = False,
    verbose: bool = False,
    provider: str = "anthropic",
) -> tuple[Optional[UnwrappedResult], Optional[str]]:
    """Run the Unwrapped pipeline.

    Args:
        chat: Parsed conversation
        stats: Computed statistics
        offline: Force offline mode
        verbose: Show progress
        provider: LLM provider to use ("anthropic" or "openai")

    Returns:
        Tuple of (UnwrappedResult or None, log_path or None)
    """
    from llm import generate_unwrapped_with_fallback, PipelineStage, ProgressUpdate
    from llm.orchestrator import generate_unwrapped

    print()
    if offline:
        print("Generating Unwrapped (offline mode)...")
    else:
        provider_name = "OpenAI GPT" if provider == "openai" else "Anthropic Claude"
        print(f"Generating Unwrapped with {provider_name}...")

    def progress_callback(update: ProgressUpdate) -> None:
        if not verbose:
            return
        stage_labels = {
            PipelineStage.PATTERNS: "Detecting patterns",
            PipelineStage.CHUNKING: "Chunking conversation",
            PipelineStage.EVIDENCE: "Gathering evidence",
            PipelineStage.SYNTHESIS: "Generating awards",
            PipelineStage.COMPLETE: "Complete",
        }
        label = stage_labels.get(update.stage, str(update.stage))
        if update.total > 0:
            print(f"  {label}... [{update.current}/{update.total}]")
        else:
            print(f"  {label}...")

    log_path = None
    try:
        result = generate_unwrapped_with_fallback(
            conversation=chat,
            stats=stats,
            offline=offline,
            progress_callback=progress_callback if verbose else None,
            enable_logging=not offline,  # Only log when using LLM
            provider=provider,
        )

        if result.success:
            print(f"  Generated {len(result.awards)} awards")
        else:
            print(f"  Warning: {result.error}")

        # Get log path from the most recent session
        if not offline:
            from llm.logging import get_logger
            session_logger = get_logger()
            if session_logger:
                log_path = session_logger.log_path

        return result, log_path

    except Exception as e:
        print(f"  Error generating Unwrapped: {e}")
        return None, None


def print_summary(
    stats: Statistics,
    paths: OutputPaths,
    unwrapped_result: Optional[UnwrappedResult] = None,
) -> None:
    """Print human-readable summary to console."""
    print()
    print("=" * 50)
    print("  WhatsApp Unwrapped - Analysis Complete")
    print("=" * 50)

    # Basic stats
    print()
    print("Chat Overview:")
    print(f"  Type: {stats.chat_type.value}")
    print(f"  Total messages: {stats.basic.total_messages:,}")
    print(f"  Total words: {stats.basic.total_words:,}")

    # Date range
    start = stats.temporal.first_message_date
    end = stats.temporal.last_message_date
    days = (end - start).days + 1
    print(f"  Date range: {start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')} ({days} days)")

    # Participants
    print()
    print("Messages per person:")
    for person, count in sorted(
        stats.basic.messages_per_person.items(), key=lambda x: -x[1]
    ):
        pct = (count / stats.basic.total_messages) * 100
        print(f"  {person}: {count:,} ({pct:.1f}%)")

    # Conversation patterns
    print()
    print("Conversation patterns:")
    print(f"  Conversation sessions: {stats.temporal.conversation_count}")
    print(f"  Avg messages/session: {stats.interaction.messages_per_conversation:.1f}")

    # Who initiates more
    if stats.interaction.conversation_initiators:
        top_initiator = max(
            stats.interaction.conversation_initiators.items(), key=lambda x: x[1]
        )
        print(f"  Most likely to start: {top_initiator[0]} ({top_initiator[1]} times)")

    # Response times (1-on-1 only)
    if stats.interaction.avg_response_time:
        print()
        print("Average response times:")
        for person, avg_time in stats.interaction.avg_response_time.items():
            if avg_time > 0:
                if avg_time < 60:
                    print(f"  {person}: {avg_time:.0f} minutes")
                else:
                    print(f"  {person}: {avg_time / 60:.1f} hours")

    # Top emojis (detailed display)
    if stats.content.top_emojis:
        print()
        print("Top emojis:")
        # Get max count for scaling bars
        max_count = max(c for _, c in stats.content.top_emojis[:10]) if stats.content.top_emojis else 1
        
        for emoji, count in stats.content.top_emojis[:10]:
            # Create a simple bar visualization with ASCII-safe characters
            bar_length = min(int(count / max_count * 30), 30)
            bar = "#" * bar_length
            
            try:
                print(f"  {emoji}  {bar} {count:,}")
            except (UnicodeEncodeError, UnicodeError):
                # Fallback for Windows console: show only count
                print(f"  [emoji]  {bar} {count:,}")

    # Fun facts
    print()
    print("Fun Facts:")
    facts = get_fun_facts(stats)
    for fact in facts:
        try:
            print(f"  • {fact}")
        except UnicodeEncodeError:
            # Fall back to ASCII representation for Windows console
            fact_ascii = fact.encode('ascii', 'ignore').decode('ascii')
            print(f"  • {fact_ascii}")

    # Output files
    print()
    print("Output files:")
    print(f"  Statistics: {paths.json_file}")
    if paths.visualization_files:
        print(f"  Visualizations: {len(paths.visualization_files)} charts in {Path(paths.visualization_files[0]).parent}")

    # Unwrapped results
    if unwrapped_result:
        try:
            print(format_unwrapped(unwrapped_result))
        except UnicodeEncodeError:
            # Fallback for Windows console
            from output.unwrapped import format_unwrapped_brief
            print(format_unwrapped_brief(unwrapped_result))

    print()


def main() -> int:
    """Main function to orchestrate the analysis workflow.

    Returns:
        Exit code: 0 for success, 1 for known errors, 2 for unexpected errors
    """
    args = parse_cli_arguments()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    # Capture terminal output for logging
    tee = TeeOutput(sys.stdout)
    sys.stdout = tee
    log_path = None

    try:
        # Determine output directory based on input filename
        if args.output_dir is None:
            input_path = Path(args.input_file)
            # Use the stem (filename without extension) for the output directory
            output_dir = f"output_data/{input_path.stem}"
        else:
            output_dir = args.output_dir

        # Parse
        print(f"Loading chat from {args.input_file}...")
        explicit_type = None if args.type == "auto" else args.type
        chat = load_chat(args.input_file, explicit_type)
        print(f"  Found {len(chat.messages)} messages from {len(chat.participants)} participants")

        # Analyze
        print("Running analysis...")
        stats = run_analysis(
            chat,
            gap_hours=args.gap_hours,
            min_phrase_freq=args.min_phrase_freq,
            max_ngram=args.max_ngram,
        )

        # Render
        print("Generating outputs...")
        if args.json_only:
            from output.json_export import export_json
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            json_path = export_json(stats, output_dir)
            output_paths = OutputPaths(json_file=json_path, visualization_files=[])
        else:
            output_paths = render_outputs(chat, stats, output_dir)

        # Unwrapped (if requested)
        unwrapped_result = None
        if args.unwrapped:
            unwrapped_result, log_path = run_unwrapped(
                chat, stats, offline=args.offline, verbose=args.verbose, provider=args.provider
            )

            # Re-export JSON with unwrapped results
            if unwrapped_result:
                from output.json_export import export_json
                export_json(stats, output_dir, unwrapped_result)

            # Export frontend JSON if requested
            if args.export_frontend and unwrapped_result:
                from output.frontend_export import export_frontend_json
                frontend_path = export_frontend_json(chat, stats, unwrapped_result)
                print(f"\nFrontend JSON exported: {frontend_path}")
                print("  Copy this file to frontend/public/data/ to use with the web UI")

        # Summary
        print_summary(stats, output_paths, unwrapped_result)

        # Log where session logs are saved
        if log_path:
            print(f"Session logs: {log_path}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except WhatsAppUnwrappedError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 1

    except Exception as e:
        logger.exception("Unexpected error")
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2

    finally:
        # Restore stdout and save terminal output to log
        sys.stdout = tee.original
        if log_path:
            from llm.logging import get_logger
            session_logger = get_logger()
            if session_logger:
                session_logger.log_terminal_output(tee.getvalue())


if __name__ == "__main__":
    sys.exit(main())
