"""Main entry point for the Birkenbihl application.

This module serves as the primary entry point and can launch different
interfaces (CLI, GUI, etc.) based on arguments or configuration.
"""

import sys


def main() -> None:
    """Main function to start the app.

    By default, launches the CLI interface. In the future, this can be
    extended to support GUI mode via command-line arguments.

    Example future usage:
        birkenbihl           # Launch CLI (default)
        birkenbihl --gui     # Launch GUI
    """
    # For now, always launch CLI
    # Future: Parse args to determine CLI vs GUI
    from birkenbihl.cli import cli

    cli()


def main_gui() -> None:
    """Entry point for GUI mode (future implementation).

    This will be used when the GUI is implemented, allowing:
        birkenbihl-gui
    or as a separate command in pyproject.toml
    """
    # Future GUI implementation
    print("GUI not yet implemented. Use CLI for now.")
    sys.exit(1)


if __name__ in {"__main__", "__mp_main__"}:
    main()
