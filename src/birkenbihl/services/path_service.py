"""Path service for centralized application path management.

Provides platform-aware path resolution for application data, settings, and storage.
Ensures consistent path handling across Windows and Linux.
"""

import os
import sys
from pathlib import Path


def _ensure_exists(path: Path) -> Path:
    """Ensure directory exists, creating it if necessary.

    Args:
        path: Path to check/create

    Returns:
        The same path (for chaining)
    """
    if path.exists():
        return path

    # Create directory (handles both file paths and directory paths)
    dir_path = path.parent if path.suffix else path
    dir_path.mkdir(parents=True, exist_ok=True)
    return path


def _get_config_root_path() -> Path:
    """Get platform-specific configuration root directory.

    Returns:
        Path to Birkenbihl config directory:
        - Windows: %APPDATA%/birkenbihl or %USERPROFILE%/birkenbihl
        - Linux: ~/.config/birkenbihl (XDG Base Directory)

    Raises:
        NotImplementedError: If platform is not Windows or Linux
    """
    root_path = None
    match sys.platform:
        case "win32":
            root_path = os.getenv("APPDATA", None)
        case "linux":
            root_path = os.getenv("XDG_CONFIG_HOME", None)
        case _:
            raise NotImplementedError(f"Platform not supported: {sys.platform}")
    if root_path is None:
        root_path = Path.home()
    root_path = Path(root_path) / "birkenbihl"
    return _ensure_exists(root_path)


def get_app_path(file_path_or_name: str) -> Path:
    """Get full path for application file or directory.

    Resolves relative paths against the platform-specific config root.
    Creates parent directories if they don't exist.

    Args:
        file_path_or_name: Filename or relative path within app directory

    Returns:
        Full path within Birkenbihl config directory

    Examples:
        >>> get_app_path("settings.yaml")
        PosixPath('/home/user/.config/birkenbihl/settings.yaml')
        >>> get_app_path("translations/data.json")
        PosixPath('/home/user/.config/birkenbihl/translations/data.json')
    """
    return _get_config_root_path() / file_path_or_name


def get_setting_path(filename: str = "settings.yaml") -> Path:
    """Get path to settings file.

    Args:
        filename: Settings filename (default: "settings.yaml")

    Returns:
        Full path to settings file

    Examples:
        >>> get_setting_path()
        PosixPath('/home/user/.config/birkenbihl/settings.yaml')
        >>> get_setting_path("dev-settings.yaml")
        PosixPath('/home/user/.config/birkenbihl/dev-settings.yaml')
    """
    return get_app_path(filename)


def get_translation_path(filename: str = "translations.json") -> Path:
    """Get path to translation storage file or directory.

    Args:
        filename: Translation filename or directory (default: "translations.json")

    Returns:
        Full path to translation storage

    Examples:
        >>> get_translation_path()
        PosixPath('/home/user/.config/birkenbihl/translations.json')
        >>> get_translation_path("translations")
        PosixPath('/home/user/.config/birkenbihl/translations')
    """
    return get_app_path(filename)
