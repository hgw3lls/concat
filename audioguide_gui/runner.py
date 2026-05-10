"""Subprocess runner for AudioGuide GUI renders.

The GUI runner deliberately invokes the public ``agConcatenate.py`` command-line
entry point instead of importing AudioGuide internals.  This keeps GUI renders
aligned with existing AudioGuide CLI behavior while providing asynchronous log
streaming and cancellation hooks for desktop front ends.
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
import os
import shutil
import signal
import subprocess
import sys
import threading
from typing import TextIO


LogCallback = Callable[[str], None]
ExitCallback = Callable[[int], None]
ErrorCallback = Callable[[str], None]


class RunnerError(RuntimeError):
	"""Raised when AudioGuide cannot be launched by the GUI runner."""


class CallbackSignal:
	"""Small signal-like callback collection used without requiring Qt imports."""

	def __init__(self) -> None:
		self._callbacks: list[Callable[..., None]] = []
		self._lock = threading.Lock()

	def connect(self, callback: Callable[..., None]) -> Callable[..., None]:
		"""Register *callback* and return it for decorator-style use."""
		with self._lock:
			self._callbacks.append(callback)
		return callback

	def disconnect(self, callback: Callable[..., None]) -> None:
		"""Remove a previously registered callback if present."""
		with self._lock:
			if callback in self._callbacks:
				self._callbacks.remove(callback)

	def emit(self, *args: object) -> None:
		"""Invoke all registered callbacks with *args*."""
		with self._lock:
			callbacks = list(self._callbacks)
		for callback in callbacks:
			callback(*args)


class AudioGuideRunner:
	"""Run ``agConcatenate.py`` asynchronously for a generated options file.

	``start()`` returns immediately with a :class:`concurrent.futures.Future`, so
	callers can launch renders from GUI code without blocking the GUI thread.  Log
	callbacks and signal-like attributes are emitted from worker threads; Qt front
	ends should forward them to the GUI thread using queued connections or their
	own signal bridge.
	"""

	_STOP_TIMEOUT_SECONDS = 5.0

	def __init__(
		self,
		options_file: str | os.PathLike[str] | None = None,
		*,
		ag_concatenate_path: str | os.PathLike[str] | None = None,
		python_executable: str | os.PathLike[str] | None = None,
		cwd: str | os.PathLike[str] | None = None,
		env: dict[str, str] | None = None,
	) -> None:
		self.options_file = Path(options_file) if options_file is not None else None
		self.ag_concatenate_path = Path(ag_concatenate_path) if ag_concatenate_path is not None else self._default_ag_concatenate_path()
		self.python_executable = str(python_executable) if python_executable is not None else sys.executable
		self.cwd = Path(cwd) if cwd is not None else self.ag_concatenate_path.parent
		self.env = env

		self.log_updated = CallbackSignal()
		self.stdout_updated = CallbackSignal()
		self.stderr_updated = CallbackSignal()
		self.finished = CallbackSignal()
		self.error = CallbackSignal()

		self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="audioguide-runner")
		self._process: subprocess.Popen[str] | None = None
		self._future: Future[int] | None = None
		self._lock = threading.Lock()
		self._cancel_requested = threading.Event()

	def add_log_callback(self, callback: LogCallback) -> LogCallback:
		"""Register a callback receiving every stdout/stderr line as text."""
		return self.log_updated.connect(callback)

	def add_stdout_callback(self, callback: LogCallback) -> LogCallback:
		"""Register a callback receiving stdout lines as text."""
		return self.stdout_updated.connect(callback)

	def add_stderr_callback(self, callback: LogCallback) -> LogCallback:
		"""Register a callback receiving stderr lines as text."""
		return self.stderr_updated.connect(callback)

	def add_finished_callback(self, callback: ExitCallback) -> ExitCallback:
		"""Register a callback receiving the subprocess exit code."""
		return self.finished.connect(callback)

	def add_error_callback(self, callback: ErrorCallback) -> ErrorCallback:
		"""Register a callback receiving launch/preflight errors as text."""
		return self.error.connect(callback)

	def start(self, options_file: str | os.PathLike[str] | None = None) -> Future[int]:
		"""Start AudioGuide in the background and return a future for its exit code."""
		with self._lock:
			if self._future is not None and not self._future.done():
				raise RunnerError("AudioGuide is already running.")
			if options_file is not None:
				self.options_file = Path(options_file)
			self._cancel_requested.clear()
			self._future = self._executor.submit(self._run)
			return self._future

	def run(self, options_file: str | os.PathLike[str] | None = None) -> Future[int]:
		"""Alias for :meth:`start` for callers that prefer runner-style naming."""
		return self.start(options_file)

	def render(self, options_file: str | os.PathLike[str] | None = None) -> Future[int]:
		"""Launch a render for an already generated options file.

		The return value is a future rather than a direct exit code to avoid blocking
		GUI callers.  Use ``future.result()`` from a worker/test thread if a blocking
		wait is required.
		"""
		return self.start(options_file)

	def wait(self, timeout: float | None = None) -> int:
		"""Wait for the current render future and return its exit code."""
		future = self._future
		if future is None:
			raise RunnerError("AudioGuide has not been started.")
		return future.result(timeout=timeout)

	def cancel(self) -> None:
		"""Request cancellation and terminate the running AudioGuide process."""
		self._cancel_requested.set()
		self.terminate()

	def terminate(self) -> None:
		"""Terminate the running AudioGuide process, killing it if needed."""
		process = self._process
		if process is None or process.poll() is not None:
			return
		self._terminate_process_tree(process)

	@property
	def is_running(self) -> bool:
		"""Return ``True`` while a subprocess future is still active."""
		future = self._future
		return future is not None and not future.done()

	def _run(self) -> int:
		try:
			options_path = self._preflight()
			command = [self.python_executable, str(self.ag_concatenate_path), str(options_path)]
			self._emit_log(f"Launching AudioGuide: {' '.join(command)}")
			process_kwargs = self._process_group_kwargs()
			process = subprocess.Popen(
				command,
				cwd=str(self.cwd),
				env=self.env,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				text=True,
				bufsize=1,
				**process_kwargs,
			)
			with self._lock:
				self._process = process

			stdout_thread = threading.Thread(target=self._stream_pipe, args=(process.stdout, self.stdout_updated), daemon=True)
			stderr_thread = threading.Thread(target=self._stream_pipe, args=(process.stderr, self.stderr_updated), daemon=True)
			stdout_thread.start()
			stderr_thread.start()

			exit_code = process.wait()
			stdout_thread.join()
			stderr_thread.join()
			self.finished.emit(exit_code)
			return exit_code
		except Exception as exc:
			message = str(exc)
			self.error.emit(message)
			self._emit_log(f"AudioGuide runner error: {message}")
			raise
		finally:
			with self._lock:
				self._process = None

	def _stream_pipe(self, pipe: TextIO | None, stream_signal: CallbackSignal) -> None:
		if pipe is None:
			return
		with pipe:
			for line in iter(pipe.readline, ""):
				text = line.rstrip("\r\n")
				stream_signal.emit(text)
				self._emit_log(text)

	def _emit_log(self, line: str) -> None:
		self.log_updated.emit(line)

	def _preflight(self) -> Path:
		if self.options_file is None:
			raise RunnerError("No AudioGuide options file was provided.")
		options_path = self.options_file.expanduser().resolve()
		if not options_path.exists():
			raise RunnerError(f'AudioGuide options file does not exist: "{options_path}"')
		if not options_path.is_file():
			raise RunnerError(f'AudioGuide options path is not a file: "{options_path}"')

		ag_path = self.ag_concatenate_path.expanduser().resolve()
		self.ag_concatenate_path = ag_path
		if not ag_path.exists():
			raise RunnerError(f'agConcatenate.py was not found: "{ag_path}"')
		if not ag_path.is_file():
			raise RunnerError(f'agConcatenate.py path is not a file: "{ag_path}"')

		if not self.python_executable or shutil.which(str(self.python_executable)) is None:
			raise RunnerError(f'Python executable was not found: "{self.python_executable}"')

		missing_inputs = self._missing_referenced_inputs(options_path)
		if missing_inputs:
			formatted = ", ".join(f'"{path}"' for path in missing_inputs)
			raise RunnerError(f"AudioGuide options file references missing input path(s): {formatted}")

		if self._options_require_csound(options_path) and shutil.which("csound") is None:
			raise RunnerError(
				"Csound executable was not found on PATH. Install csound or set "
				"CSOUND_RENDER_FILEPATH = None / CSOUND_CSD_FILEPATH = None in the generated options file."
			)
		return options_path

	def _missing_referenced_inputs(self, options_path: Path) -> list[Path]:
		paths = self._referenced_audio_paths(options_path)
		return [path for path in paths if not path.exists()]

	def _referenced_audio_paths(self, options_path: Path) -> list[Path]:
		try:
			tree = ast.parse(options_path.read_text(encoding="utf-8"), filename=str(options_path))
		except SyntaxError:
			return []
		paths: list[Path] = []
		for node in ast.walk(tree):
			if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"tsf", "csf"}:
				if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
					paths.append(Path(node.args[0].value).expanduser())
		return paths

	def _options_require_csound(self, options_path: Path) -> bool:
		try:
			tree = ast.parse(options_path.read_text(encoding="utf-8"), filename=str(options_path))
		except SyntaxError:
			return True
		assignments = self._literal_assignments(tree)
		if assignments.get("CSOUND_RENDER_FILEPATH", "__missing__") is None:
			return False
		if assignments.get("CSOUND_CSD_FILEPATH", "__missing__") is None:
			return False
		return True

	def _literal_assignments(self, tree: ast.AST) -> dict[str, object]:
		assignments: dict[str, object] = {}
		for node in ast.walk(tree):
			if not isinstance(node, (ast.Assign, ast.AnnAssign)):
				continue
			targets = node.targets if isinstance(node, ast.Assign) else [node.target]
			for target in targets:
				if isinstance(target, ast.Name) and target.id in {"CSOUND_RENDER_FILEPATH", "CSOUND_CSD_FILEPATH"}:
					try:
						assignments[target.id] = ast.literal_eval(node.value)
					except (ValueError, TypeError):
						pass
		return assignments

	def _terminate_process_tree(self, process: subprocess.Popen[str]) -> None:
		if os.name == "posix":
			try:
				os.killpg(process.pid, signal.SIGTERM)
			except ProcessLookupError:
				return
		else:
			process.terminate()
		try:
			process.wait(timeout=self._STOP_TIMEOUT_SECONDS)
		except subprocess.TimeoutExpired:
			if os.name == "posix":
				try:
					os.killpg(process.pid, signal.SIGKILL)
				except ProcessLookupError:
					return
			else:
				process.kill()

	def _process_group_kwargs(self) -> dict[str, object]:
		if os.name == "posix":
			return {"start_new_session": True}
		if os.name == "nt":
			return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
		return {}

	@staticmethod
	def _default_ag_concatenate_path() -> Path:
		return Path(__file__).resolve().parent.parent / "agConcatenate.py"
