"""PySide6 application and main window for the AudioGuide GUI."""

from __future__ import annotations

from concurrent.futures import Future
from pathlib import Path
import sys

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import (
	QApplication,
	QDialog,
	QDialogButtonBox,
	QFileDialog,
	QGroupBox,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QMainWindow,
	QPlainTextEdit,
	QPushButton,
	QVBoxLayout,
	QWidget,
)

from .option_builder import OptionBuilder, OptionBuilderError
from .project import AudioGuideProject, ProjectConfig
from .runner import AudioGuideRunner, RunnerError


class PathPicker(QWidget):
	"""A labeled path field with a browse button."""

	def __init__(self, label: str, dialog_title: str, mode: str, parent: QWidget | None = None):
		super().__init__(parent)
		self._dialog_title = dialog_title
		self._mode = mode

		self.label = QLabel(label)
		self.path_edit = QLineEdit()
		self.path_edit.setReadOnly(True)
		self.browse_button = QPushButton("Browse…")
		self.browse_button.clicked.connect(self._choose_path)

		layout = QHBoxLayout(self)
		layout.addWidget(self.label)
		layout.addWidget(self.path_edit, stretch=1)
		layout.addWidget(self.browse_button)

	@property
	def path(self) -> str:
		"""Return the selected path as text."""
		return self.path_edit.text().strip()

	def set_enabled(self, enabled: bool) -> None:
		"""Enable or disable editing controls for this picker."""
		self.browse_button.setEnabled(enabled)

	def _choose_path(self) -> None:
		if self._mode == "file":
			path, _ = QFileDialog.getOpenFileName(self, self._dialog_title)
		else:
			path = QFileDialog.getExistingDirectory(self, self._dialog_title)
		if path:
			self.path_edit.setText(path)


class _RunnerSignals(QObject):
	"""Qt signal bridge for runner callbacks emitted from worker threads."""

	log_updated = Signal(str)
	future_done = Signal(object)


