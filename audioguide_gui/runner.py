"""Runner abstractions for future AudioGuide GUI rendering."""

from .project import ProjectConfig


class AudioGuideRunner:
	"""Placeholder runner for invoking AudioGuide from the GUI."""

	def render(self, project: ProjectConfig) -> None:
		"""Render *project* with AudioGuide.

		Actual rendering is intentionally not implemented in this initial GUI
		scaffold.
		"""
		raise NotImplementedError("AudioGuide rendering is not implemented yet.")
