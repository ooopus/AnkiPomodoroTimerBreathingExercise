"""
This module handles all interactions with Anki's built-in addon configuration system.
It encapsulates the logic for reading and writing settings, ensuring that user
preferences are safely stored and persist across addon updates.
"""

import json
from pathlib import Path
from typing import Any

from aqt import mw

from ..translator import _


def get_addon_name() -> str:
    """Gets the name of the current addon from its directory path."""
    # __name__ for this file will be 'AnkiPomodoroTimerBreatheExercise.src.config.anki_config'
    # The root addon folder name is the first part.
    return __name__.split(".")[0]


def get_anki_config() -> dict[str, Any] | None:
    """
    Retrieves the configuration for this addon from Anki's settings.
    Returns None if no config is found.
    """
    return mw.addonManager.getConfig(get_addon_name())


def write_anki_config(config: dict[str, Any]):
    """
    Writes the configuration for this addon to Anki's settings.
    """
    mw.addonManager.writeConfig(get_addon_name(), config)


def migrate_from_json_if_needed():
    """
    If a legacy config.json file exists, this function reads its content,
    writes it to Anki's configuration system, and renames the old file
    to prevent re-migration. This ensures a seamless transition for users
    updating from older versions of the addon.
    """
    # Path to the legacy config file, which is in the parent directory of `src`
    addon_dir = Path(__file__).resolve().parent.parent.parent
    config_path = addon_dir / "config.json"
    migrated_path = addon_dir / "config.json.migrated"

    if migrated_path.exists():
        return

    if config_path.exists():
        try:
            with config_path.open("r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    # File is empty, just rename it
                    config_path.rename(migrated_path)
                    return

                config_data = json.loads(content)

            write_anki_config(config_data)
            config_path.rename(migrated_path)
            print(
                f"{get_addon_name()}: "
                + _("Successfully migrated settings from config.json.")
            )
        except Exception as e:
            print(
                f"{get_addon_name()}: "
                + _("Could not migrate settings from config.json: {}").format(e)
            )
