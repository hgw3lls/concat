"""Runner abstractions for future AudioGuide GUI rendering."""

from .project import AudioGuideProject


class AudioGuideRunner:
	"""Placeholder runner for invoking AudioGuide from the GUI."""

	def render(self, project: AudioGuideProject) -> None:
		"""Render *project* with AudioGuide.

		Actual rendering is intentionally not implemented in this initial GUI
		scaffold.
		"""
		raise NotImplementedError("AudioGuide rendering is not implemented yet.")
