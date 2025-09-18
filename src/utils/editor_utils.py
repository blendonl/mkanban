import subprocess
from pathlib import Path
from config.environment import Environment


def open_editor_for_app(file_path: str, app_instance) -> None:
    editor = Environment.get_editor()
    try:
        with app_instance.suspend():
            subprocess.run([editor, str(file_path)], check=True)
    except subprocess.CalledProcessError:
        app_instance.notify(f"Error opening {editor}", severity="error")
        raise
    except FileNotFoundError:
        app_instance.notify(f"{editor} not found. Please install {editor}", severity="error")
        raise