class MainWindow(QMainWindow):
	"""AudioGuide GUI window that builds options and launches renders."""

	def __init__(self):
		super().__init__()
		self.setWindowTitle("AudioGuide GUI")
		self.resize(800, 500)

		self._option_builder = OptionBuilder()
		self._runner: AudioGuideRunner | None = None
		self._render_future: Future[int] | None = None
		self._cancel_requested = False
		self._signals = _RunnerSignals(self)
		self._signals.log_updated.connect(self._append_log)
		self._signals.future_done.connect(self._render_finished)

		self.target_picker = PathPicker("Target sound file", "Choose target sound file", "file")
		self.corpus_picker = PathPicker("Corpus folder", "Choose corpus folder", "directory")
		self.output_picker = PathPicker("Output folder", "Choose output folder", "directory")

		self.advanced_options_edit = QPlainTextEdit()
		self.advanced_options_edit.setPlaceholderText(
			"Paste raw AudioGuide option syntax here. Text is preserved verbatim and appended "
			"after generated settings."
		)

		self.preview_options_button = QPushButton("Preview Generated Options File")
		self.preview_options_button.clicked.connect(self._preview_options_clicked)
		self.save_options_button = QPushButton("Save Options File As…")
		self.save_options_button.clicked.connect(self._save_options_clicked)
		self.load_options_button = QPushButton("Load Existing Options File…")
		self.load_options_button.clicked.connect(self._load_options_clicked)

		advanced_button_layout = QHBoxLayout()
		advanced_button_layout.addWidget(self.preview_options_button)
		advanced_button_layout.addWidget(self.save_options_button)
		advanced_button_layout.addWidget(self.load_options_button)
		advanced_button_layout.addStretch(1)

		advanced_layout = QVBoxLayout()
		advanced_layout.addWidget(QLabel("Raw AudioGuide options"))
		advanced_layout.addWidget(self.advanced_options_edit, stretch=1)
		advanced_layout.addLayout(advanced_button_layout)

		self.advanced_options_group = QGroupBox("Advanced Options")
		self.advanced_options_group.setLayout(advanced_layout)

		self.render_button = QPushButton("Render")
		self.render_button.clicked.connect(self._render_clicked)
		self.cancel_button = QPushButton("Cancel")
		self.cancel_button.setEnabled(False)
		self.cancel_button.clicked.connect(self._cancel_clicked)

		button_layout = QHBoxLayout()
		button_layout.addStretch(1)
		button_layout.addWidget(self.cancel_button)
		button_layout.addWidget(self.render_button)

		self.log_output = QPlainTextEdit()
		self.log_output.setReadOnly(True)
		self.log_output.setPlaceholderText("AudioGuide GUI log output will appear here.")

		layout = QVBoxLayout()
		layout.addWidget(self.target_picker)
		layout.addWidget(self.corpus_picker)
		layout.addWidget(self.output_picker)
		layout.addWidget(self.advanced_options_group, stretch=1)
		layout.addLayout(button_layout)
		layout.addWidget(QLabel("Log output"))
		layout.addWidget(self.log_output, stretch=1)

		container = QWidget()
		container.setLayout(layout)
		self.setCentralWidget(container)

	def _project_from_inputs(self) -> AudioGuideProject:
		return AudioGuideProject(
			target_sound_file=self.target_picker.path,
			corpus_folder=self.corpus_picker.path,
			output_folder=self.output_picker.path,
		)

	def _config_from_inputs(self) -> ProjectConfig:
		project = self._project_from_inputs()
		config = project.to_config()
		config.extra_options_text = self.advanced_options_edit.toPlainText()
		return config

	def _preview_options_clicked(self) -> None:
		try:
			options_text = self._option_builder.build(self._config_from_inputs())
		except (OptionBuilderError, ValueError) as exc:
			self._append_log(f"Cannot preview options file: {exc}")
			return

		dialog = QDialog(self)
		dialog.setWindowTitle("Preview Generated Options File")
		dialog.resize(700, 500)

		preview_edit = QPlainTextEdit(dialog)
		preview_edit.setReadOnly(True)
		preview_edit.setPlainText(options_text)

		buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, dialog)
		buttons.rejected.connect(dialog.reject)

		layout = QVBoxLayout(dialog)
		layout.addWidget(preview_edit)
		layout.addWidget(buttons)
		dialog.exec()

	def _save_options_clicked(self) -> None:
		path, _ = QFileDialog.getSaveFileName(
			self,
			"Save AudioGuide options file",
			"audioguide-options.py",
			"Python files (*.py);;All files (*)",
		)
		if not path:
			return

		try:
			written_path = self._option_builder.build_file(self._config_from_inputs(), path)
		except (OptionBuilderError, OSError, ValueError) as exc:
			self._append_log(f"Cannot save options file: {exc}")
			return
		self._append_log(f"Saved options file: {written_path}")

	def _load_options_clicked(self) -> None:
		path, _ = QFileDialog.getOpenFileName(
			self,
			"Load AudioGuide options file",
			"",
			"Python files (*.py);;All files (*)",
		)
		if not path:
			return

		try:
			options_text = Path(path).read_text(encoding="utf-8")
		except OSError as exc:
			self._append_log(f"Cannot load options file: {exc}")
			return

		self.advanced_options_edit.setPlainText(options_text)
		self._append_log(f"Loaded raw options text: {path}")

	def _render_clicked(self) -> None:
		if self._runner is not None and self._runner.is_running:
			self._append_log("Render is already running.")
			return

		self.log_output.clear()
		try:
			config = self._config_from_inputs()
			self._validate_config(config)
			options_path = self._options_path_for_config(config)
			self._option_builder.build_file(config, options_path)
		except (OptionBuilderError, OSError, RunnerError, ValueError) as exc:
			self._append_log(f"Cannot start render: {exc}")
			return

		self._append_log("Render requested.")
		self._append_log(f"Target sound file: {config.target_path}")
		self._append_log(f"Corpus folder: {config.corpus_paths[0]}")
		self._append_log(f"Output folder: {config.output_dir}")
		self._append_log(f"Generated options file: {options_path}")

		self._set_running_state(True)
		self._cancel_requested = False
		self._runner = AudioGuideRunner(options_path)
		self._runner.add_log_callback(self._signals.log_updated.emit)
		try:
			self._render_future = self._runner.start()
		except RunnerError as exc:
			self._append_log(f"Cannot start render: {exc}")
			self._set_running_state(False)
			return
		self._render_future.add_done_callback(self._signals.future_done.emit)

	def _cancel_clicked(self) -> None:
		if self._runner is None or not self._runner.is_running:
			return
		self._cancel_requested = True
		self.cancel_button.setEnabled(False)
		self._append_log("Cancel requested. Stopping AudioGuide…")
		self._runner.cancel()

	def _validate_config(self, config: ProjectConfig) -> None:
		target_path = Path(config.target_path).expanduser()
		if not config.target_path:
			raise ValueError("choose a target sound file")
		if not target_path.exists() or not target_path.is_file():
			raise ValueError(f'target sound file does not exist: "{target_path}"')

		if not config.corpus_paths or not config.corpus_paths[0]:
			raise ValueError("choose a corpus folder")
		corpus_path = Path(config.corpus_paths[0]).expanduser()
		if not corpus_path.exists() or not corpus_path.is_dir():
			raise ValueError(f'corpus folder does not exist: "{corpus_path}"')

		if not config.output_dir:
			raise ValueError("choose an output folder")
		output_dir = Path(config.output_dir).expanduser()
		if not output_dir.exists() or not output_dir.is_dir():
			raise ValueError(f'output folder does not exist: "{output_dir}"')

	def _options_path_for_config(self, config: ProjectConfig) -> Path:
		output_dir = Path(config.output_dir).expanduser()
		return output_dir / "audioguide-gui-options.py"

	def _set_running_state(self, is_running: bool) -> None:
		self.render_button.setEnabled(not is_running)
		self.cancel_button.setEnabled(is_running)
		self.target_picker.set_enabled(not is_running)
		self.corpus_picker.set_enabled(not is_running)
		self.output_picker.set_enabled(not is_running)
		self.advanced_options_edit.setReadOnly(is_running)
		self.preview_options_button.setEnabled(not is_running)
		self.save_options_button.setEnabled(not is_running)
		self.load_options_button.setEnabled(not is_running)

	@Slot(str)
	def _append_log(self, line: str) -> None:
		self.log_output.appendPlainText(line)

	@Slot(object)
	def _render_finished(self, future: Future[int]) -> None:
		self._set_running_state(False)
		try:
			exit_code = future.result()
		except Exception as exc:
			self._append_log(f"Render failed: {exc}")
			return

		if exit_code == 0:
			self._append_log("Render finished successfully.")
		elif self._cancel_requested:
			self._append_log(f"Render cancelled with exit code {exit_code}.")
		else:
			self._append_log(f"Render failed with exit code {exit_code}.")


def run() -> int:
	"""Create and run the PySide6 application."""
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	return app.exec()
