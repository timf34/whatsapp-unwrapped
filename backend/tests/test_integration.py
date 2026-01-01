"""Integration tests for the full pipeline."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from analysis import run_analysis
from models import ChatType, OutputPaths, Statistics
from output import render_outputs
from parser import load_chat


class TestFullPipeline:
    """End-to-end integration tests."""

    def test_full_pipeline_1on1(self, simple_1on1_path: str, tmp_path: Path):
        """Full pipeline works for 1-on-1 chat."""
        # Parse
        conv = load_chat(simple_1on1_path)
        assert conv.chat_type == ChatType.ONE_ON_ONE

        # Analyze
        stats = run_analysis(conv)
        assert isinstance(stats, Statistics)
        assert stats.basic.total_messages > 0

        # Render
        paths = render_outputs(conv, stats, str(tmp_path))
        assert isinstance(paths, OutputPaths)
        assert os.path.exists(paths.json_file)
        assert len(paths.visualization_files) > 0

    def test_full_pipeline_group(self, system_messages_path: str, tmp_path: Path):
        """Full pipeline works for group chat."""
        # Parse
        conv = load_chat(system_messages_path)
        assert conv.chat_type == ChatType.GROUP

        # Analyze
        stats = run_analysis(conv)
        assert isinstance(stats, Statistics)

        # Render
        paths = render_outputs(conv, stats, str(tmp_path))
        assert os.path.exists(paths.json_file)

    def test_json_output_is_complete(self, simple_1on1_path: str, tmp_path: Path):
        """JSON output contains all expected sections."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)
        paths = render_outputs(conv, stats, str(tmp_path))

        with open(paths.json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check all sections present
        assert "chat_type" in data
        assert "basic" in data
        assert "temporal" in data
        assert "content" in data
        assert "interaction" in data

        # Check basic stats
        assert "messages_per_person" in data["basic"]
        assert "total_messages" in data["basic"]
        assert "total_words" in data["basic"]

        # Check temporal stats
        assert "messages_by_date" in data["temporal"]
        assert "messages_by_hour" in data["temporal"]

    def test_visualization_files_exist(self, simple_1on1_path: str, tmp_path: Path):
        """All expected visualization files are created."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)
        paths = render_outputs(conv, stats, str(tmp_path))

        expected_files = [
            "timeline.png",
            "hour_distribution.png",
            "weekday_distribution.png",
            "messages_per_person.png",
        ]

        for expected in expected_files:
            matching = [p for p in paths.visualization_files if p.endswith(expected)]
            assert len(matching) == 1, f"Missing visualization: {expected}"

    def test_statistics_are_consistent(self, simple_1on1_path: str):
        """Statistics are internally consistent."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        # Total messages should match sum of per-person messages
        total_from_persons = sum(stats.basic.messages_per_person.values())
        assert stats.basic.total_messages == total_from_persons

        # All hours should be present (0-23)
        assert len(stats.temporal.messages_by_hour) == 24

        # All weekdays should be present (0-6)
        assert len(stats.temporal.messages_by_weekday) == 7


class TestCLI:
    """Tests for the command-line interface."""

    def test_cli_help(self):
        """CLI --help works."""
        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "PYTHONPATH": str(Path(__file__).parent.parent)},
        )
        assert result.returncode == 0
        assert "WhatsApp" in result.stdout or "whatsapp" in result.stdout.lower()

    def test_cli_missing_file(self):
        """CLI reports error for missing file."""
        result = subprocess.run(
            [sys.executable, "main.py", "nonexistent.txt"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "PYTHONPATH": str(Path(__file__).parent.parent)},
        )
        assert result.returncode == 1
        assert "Error" in result.stderr or "error" in result.stderr.lower()

    def test_cli_with_fixture(self, simple_1on1_path: str, tmp_path: Path):
        """CLI successfully processes a fixture file."""
        output_dir = tmp_path / "cli_output"
        result = subprocess.run(
            [
                sys.executable,
                "main.py",
                simple_1on1_path,
                "--output-dir",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "PYTHONPATH": str(Path(__file__).parent.parent)},
        )

        assert result.returncode == 0
        assert output_dir.exists()
        assert (output_dir / "statistics.json").exists()

    def test_cli_json_only(self, simple_1on1_path: str, tmp_path: Path):
        """CLI --json-only skips visualizations."""
        output_dir = tmp_path / "json_only_output"
        result = subprocess.run(
            [
                sys.executable,
                "main.py",
                simple_1on1_path,
                "--output-dir",
                str(output_dir),
                "--json-only",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
            env={**os.environ, "PYTHONPATH": str(Path(__file__).parent.parent)},
        )

        assert result.returncode == 0
        assert (output_dir / "statistics.json").exists()
        # Should not have visualizations directory or it should be empty
        viz_dir = output_dir / "visualizations"
        if viz_dir.exists():
            assert len(list(viz_dir.iterdir())) == 0


class TestEdgeCasePipeline:
    """Test pipeline with edge case inputs."""

    def test_pipeline_with_emojis(self, edge_cases_path: str, tmp_path: Path):
        """Pipeline handles emojis correctly."""
        conv = load_chat(edge_cases_path)
        stats = run_analysis(conv)
        paths = render_outputs(conv, stats, str(tmp_path))

        # Should have detected emojis
        assert len(stats.content.top_emojis) > 0

        # JSON should be valid
        with open(paths.json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data["content"]["top_emojis"]) > 0

    def test_pipeline_with_multiline(self, multiline_path: str, tmp_path: Path):
        """Pipeline handles multiline messages correctly."""
        conv = load_chat(multiline_path)
        stats = run_analysis(conv)

        # Should have parsed multi-line messages
        assert any("\n" in msg.text for msg in conv.messages)
        assert stats.basic.total_messages > 0
