"""Project state used by the AudioGuide GUI."""

from dataclasses import dataclass, field


@dataclass
class ProjectConfig:
	"""Structured project settings used to generate AudioGuide options."""

	target_path: str = ""
	corpus_paths: list[str] = field(default_factory=list)
	output_dir: str = ""
	output_name: str = "output"
	render_csound: bool = True
	output_json: bool = True
	output_reaper: bool = False
	output_aaf: bool = False
	extra_options_text: str = ""


@dataclass
class AudioGuideProject:
	"""Minimal project settings collected by the first GUI version."""

	target_sound_file: str = ""
	corpus_folder: str = ""
	output_folder: str = ""

	def to_config(self) -> ProjectConfig:
		"""Return this legacy project shape as a structured project config."""
		return ProjectConfig(
			target_path=self.target_sound_file,
			corpus_paths=[self.corpus_folder] if self.corpus_folder else [],
			output_dir=self.output_folder,
		)
