"""Tests for the built-in GUI tutorial content."""

from pathlib import Path
import unittest

from audioguide_gui.tutorial import TUTORIAL_SECTIONS, render_tutorial_html


class TutorialContentTest(unittest.TestCase):
	def test_tutorial_html_contains_workflow_sections(self):
		html = render_tutorial_html()
		self.assertIn("AudioGuide GUI Tutorial", html)
		self.assertIn("Choose source and output paths", html)
		self.assertIn("Render and review outputs", html)
		self.assertIn("Save reusable projects", html)

	def test_markdown_tutorial_covers_embedded_sections(self):
		document = Path("docs/GUI_TUTORIAL.md").read_text(encoding="utf-8")
		for section in TUTORIAL_SECTIONS:
			self.assertIn(f"## {section.title}", document)


if __name__ == "__main__":
	unittest.main()
