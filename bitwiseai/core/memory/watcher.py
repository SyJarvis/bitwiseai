"""
File watcher for monitoring memory file changes.
"""

import os
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    # Dummy classes for type hints when watchdog is not available
    FileSystemEventHandler = object
    FileSystemEvent = object


if HAS_WATCHDOG:
    class MemoryFileEventHandler(FileSystemEventHandler):
        """Event handler for memory file changes."""

        def __init__(
            self,
            on_change: Callable[[str, str], None],
            debounce_ms: int = 1000
        ):
            """
            Initialize event handler.

            Args:
                on_change: Callback function (file_path, event_type)
                debounce_ms: Debounce delay in milliseconds
            """
            self.on_change = on_change
            self.debounce_ms = debounce_ms
            self._pending_changes: Dict[str, str] = {}
            self._timer: Optional[threading.Timer] = None
            self._lock = threading.Lock()

        def on_modified(self, event) -> None:
            """Handle file modification."""
            if event.is_directory:
                return

            if self._is_memory_file(event.src_path):
                self._queue_change(event.src_path, "modified")

        def on_created(self, event) -> None:
            """Handle file creation."""
            if event.is_directory:
                return

            if self._is_memory_file(event.src_path):
                self._queue_change(event.src_path, "created")

        def on_deleted(self, event) -> None:
            """Handle file deletion."""
            if event.is_directory:
                return

            if self._is_memory_file(event.src_path):
                self._queue_change(event.src_path, "deleted")

        def on_moved(self, event) -> None:
            """Handle file move/rename."""
            if event.is_directory:
                return

            # Treat as delete + create
            if self._is_memory_file(event.src_path):
                self._queue_change(event.src_path, "deleted")

            if hasattr(event, 'dest_path') and self._is_memory_file(event.dest_path):
                self._queue_change(event.dest_path, "created")

        def _is_memory_file(self, path: str) -> bool:
            """Check if file is a memory file (markdown)."""
            path_lower = path.lower()
            return path_lower.endswith('.md') or path_lower.endswith('.markdown')

        def _queue_change(self, file_path: str, event_type: str) -> None:
            """Queue a file change with debouncing."""
            with self._lock:
                self._pending_changes[file_path] = event_type

                # Cancel existing timer
                if self._timer:
                    self._timer.cancel()

                # Schedule new timer
                self._timer = threading.Timer(
                    self.debounce_ms / 1000.0,
                    self._flush_changes
                )
                self._timer.start()

        def _flush_changes(self) -> None:
            """Flush pending changes."""
            with self._lock:
                changes = dict(self._pending_changes)
                self._pending_changes.clear()
                self._timer = None

            # Call callbacks
            for file_path, event_type in changes.items():
                try:
                    self.on_change(file_path, event_type)
                except Exception:
                    pass  # Ignore callback errors


class FileWatcher:
    """File watcher for monitoring memory file changes."""

    def __init__(
        self,
        watch_paths: List[str],
        on_change: Callable[[str, str], None],
        debounce_ms: int = 1000
    ):
        """
        Initialize file watcher.

        Args:
            watch_paths: List of paths to watch
            on_change: Callback function (file_path, event_type)
            debounce_ms: Debounce delay in milliseconds
        """
        self.watch_paths: Set[str] = set()
        self.on_change = on_change
        self.debounce_ms = debounce_ms

        self._observer = None
        self._handler = None
        self._running = False

        # Add initial paths
        for path in watch_paths:
            self.add_path(path)

    def add_path(self, path: str) -> None:
        """Add a path to watch."""
        abs_path = os.path.abspath(os.path.expanduser(path))

        # If path is a file, watch its directory
        if os.path.isfile(abs_path):
            abs_path = os.path.dirname(abs_path)

        self.watch_paths.add(abs_path)

        # If already running, add to observer
        if self._running and self._observer and HAS_WATCHDOG:
            try:
                self._observer.schedule(
                    self._handler,
                    abs_path,
                    recursive=True
                )
            except Exception:
                pass

    def remove_path(self, path: str) -> None:
        """Remove a path from watching."""
        abs_path = os.path.abspath(os.path.expanduser(path))

        if os.path.isfile(abs_path):
            abs_path = os.path.dirname(abs_path)

        self.watch_paths.discard(abs_path)

        # Note: watchdog doesn't support unscheduling individual paths
        # We would need to restart the observer

    def start(self) -> None:
        """Start watching."""
        if self._running:
            return

        if not HAS_WATCHDOG:
            print("Warning: watchdog not installed, file watching disabled")
            return

        self._handler = MemoryFileEventHandler(
            self.on_change,
            self.debounce_ms
        )

        self._observer = Observer()

        for path in self.watch_paths:
            if os.path.exists(path):
                try:
                    self._observer.schedule(
                        self._handler,
                        path,
                        recursive=True
                    )
                except Exception as e:
                    print(f"Warning: Failed to watch path {path}: {e}")

        self._observer.start()
        self._running = True

    def stop(self) -> None:
        """Stop watching."""
        if not self._running:
            return

        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None

        self._handler = None
        self._running = False

    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._running


