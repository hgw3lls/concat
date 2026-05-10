"""Helpers for future AudioGuide option-file generation."""

from .project import AudioGuideProject


class OptionBuilder:
	"""Placeholder option builder for generated AudioGuide option files."""

	def build(self, project: AudioGuideProject) -> str:
		"""Return option-file text for *project*.

		Actual AudioGuide option generation is intentionally deferred until the
		GUI rendering workflow is implemented.
		"""
		raise NotImplementedError("Option file generation is not implemented yet.")
