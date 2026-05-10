"""Command-line entry point for the AudioGuide desktop GUI."""

from .app import run


def main() -> int:
	"""Launch the AudioGuide GUI application."""
	return run()
