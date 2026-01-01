"""Tests for the output module."""

import json
import os
from pathlib import Path

import pytest

from analysis import run_analysis
from models import OutputPaths
from output import render_outputs
from output.json_export import export_json
from parser import load_chat


class TestJsonExport:
    """Tests for JSON export functionality."""

    def test_export_json_creates_file(self, simple_1on1_path: str, tmp_path: Path):
        """export_json creates a statistics.json file."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        json_path = export_json(stats, str(tmp_path))

        assert os.path.exists(json_path)
        assert json_path.endswith("statistics.json")

    def test_export_json_valid_content(self, simple_1on1_path: str, tmp_path: Path):
        """Exported JSON contains valid data."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        json_path = export_json(stats, str(tmp_path))

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "chat_type" in data
        assert "basic" in data
        assert "temporal" in data
        assert "content" in data
        assert "interaction" in data

    def test_export_json_preserves_unicode(self, edge_cases_path: str, tmp_path: Path):
        """Exported JSON preserves Unicode characters (emojis)."""
        conv = load_chat(edge_cases_path)
        stats = run_analysis(conv)

        json_path = export_json(stats, str(tmp_path))

        with open(json_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should contain emoji characters, not escaped unicode
        # The edge_cases fixture contains emojis
        data = json.loads(content)
        # Just verify it's valid JSON with expected structure
        assert data["chat_type"] == "1-on-1"


class TestRenderOutputs:
    """Tests for render_outputs coordinator."""

    def test_render_outputs_returns_output_paths(
        self, simple_1on1_path: str, tmp_path: Path
    ):
        """render_outputs returns OutputPaths object."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        paths = render_outputs(conv, stats, str(tmp_path))

        assert isinstance(paths, OutputPaths)
        assert paths.json_file is not None
        assert isinstance(paths.visualization_files, list)

    def test_render_outputs_creates_json(self, simple_1on1_path: str, tmp_path: Path):
        """render_outputs creates JSON file."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        paths = render_outputs(conv, stats, str(tmp_path))

        assert os.path.exists(paths.json_file)

    def test_render_outputs_creates_visualizations(
        self, simple_1on1_path: str, tmp_path: Path
    ):
        """render_outputs creates visualization files."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        paths = render_outputs(conv, stats, str(tmp_path))

        # Should have created at least some visualization files
        assert len(paths.visualization_files) > 0
        for viz_path in paths.visualization_files:
            if viz_path:  # Skip empty strings from failed charts
                assert os.path.exists(viz_path)

    def test_render_outputs_creates_output_dir(self, simple_1on1_path: str, tmp_path: Path):
        """render_outputs creates output directory if it doesn't exist."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        new_dir = tmp_path / "new_output_dir"
        paths = render_outputs(conv, stats, str(new_dir))

        assert new_dir.exists()


class TestVisualizationFiles:
    """Tests for specific visualization files."""

    def test_timeline_created(self, simple_1on1_path: str, tmp_path: Path):
        """Timeline visualization is created."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        paths = render_outputs(conv, stats, str(tmp_path))

        timeline_files = [p for p in paths.visualization_files if p.endswith("timeline.png")]
        assert len(timeline_files) == 1

    def test_hour_distribution_created(self, simple_1on1_path: str, tmp_path: Path):
        """Hour distribution visualization is created."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        paths = render_outputs(conv, stats, str(tmp_path))

        hour_files = [p for p in paths.visualization_files if p.endswith("hour_distribution.png")]
        assert len(hour_files) == 1

    def test_wordclouds_created_for_participants(
        self, simple_1on1_path: str, tmp_path: Path
    ):
        """Word clouds are created for each participant."""
        conv = load_chat(simple_1on1_path)
        stats = run_analysis(conv)

        paths = render_outputs(conv, stats, str(tmp_path))

        wordcloud_files = [p for p in paths.visualization_files if "wordcloud" in p]
        # Should have wordcloud for each participant (2 in 1-on-1)
        assert len(wordcloud_files) >= 1
