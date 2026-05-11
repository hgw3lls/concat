# AudioGuide GUI Setup and Packaging

This document covers local setup for the optional desktop GUI in `audioguide_gui`.
It is intentionally separate from the existing AudioGuide CLI documentation so the
command-line workflow remains documented in `README.md` and `docs_v1.79.html`.

## What the GUI provides

The GUI is a PySide6 desktop front end for common AudioGuide tasks:

- build and preview AudioGuide options files from selected target/corpus/output paths;
- launch `agConcatenate.py` while streaming stdout/stderr into the window;
- run helper tools such as `agSegmentSf.py`, `agGetSfDescriptors.py`, and `agGranulateSf.py`;
- browse generated output files from the selected render output directory.

The GUI invokes the same Python entry points used by the CLI. Keep using the CLI
docs for detailed AudioGuide option syntax and synthesis behavior.

## Requirements

- Python 3.10 or newer is recommended.
- `PySide6` is required for the desktop widgets and is listed in `requirements-gui.txt`.
- `csound` is required when rendering Csound audio output. The GUI checks for a
  `csound` executable on `PATH` before launching options that request Csound
  output. If you only want non-Csound outputs, set the generated options to avoid
  Csound rendering, for example by setting `CSOUND_RENDER_FILEPATH = None` or
  `CSOUND_CSD_FILEPATH = None` in the options text before rendering.
- `ffmpeg` is not required by the GUI itself. Install it only if your local
  AudioGuide workflow, external conversion step, or downstream preview tool needs
  FFmpeg-supported audio/video conversion.

### macOS dependency hints

Using Homebrew is one common way to install the external audio tools:

```bash
brew install csound ffmpeg
```

After installation, confirm that the tools are visible to shells and packaged
apps launched from Terminal:

```bash
which csound
which ffmpeg
```

## Local source checkout setup

On macOS, the fastest setup path is the repository installer:

```bash
scripts/install_macos.sh
```

The installer creates `.venv`, installs the Python packages required by the CLI
and GUI, and uses Homebrew for Apple Silicon/Intel Mac command-line audio tools
when Homebrew is available. Use `scripts/install_macos.sh --help` to see options
for installing Homebrew, optional analysis extras, or building the `.app` bundle.

For a manual setup from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy
python -m pip install -r requirements-gui.txt
```

Then launch the GUI from the repository root:

```bash
python -m audioguide_gui
```

Launching from the repository root keeps the GUI's relative lookups for
`agConcatenate.py` and the helper scripts aligned with the source checkout.

## Basic GUI usage

For a guided walkthrough, open the built-in **Tutorial** tab or read `docs/GUI_TUTORIAL.md`.

1. Start the app with `python -m audioguide_gui`.
2. On the **Render** tab, choose a target sound file, corpus folder, and output
   folder.
3. Choose the output formats you need. Csound audio rendering requires `csound`
   on `PATH`.
4. Use **Preview Generated Options File** to inspect the AudioGuide option file
   the GUI will pass to `agConcatenate.py`.
5. Use **Save Options File As…** if you want to keep or edit the options file.
6. Click **Render** to launch AudioGuide. Logs stream in the lower pane.
7. Use **Cancel** to request process termination if the render should stop.
8. Use the **Tools** tabs for segmentation, descriptor extraction, and granular
   helper scripts.

## Optional macOS app packaging with PyInstaller

The repository includes a starter PyInstaller spec at
`packaging/audioguide_gui_macos.spec`. It is intended as a local packaging aid,
not as a replacement for source-checkout development.

Install packaging dependencies into a clean virtual environment:

```bash
python3 -m venv .venv-package
source .venv-package/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-gui.txt pyinstaller
```

Build the `.app` bundle from the repository root:

```bash
pyinstaller --clean --noconfirm packaging/audioguide_gui_macos.spec
```

The app bundle is written under `dist/AudioGuide GUI.app`.

### Packaging notes and limitations

- The spec bundles the AudioGuide Python packages and top-level helper scripts
  needed by the GUI. Keep the app's working directory and bundled paths in mind
  if you customize how scripts are discovered.
- `csound` and `ffmpeg` are treated as external command-line tools. They are not
  bundled by the starter spec; install them separately and ensure the packaged
  app can find them on `PATH`, or configure your options to avoid features that
  require them.
- macOS Gatekeeper signing/notarization is outside the scope of the starter spec.
  For distribution outside your own machine, sign and notarize the app according
  to Apple's current developer documentation.
- If PyInstaller misses optional modules used by a custom AudioGuide options
  file, add them to the spec's `hiddenimports` list and rebuild.
