"""기록에 쓰는 지금 시각."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> str:
    """기록에 쓰는 지금 시각 (UTC, 초 단위, Z)."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
