"""Tests for AudioGuide GUI output-directory scanning."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from audioguide_gui.output_scanner import scan_output_directory


class OutputScannerTest(unittest.TestCase):
	def test_scan_output_directory_groups_known_generated_files(self):
		with TemporaryDirectory() as tmp:
			root = Path(tmp)
			for name in (
				"demo.aiff",
				"demo.csd",
				"demo-log.html",
				"demo.log",
				"demo.json",
				"demo.rpp",
				"demo.aaf",
				"demo.maxpat",
				"ignored.tmp",
			):
				(root / name).write_text("x", encoding="utf-8")
			(root / "nested").mkdir()
			(root / "nested" / "demo.bach").write_text("x", encoding="utf-8")

			groups = {group.key: group for group in scan_output_directory(root)}

			self.assertEqual([path.name for path in groups["audio"].files], ["demo.aiff"])
			self.assertEqual([path.name for path in groups["csound"].files], ["demo.csd"])
			self.assertEqual([path.name for path in groups["html_log"].files], ["demo-log.html", "demo.log"])
			self.assertEqual([path.name for path in groups["json"].files], ["demo.json"])
			self.assertEqual([path.name for path in groups["rpp"].files], ["demo.rpp"])
			self.assertEqual([path.name for path in groups["aaf"].files], ["demo.aaf"])
			self.assertEqual([path.name for path in groups["bach_max"].files], ["demo.maxpat", "demo.bach"])

	def test_scan_output_directory_handles_missing_folder(self):
		groups = scan_output_directory("/folder/that/does/not/exist")
		self.assertTrue(groups)
		self.assertTrue(all(group.files == () for group in groups))


if __name__ == "__main__":
	unittest.main()
