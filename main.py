"""Main entry point for WhatsApp Unwrapped."""

import argparse
import logging
import sys
from pathlib import Path

from analysis import run_analysis
from exceptions import WhatsAppUnwrappedError
from models import OutputPaths, Statistics
from output import render_outputs
from output.presentation import get_fun_facts
from parser import load_chat

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

    return parser.parse_args()


def print_summary(stats: Statistics, paths: OutputPaths) -> None:
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

    # Top content
    if stats.content.top_emojis:
        print()
        try:
            top_emojis = " ".join(e for e, _ in stats.content.top_emojis[:5])
            print(f"Top emojis: {top_emojis}")
        except UnicodeEncodeError:
            # Skip emoji display if console doesn't support it
            emoji_list = [f"{e}({c})" for e, c in stats.content.top_emojis[:5]]
            print(f"Top emojis: {len(stats.content.top_emojis[:5])} emojis (see JSON for details)")

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

        # Summary
        print_summary(stats, output_paths)

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


if __name__ == "__main__":
    sys.exit(main())
