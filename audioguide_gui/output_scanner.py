"""Scan AudioGuide output folders for generated files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OutputFileGroup:
	"""A named group of files discovered in an AudioGuide output directory."""

	key: str
	label: str
	files: tuple[Path, ...]


OUTPUT_GROUPS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
	("audio", "Audio render", (".aif", ".aiff", ".wav", ".wave", ".flac", ".mp3", ".m4a")),
	("csound", "Csound score", (".csd", ".sco", ".orc")),
	("html_log", "HTML/log", (".html", ".htm", ".log", ".txt")),
	("json", "JSON", (".json",)),
	("rpp", "RPP", (".rpp",)),
	("aaf", "AAF", (".aaf",)),
	(
		"bach_max",
		"Bach/Max files",
		(".bach", ".maxpat", ".maxhelp", ".maxproj", ".maxsnap", ".mxt", ".pat"),
	),
)

_GROUPS_BY_SUFFIX = {
	suffix: (key, label)
	for key, label, suffixes in OUTPUT_GROUPS
	for suffix in suffixes
}


def scan_output_directory(output_dir: str | Path) -> list[OutputFileGroup]:
	"""Return generated files in *output_dir*, grouped by AudioGuide output type."""
	root = Path(output_dir).expanduser()
	grouped: dict[str, list[Path]] = {key: [] for key, _, _ in OUTPUT_GROUPS}
	if not root.exists() or not root.is_dir():
		return [OutputFileGroup(key, label, ()) for key, label, _ in OUTPUT_GROUPS]

	for path in sorted((candidate for candidate in root.rglob("*") if candidate.is_file()), key=_sort_key):
		group = _GROUPS_BY_SUFFIX.get(path.suffix.lower())
		if group is None:
			continue
		key, _ = group
		grouped[key].append(path)

	return [
		OutputFileGroup(key, label, tuple(grouped[key]))
		for key, label, _ in OUTPUT_GROUPS
	]


def _sort_key(path: Path) -> tuple[str, str]:
	return (str(path.parent).lower(), path.name.lower())


__all__ = ["OUTPUT_GROUPS", "OutputFileGroup", "scan_output_directory"]
