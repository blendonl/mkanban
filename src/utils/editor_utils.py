import os
import subprocess
from src.config.configuration_manager import get_config


def open_editor_for_app(file_path: str, app_instance) -> None:
    config_manager = get_config()
    editor = config_manager.get_editor()
    try:
        with app_instance.suspend():
            subprocess.run([editor, str(file_path)], check=True, env=os.environ.copy())
    except subprocess.CalledProcessError:
        app_instance.notify(f"Error opening {editor}", severity="error")
        raise
    except FileNotFoundError:
        app_instance.notify(
            f"{editor} not found. Please install {editor}", severity="error"
        )
        raise