class PollingFileWatcher:
    """
    Simple polling-based file watcher (fallback when watchdog is not available).
    """

    def __init__(
        self,
        watch_paths: List[str],
        on_change: Callable[[str, str], None],
        poll_interval: float = 5.0
    ):
        """
        Initialize polling watcher.

        Args:
            watch_paths: List of paths to watch
            on_change: Callback function (file_path, event_type)
            poll_interval: Polling interval in seconds
        """
        self.watch_paths: Set[str] = set()
        self.on_change = on_change
        self.poll_interval = poll_interval

        self._files_state: Dict[str, float] = {}
        self._thread: Optional[threading.Thread] = None
        self._running = False

        for path in watch_paths:
            self.add_path(path)

    def add_path(self, path: str) -> None:
        """Add a path to watch."""
        abs_path = os.path.abspath(os.path.expanduser(path))
        self.watch_paths.add(abs_path)

        # Initialize state for existing files
        self._scan_path(abs_path)

    def remove_path(self, path: str) -> None:
        """Remove a path from watching."""
        abs_path = os.path.abspath(os.path.expanduser(path))
        self.watch_paths.discard(abs_path)

    def start(self) -> None:
        """Start polling."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop polling."""
        self._running = False

        if self._thread:
            self._thread.join(timeout=self.poll_interval + 1)
            self._thread = None

    def _poll_loop(self) -> None:
        """Main polling loop."""
        while self._running:
            for path in list(self.watch_paths):
                self._scan_path(path)

            time.sleep(self.poll_interval)

    def _scan_path(self, path: str) -> None:
        """Scan a path for changes."""
        if os.path.isfile(path):
            # Single file
            self._check_file(path)
        elif os.path.isdir(path):
            # Directory - scan markdown files
            try:
                for root, _, files in os.walk(path):
                    for filename in files:
                        if filename.lower().endswith('.md'):
                            file_path = os.path.join(root, filename)
                            self._check_file(file_path)
            except Exception:
                pass

    def _check_file(self, file_path: str) -> None:
        """Check a file for changes."""
        try:
            mtime = os.path.getmtime(file_path)

            if file_path in self._files_state:
                if self._files_state[file_path] != mtime:
                    # File modified
                    self._files_state[file_path] = mtime
                    try:
                        self.on_change(file_path, "modified")
                    except Exception:
                        pass
            else:
                # New file
                self._files_state[file_path] = mtime
                try:
                    self.on_change(file_path, "created")
                except Exception:
                    pass

        except OSError:
            # File might have been deleted
            if file_path in self._files_state:
                del self._files_state[file_path]
                try:
                    self.on_change(file_path, "deleted")
                except Exception:
                    pass

    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._running


def create_file_watcher(
    watch_paths: List[str],
    on_change: Callable[[str, str], None],
    debounce_ms: int = 1000,
    use_polling: bool = False
):
    """
    Create a file watcher.

    Args:
        watch_paths: List of paths to watch
        on_change: Callback function
        debounce_ms: Debounce delay in milliseconds
        use_polling: Force use of polling watcher

    Returns:
        FileWatcher instance or PollingFileWatcher instance
    """
    if use_polling or not HAS_WATCHDOG:
        # Use polling fallback
        return PollingFileWatcher(
            watch_paths,
            on_change,
            poll_interval=debounce_ms / 1000.0
        )

    return FileWatcher(watch_paths, on_change, debounce_ms)
