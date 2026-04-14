from __future__ import annotations

from collections import Counter


class MetricsRegistry:
    def __init__(self) -> None:
        self._counters = Counter()

    def inc(self, name: str, value: int = 1) -> None:
        self._counters[name] += value

    def render(self) -> str:
        lines = []
        for key in sorted(self._counters):
            lines.append(f"# TYPE {key} counter")
            lines.append(f"{key} {self._counters[key]}")
        return "\n".join(lines) + ("\n" if lines else "")
