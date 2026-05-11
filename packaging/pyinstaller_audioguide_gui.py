"""PyInstaller entry point for the AudioGuide GUI.

PyInstaller executes entry scripts as files, so this wrapper uses an absolute
import instead of running ``audioguide_gui/__main__.py`` directly.
"""

from audioguide_gui.main import main


if __name__ == "__main__":
    raise SystemExit(main())
