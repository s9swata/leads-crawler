"""Signal handlers for graceful shutdown."""

import signal
import sys
from typing import Callable, Optional

# Global cleanup callback reference
cleanup_callback: Optional[Callable[[], None]] = None


def setup_signal_handlers(callback: Optional[Callable[[], None]] = None):
    """Register SIGINT/SIGTERM handlers for graceful shutdown.

    Args:
        callback: Optional callback to execute before exit (e.g., save checkpoint).
    """
    global cleanup_callback
    cleanup_callback = callback

    def handle_signal(signum, frame):
        if cleanup_callback:
            try:
                cleanup_callback()
            except Exception as e:
                print(f"Error during cleanup: {e}", file=sys.stderr)

        # Close any tqdm progress bars
        try:
            from tqdm import tqdm

            tqdm._instances.clear()  # type: ignore
        except Exception:
            pass

        print("\nInterrupted. Progress saved.")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)


def set_cleanup_callback(callback: Callable[[], None]):
    """Set the global cleanup callback after handlers are registered."""
    global cleanup_callback
    cleanup_callback = callback
