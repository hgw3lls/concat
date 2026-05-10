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
