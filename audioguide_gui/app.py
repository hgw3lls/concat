"""PySide6 application and main window for the AudioGuide GUI."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
	QApplication,
	QFileDialog,
	QHBoxLayout,
	QLabel,
	QLineEdit,
	QMainWindow,
	QPlainTextEdit,
	QPushButton,
	QVBoxLayout,
	QWidget,
)

from .project import AudioGuideProject


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
		return self.path_edit.text()

	def _choose_path(self) -> None:
		if self._mode == "file":
			path, _ = QFileDialog.getOpenFileName(self, self._dialog_title)
		else:
			path = QFileDialog.getExistingDirectory(self, self._dialog_title)
		if path:
			self.path_edit.setText(path)


class MainWindow(QMainWindow):
	"""Initial AudioGuide GUI window."""

	def __init__(self):
		super().__init__()
		self.setWindowTitle("AudioGuide GUI")
		self.resize(800, 500)

		self.target_picker = PathPicker("Target sound file", "Choose target sound file", "file")
		self.corpus_picker = PathPicker("Corpus folder", "Choose corpus folder", "directory")
		self.output_picker = PathPicker("Output folder", "Choose output folder", "directory")

		self.render_button = QPushButton("Render")
		self.render_button.clicked.connect(self._render_clicked)

		self.log_output = QPlainTextEdit()
		self.log_output.setReadOnly(True)
		self.log_output.setPlaceholderText("AudioGuide GUI log output will appear here.")

		layout = QVBoxLayout()
		layout.addWidget(self.target_picker)
		layout.addWidget(self.corpus_picker)
		layout.addWidget(self.output_picker)
		layout.addWidget(self.render_button, alignment=Qt.AlignRight)
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

	def _render_clicked(self) -> None:
		project = self._project_from_inputs()
		self.log_output.appendPlainText("Render requested.")
		self.log_output.appendPlainText(f"Target sound file: {project.target_sound_file or '(not selected)'}")
		self.log_output.appendPlainText(f"Corpus folder: {project.corpus_folder or '(not selected)'}")
		self.log_output.appendPlainText(f"Output folder: {project.output_folder or '(not selected)'}")
		self.log_output.appendPlainText("Rendering is not implemented yet.")
		self.log_output.appendPlainText("")


def run() -> int:
	"""Create and run the PySide6 application."""
	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	return app.exec()
