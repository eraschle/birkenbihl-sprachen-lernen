"""Main entry point for the Birkenbihl application.

This module serves as the primary entry point and can launch different
interfaces (CLI, GUI, etc.) based on arguments or configuration.
"""

import logging
import sys


def configure_logging() -> None:
    """Configure logging for the application.

    Sets up logging to stdout with colored formatting and appropriate levels.
    """
    # Create formatter with colors and timestamps
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Set specific levels for birkenbihl modules
    logging.getLogger("birkenbihl").setLevel(logging.INFO)
    logging.getLogger("birkenbihl.providers").setLevel(logging.DEBUG)
    logging.getLogger("birkenbihl.ui").setLevel(logging.INFO)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)

    logging.info("Logging configured successfully")


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

    configure_logging()
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
