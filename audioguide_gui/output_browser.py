"""Output-directory scanning and browser widgets for the AudioGuide GUI."""

from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
	QApplication,
	QHBoxLayout,
	QLabel,
	QPushButton,
	QTreeWidget,
	QTreeWidgetItem,
	QVBoxLayout,
	QWidget,
)

from .output_scanner import OUTPUT_GROUPS, OutputFileGroup, scan_output_directory


def reveal_path(path: str | Path) -> None:
	"""Reveal *path* in the platform file manager where possible."""
	resolved = Path(path).expanduser()
	if sys.platform == "darwin":
		subprocess.Popen(["open", "-R", str(resolved)])
	elif os.name == "nt":
		subprocess.Popen(["explorer", f"/select,{resolved}"])
	else:
		folder = resolved if resolved.is_dir() else resolved.parent
		subprocess.Popen(["xdg-open", str(folder)])


def open_path(path: str | Path) -> bool:
	"""Open *path* with the default desktop application."""
	return QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).expanduser())))


class OutputBrowserPanel(QWidget):
	"""Panel that lists generated output files and common file actions."""

	def __init__(self, parent: QWidget | None = None):
		super().__init__(parent)
		self._output_dir: Path | None = None

		self.status_label = QLabel("Render output files will appear here after a successful render.")
		self.tree = QTreeWidget()
		self.tree.setHeaderLabels(["Generated file", "Path"])
		self.tree.itemSelectionChanged.connect(self._update_action_state)
		self.tree.itemDoubleClicked.connect(self._open_selected)

		self.reveal_button = QPushButton("Reveal in Finder")
		self.reveal_button.clicked.connect(self._reveal_selected)
		self.open_button = QPushButton("Open file")
		self.open_button.clicked.connect(self._open_selected)
		self.copy_button = QPushButton("Copy path")
		self.copy_button.clicked.connect(self._copy_selected_path)

		button_layout = QHBoxLayout()
		button_layout.addWidget(self.reveal_button)
		button_layout.addWidget(self.open_button)
		button_layout.addWidget(self.copy_button)
		button_layout.addStretch(1)

		layout = QVBoxLayout(self)
		layout.addWidget(self.status_label)
		layout.addWidget(self.tree, stretch=1)
		layout.addLayout(button_layout)
		self._update_action_state()

	def scan(self, output_dir: str | Path) -> None:
		"""Scan *output_dir* and refresh the displayed output-file groups."""
		self._output_dir = Path(output_dir).expanduser()
		groups = scan_output_directory(self._output_dir)
		self.tree.clear()

		file_count = 0
		for group in groups:
			parent = QTreeWidgetItem([f"{group.label} ({len(group.files)})", ""])
			parent.setData(0, Qt.ItemDataRole.UserRole, "")
			self.tree.addTopLevelItem(parent)
			for file_path in group.files:
				file_count += 1
				item = QTreeWidgetItem([file_path.name, str(file_path)])
				item.setData(0, Qt.ItemDataRole.UserRole, str(file_path))
				parent.addChild(item)
			parent.setExpanded(bool(group.files))

		self.tree.resizeColumnToContents(0)
		self.status_label.setText(
			f"Found {file_count} generated file{'s' if file_count != 1 else ''} in {self._output_dir}."
		)
		self._update_action_state()

	def clear(self) -> None:
		"""Clear the browser back to its initial state."""
		self._output_dir = None
		self.tree.clear()
		self.status_label.setText("Render output files will appear here after a successful render.")
		self._update_action_state()

	def selected_path(self) -> Path | None:
		"""Return the currently selected generated file path, if any."""
		item = self.tree.currentItem()
		if item is None:
			return None
		path_text = item.data(0, Qt.ItemDataRole.UserRole)
		if not path_text:
			return None
		return Path(path_text)

	def _update_action_state(self) -> None:
		has_selection = self.selected_path() is not None
		self.reveal_button.setEnabled(has_selection)
		self.open_button.setEnabled(has_selection)
		self.copy_button.setEnabled(has_selection)

	def _reveal_selected(self, *_args: object) -> None:
		path = self.selected_path()
		if path is not None:
			reveal_path(path)

	def _open_selected(self, *_args: object) -> None:
		path = self.selected_path()
		if path is not None:
			open_path(path)

	def _copy_selected_path(self, *_args: object) -> None:
		path = self.selected_path()
		if path is not None:
			QApplication.clipboard().setText(str(path))


__all__ = [
	"OUTPUT_GROUPS",
	"OutputBrowserPanel",
	"OutputFileGroup",
	"open_path",
	"reveal_path",
	"scan_output_directory",
]
