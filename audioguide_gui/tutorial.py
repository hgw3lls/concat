"""Built-in tutorial content for the AudioGuide GUI."""

from __future__ import annotations

from dataclasses import dataclass
import html


@dataclass(frozen=True)
class TutorialSection:
	"""One step in the GUI tutorial."""

	title: str
	body: tuple[str, ...]


TUTORIAL_SECTIONS: tuple[TutorialSection, ...] = (
	TutorialSection(
		"1. Prepare your Mac and start the GUI",
		(
			"From the repository root, run scripts/install_macos.sh on macOS. The installer creates .venv, installs the GUI dependencies, and checks for optional audio tools such as csound and ffmpeg.",
			"Activate the environment with source .venv/bin/activate, then launch the desktop app with python -m audioguide_gui.",
		),
	),
	TutorialSection(
		"2. Choose source and output paths",
		(
			"On the Render tab, choose a target sound file. This is the sound AudioGuide tries to reconstruct or follow.",
			"Choose a corpus folder containing the source sounds AudioGuide can select from.",
			"Choose an output folder and set an output name. The output folder must already exist so the GUI can write the generated options file and render outputs there.",
		),
	),
	TutorialSection(
		"3. Select output formats",
		(
			"Enable Csound audio render when you want AudioGuide to render an audio file. This requires the csound command-line tool on PATH.",
			"Keep JSON enabled when you want machine-readable selection data for Max/MSP or other tools.",
			"Enable Reaper or AAF only when you need a DAW session/export file for downstream editing.",
		),
	),
	TutorialSection(
		"4. Preview or customize options",
		(
			"Use Preview Generated Options File to inspect the Python options that the GUI will pass to agConcatenate.py.",
			"Use Raw AudioGuide options for advanced settings that are not exposed as form controls. Text entered there is appended after generated settings, so advanced values can override generated defaults.",
			"Use Save Options File As if you want to keep the generated options for command-line runs or manual editing.",
		),
	),
	TutorialSection(
		"5. Render and review outputs",
		(
			"Click Render to run AudioGuide. The live log shows the generated options path, progress messages, and any errors from the backend scripts.",
			"When rendering completes successfully, open the Output Browser tab. The GUI scans the output folder and groups Csound, JSON, Reaper, AAF, audio, and other generated files.",
		),
	),
	TutorialSection(
		"6. Use helper tools",
		(
			"The Tools tab wraps agSegmentSf.py, agGetSfDescriptors.py, and agGranulateSf.py. Choose an input file or folder, choose an output path when needed, and add advanced flags only if you already know the command-line option you need.",
			"Tool output streams into each tool panel so you can troubleshoot without leaving the GUI.",
		),
	),
	TutorialSection(
		"7. Save reusable projects",
		(
			"Use Project > Save Project to store paths, selected output formats, raw options, and the last generated options file path in an .agui project file.",
			"Use Project > Open Project to restore a previous GUI session before rendering again.",
		),
	),
)


TUTORIAL_INTRO = (
	"This guided walkthrough covers the usual AudioGuide GUI workflow: install, choose sounds, generate options, render, inspect outputs, and save reusable projects."
)


def render_tutorial_html() -> str:
	"""Return the tutorial as safe, simple HTML for QTextBrowser."""
	parts = [
		"<h1>AudioGuide GUI Tutorial</h1>",
		f"<p>{html.escape(TUTORIAL_INTRO)}</p>",
	]
	for section in TUTORIAL_SECTIONS:
		parts.append(f"<h2>{html.escape(section.title)}</h2>")
		parts.append("<ul>")
		for paragraph in section.body:
			parts.append(f"<li>{html.escape(paragraph)}</li>")
		parts.append("</ul>")
	parts.append(
		"<p><b>Tip:</b> The same tutorial is available as a Markdown document in "
		"<code>docs/GUI_TUTORIAL.md</code>.</p>"
	)
	return "\n".join(parts)
