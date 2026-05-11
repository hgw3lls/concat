# AudioGuide GUI Tutorial

This tutorial walks through the macOS-first AudioGuide GUI workflow: install the app dependencies, choose sounds, generate options, render, inspect outputs, use helper tools, and save reusable projects.

## 1. Prepare your Mac and start the GUI

From the repository root, run the macOS installer:

```bash
scripts/install_macos.sh
```

The installer creates `.venv`, installs the GUI dependencies, and checks for optional audio tools such as `csound` and `ffmpeg`. If Homebrew is available, the installer can use it to install command-line audio dependencies for both Apple Silicon and Intel Macs.

Activate the virtual environment and start the GUI:

```bash
source .venv/bin/activate
python -m audioguide_gui
```

## 2. Choose source and output paths

Open the **Render** tab and fill in the three path fields:

1. **Target sound file**: the sound AudioGuide tries to reconstruct or follow.
2. **Corpus folder**: the folder of source sounds AudioGuide can select from.
3. **Output folder**: the destination for generated options and render outputs.

The output folder must already exist. Set **Output name** to control the base name used for generated files.

## 3. Select output formats

Choose only the formats you need:

- **Csound audio render** writes and renders a Csound output file. This requires a `csound` executable on `PATH`.
- **JSON dictionary** writes machine-readable selection data that can be used by Max/MSP or other tools.
- **Reaper project** writes a `.rpp` session for Reaper.
- **AAF** writes an AAF interchange file for DAW workflows.

If you do not have `csound` installed, disable **Csound audio render** and use JSON/Reaper/AAF outputs instead.

## 4. Preview or customize options

Use **Preview Generated Options File** before rendering to inspect the Python options the GUI will pass to `agConcatenate.py`.

Use **Raw AudioGuide options** for advanced settings that are not exposed as form controls. The GUI appends that text after generated settings, so advanced values can override generated defaults.

Use **Save Options File As…** when you want to keep the generated options for command-line runs or manual editing.

## 5. Render and review outputs

Click **Render** to run AudioGuide. The live log shows:

- the selected target/corpus/output paths;
- the generated options file path;
- progress messages from AudioGuide;
- validation errors or backend failures.

When rendering completes successfully, open **Output Browser**. The GUI scans the output folder and groups generated files such as Csound scores/renders, JSON dictionaries, Reaper projects, AAF files, audio files, and uncategorized outputs.

## 6. Use helper tools

The **Tools** tab wraps the repository helper scripts:

- **Segment** runs `agSegmentSf.py`.
- **Descriptors** runs `agGetSfDescriptors.py`.
- **Granulate** runs `agGranulateSf.py`.

Choose an input file or folder, choose an output path when the tool asks for one, and add **Advanced flags** only when you already know the command-line option you need. Each tool streams output into its panel so you can troubleshoot without leaving the GUI.

## 7. Save reusable projects

Use **Project > Save Project** to store paths, selected output formats, raw options, and the last generated options file path in an `.agui` project file.

Use **Project > Open Project** to restore a previous GUI session before rendering again.

## Troubleshooting

- If rendering reports that `csound` is missing, install it with Homebrew or disable **Csound audio render**.
- If a path validation message appears, confirm the target file, corpus folder, and output folder exist before rendering.
- If advanced options cause failures, preview the generated options file and remove overrides until the render works again.
