from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from utils.platform import get_app_data_dir

logger = logging.getLogger(__name__)

_LOCK_NAME = "client.lock"


class SingleInstance:
    def __init__(self, lock_dir: Path | None = None):
        self._lock_dir = lock_dir or get_app_data_dir()
        self._lock_file = self._lock_dir / _LOCK_NAME
        self._handle = None
        self._acquired = False

    def acquire(self) -> bool:
        if self._acquired:
            return True
        self._lock_dir.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                return self._acquire_windows()
            return self._acquire_posix()
        except Exception:
            logger.exception("Failed to acquire single instance lock")
            return False

    def release(self) -> None:
        try:
            if sys.platform == "win32":
                self._release_windows()
            else:
                self._release_posix()
        except Exception:
            logger.exception("Failed to release single instance lock")

    def __enter__(self) -> bool:
        return self.acquire()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()

    def _acquire_posix(self) -> bool:
        import fcntl

        self._handle = open(self._lock_file, "w")
        try:
            fcntl.flock(self._handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            try:
                self._handle.close()
            except Exception:
                pass
            self._handle = None
            self._acquired = False
            return False
        self._handle.write(str(os.getpid()))
        self._handle.flush()
        self._acquired = True
        return True

    def _release_posix(self) -> None:
        if not self._handle:
            return
        import fcntl

        try:
            fcntl.flock(self._handle, fcntl.LOCK_UN)
        finally:
            try:
                self._handle.close()
            finally:
                self._handle = None
                self._acquired = False

    def _acquire_windows(self) -> bool:
        import msvcrt

        self._handle = open(self._lock_file, "w")
        try:
            # Lock 1 byte of the file.
            msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            try:
                self._handle.close()
            except Exception:
                pass
            self._handle = None
            self._acquired = False
            return False
        self._handle.write(str(os.getpid()))
        self._handle.flush()
        self._acquired = True
        return True

    def _release_windows(self) -> None:
        if not self._handle:
            return
        import msvcrt

        try:
            msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
        finally:
            try:
                self._handle.close()
            finally:
                self._handle = None
                self._acquired = False

