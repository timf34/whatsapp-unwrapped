"""Shared test fixtures."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def simple_1on1_path(fixtures_dir: Path) -> str:
    """Return path to simple 1-on-1 chat fixture."""
    return str(fixtures_dir / "simple_1on1.txt")


@pytest.fixture
def multiline_path(fixtures_dir: Path) -> str:
    """Return path to multiline messages fixture."""
    return str(fixtures_dir / "multiline.txt")


@pytest.fixture
def system_messages_path(fixtures_dir: Path) -> str:
    """Return path to system messages fixture."""
    return str(fixtures_dir / "system_messages.txt")


@pytest.fixture
def edge_cases_path(fixtures_dir: Path) -> str:
    """Return path to edge cases fixture."""
    return str(fixtures_dir / "edge_cases.txt")
