#!/usr/bin/env python3
"""Run a command while writing stdout/stderr to date-partitioned log files.

This wrapper is intentionally dependency-free so systemd units can use it
before the project virtual/toolchain environment is loaded. It tees child
output to systemd's journal and to:

  logs/systemd/YYYY-MM-DD/<service>.log
  logs/systemd/YYYY-MM-DD/<service>.err.log

Long-running services keep running while the wrapper reopens log files when the
KST day changes.
"""

from __future__ import annotations

import argparse
import os
import selectors
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - fallback for very old Python builds
    ZoneInfo = None  # type: ignore[assignment]


DEFAULT_LOG_ROOT = "/data/workspace/My/hwiStock/logs/systemd"
DEFAULT_TIMEZONE = "Asia/Seoul"


class DailyLogWriter:
    def __init__(self, *, name: str, log_root: Path, timezone_name: str, tee: bool) -> None:
        self.name = name
        self.log_root = log_root
        self.timezone_name = timezone_name
        self.tee = tee
        self.current_day: str | None = None
        self.stdout_file: BinaryIO | None = None
        self.stderr_file: BinaryIO | None = None

    def _today(self) -> str:
        if ZoneInfo is None:
            return datetime.now().date().isoformat()
        return datetime.now(ZoneInfo(self.timezone_name)).date().isoformat()

    def _ensure_open(self) -> None:
        today = self._today()
        if today == self.current_day and self.stdout_file and self.stderr_file:
            return

        self.close()
        day_dir = self.log_root / today
        day_dir.mkdir(parents=True, exist_ok=True)
        self.stdout_file = (day_dir / f"{self.name}.log").open("ab", buffering=0)
        self.stderr_file = (day_dir / f"{self.name}.err.log").open("ab", buffering=0)
        self.current_day = today

    def write(self, *, stream_name: str, data: bytes) -> None:
        if not data:
            return
        self._ensure_open()
        if stream_name == "stdout":
            assert self.stdout_file is not None
            self.stdout_file.write(data)
            if self.tee:
                os.write(sys.stdout.fileno(), data)
            return

        assert self.stderr_file is not None
        self.stderr_file.write(data)
        if self.tee:
            os.write(sys.stderr.fileno(), data)

    def close(self) -> None:
        for handle in (self.stdout_file, self.stderr_file):
            if handle is not None:
                handle.close()
        self.stdout_file = None
        self.stderr_file = None


def normalize_command(raw_command: list[str]) -> list[str]:
    if raw_command and raw_command[0] == "--":
        return raw_command[1:]
    return raw_command


def run(command: list[str], writer: DailyLogWriter) -> int:
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        close_fds=True,
    )

    def forward_signal(signum: int, _frame: object) -> None:
        try:
            process.send_signal(signum)
        except ProcessLookupError:
            pass

    previous_sigterm = signal.signal(signal.SIGTERM, forward_signal)
    previous_sigint = signal.signal(signal.SIGINT, forward_signal)

    selector = selectors.DefaultSelector()
    assert process.stdout is not None
    assert process.stderr is not None
    selector.register(process.stdout.fileno(), selectors.EVENT_READ, "stdout")
    selector.register(process.stderr.fileno(), selectors.EVENT_READ, "stderr")

    try:
        while selector.get_map():
            for key, _mask in selector.select(timeout=0.5):
                chunk = os.read(key.fd, 65536)
                if chunk:
                    writer.write(stream_name=str(key.data), data=chunk)
                else:
                    selector.unregister(key.fd)

            if process.poll() is not None and not selector.get_map():
                break
        return process.wait()
    finally:
        signal.signal(signal.SIGTERM, previous_sigterm)
        signal.signal(signal.SIGINT, previous_sigint)
        selector.close()
        writer.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a command with daily log files.")
    parser.add_argument("--name", required=True, help="Log file base name, usually the systemd service stem")
    parser.add_argument(
        "--log-root",
        default=os.environ.get("HWISTOCK_SYSTEMD_LOG_ROOT", DEFAULT_LOG_ROOT),
        help="Root directory for date-partitioned logs",
    )
    parser.add_argument(
        "--timezone",
        default=os.environ.get("HWISTOCK_LOG_TIMEZONE", DEFAULT_TIMEZONE),
        help="Timezone used for date partitioning",
    )
    parser.add_argument("--no-tee", action="store_true", help="Do not also write child output to stdout/stderr")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run after --")
    args = parser.parse_args(argv)

    command = normalize_command(args.command)
    if not command:
        parser.error("missing command after --")

    writer = DailyLogWriter(
        name=args.name,
        log_root=Path(args.log_root),
        timezone_name=args.timezone,
        tee=not args.no_tee,
    )
    return run(command, writer)


if __name__ == "__main__":
    raise SystemExit(main())
