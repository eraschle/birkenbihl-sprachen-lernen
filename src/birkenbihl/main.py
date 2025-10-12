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
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

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


def main_gui() -> int:
    """Entry point for GUI mode using PySide6.

    Launches the native Qt desktop GUI for the Birkenbihl application.
    Use with: birkenbihl-gui

    Returns:
        Exit code (0 for success, 1 for error)
    """
    configure_logging()

    try:
        from birkenbihl.gui.main import main as gui_main

        return gui_main()
    except ImportError as e:
        print("Error: PySide6 not installed. Install with: uv sync")
        print(f"Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching GUI: {e}")
        sys.exit(1)


if __name__ in {"__main__", "__mp_main__"}:
    main()
