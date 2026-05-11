"""Tests for the AudioGuide subprocess runner."""

from pathlib import Path
from tempfile import TemporaryDirectory
import textwrap
import time
import unittest
from unittest.mock import patch

from audioguide_gui.runner import AudioGuideRunner, AudioGuideToolRunner, RunnerError


class AudioGuideRunnerTest(unittest.TestCase):
	def test_runner_streams_stdout_and_stderr_and_returns_exit_code(self):
		with TemporaryDirectory() as tmp:
			root = Path(tmp)
			script = root / "fake_ag.py"
			script.write_text(
				textwrap.dedent(
					"""
					import sys

					print("stdout one", flush=True)
					print("stderr one", file=sys.stderr, flush=True)
					sys.exit(7)
					"""
				),
				encoding="utf-8",
			)
			options = root / "options.py"
			options.write_text("CSOUND_RENDER_FILEPATH = None\n", encoding="utf-8")
			logs: list[str] = []
			stdout: list[str] = []
			stderr: list[str] = []
			finished: list[int] = []

			runner = AudioGuideRunner(options, ag_concatenate_path=script)
			runner.add_log_callback(logs.append)
			runner.add_stdout_callback(stdout.append)
			runner.add_stderr_callback(stderr.append)
			runner.add_finished_callback(finished.append)

			future = runner.start()

			self.assertEqual(future.result(timeout=5), 7)
			self.assertIn("stdout one", stdout)
			self.assertIn("stderr one", stderr)
			self.assertIn("stdout one", logs)
			self.assertIn("stderr one", logs)
			self.assertEqual(finished, [7])

	def test_runner_can_cancel_running_process(self):
		with TemporaryDirectory() as tmp:
			root = Path(tmp)
			script = root / "fake_ag.py"
			script.write_text(
				textwrap.dedent(
					"""
					import time

					print("started", flush=True)
					time.sleep(30)
					"""
				),
				encoding="utf-8",
			)
			options = root / "options.py"
			options.write_text("CSOUND_RENDER_FILEPATH = None\n", encoding="utf-8")
			logs: list[str] = []

			runner = AudioGuideRunner(options, ag_concatenate_path=script)
			runner.add_log_callback(logs.append)
			future = runner.start()

			deadline = time.monotonic() + 5
			while "started" not in logs and time.monotonic() < deadline:
				time.sleep(0.01)
			runner.cancel()

			self.assertNotEqual(future.result(timeout=5), 0)

	def test_tool_runner_launches_utility_script_with_arguments(self):
		with TemporaryDirectory() as tmp:
			root = Path(tmp)
			script = root / "fake_tool.py"
			script.write_text(
				textwrap.dedent(
					"""
					import sys

					print("args=" + "|".join(sys.argv[1:]), flush=True)
					"""
				),
				encoding="utf-8",
			)
			logs: list[str] = []

			runner = AudioGuideToolRunner(script, ["-f", str(root / "out.txt"), str(root / "in.wav")])
			runner.add_log_callback(logs.append)

			future = runner.start()

			self.assertEqual(future.result(timeout=5), 0)
			self.assertIn(f"args=-f|{root / 'out.txt'}|{root / 'in.wav'}", logs)

	def test_runner_reports_missing_options_file(self):
		with TemporaryDirectory() as tmp:
			runner = AudioGuideRunner(Path(tmp) / "missing.py")
			with self.assertRaises(RunnerError) as caught:
				runner.start().result(timeout=5)
			self.assertIn("options file does not exist", str(caught.exception))

	def test_runner_reports_missing_csound_when_options_require_rendering(self):
		with TemporaryDirectory() as tmp:
			root = Path(tmp)
			script = root / "fake_ag.py"
			script.write_text("print('should not launch')\n", encoding="utf-8")
			options = root / "options.py"
			options.write_text("CSOUND_RENDER_FILEPATH = 'out.aiff'\n", encoding="utf-8")
			real_which = __import__("shutil").which

			def fake_which(command):
				if command == "csound":
					return None
				return real_which(command)

			runner = AudioGuideRunner(options, ag_concatenate_path=script)
			with patch("audioguide_gui.runner.shutil.which", side_effect=fake_which):
				with self.assertRaises(RunnerError) as caught:
					runner.start().result(timeout=5)
			self.assertIn("Csound executable was not found", str(caught.exception))


if __name__ == "__main__":
	unittest.main()
