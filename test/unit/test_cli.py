"""Test logic for our CLI module."""
from funicular import cli


def test_returns_without_error():
    """Verify nothing goes awry."""
    assert cli.main() is None
