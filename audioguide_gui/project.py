"""Project state used by the AudioGuide GUI."""

from dataclasses import dataclass


@dataclass
class AudioGuideProject:
	"""Minimal project settings collected by the first GUI version."""

	target_sound_file: str = ""
	corpus_folder: str = ""
	output_folder: str = ""
