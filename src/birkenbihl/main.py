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
    """Entry point for GUI mode using Streamlit.

    Launches the Streamlit web interface for the Birkenbihl application.
    Use with: birkenbihl-gui
    """
    import subprocess
    from pathlib import Path

    app_path = Path(__file__).parent / "ui" / "app.py"
    try:
        subprocess.run(
            ["streamlit", "run", str(app_path)],
            check=True,
        )
    except ImportError:
        print("Error: Streamlit not installed. Install with: uv sync")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error launching Streamlit: {e}")
        sys.exit(1)


if __name__ in {"__main__", "__mp_main__"}:
    main()
