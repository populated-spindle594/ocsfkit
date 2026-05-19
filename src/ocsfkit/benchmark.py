from __future__ import annotations

from statistics import median
from time import perf_counter
from typing import Any

from ocsfkit.mapping import apply_mapping


def benchmark_mapping(
    events: list[dict[str, Any]],
    mapping: dict[str, Any],
    custom_transforms: dict[str, Any] | None = None,
    iterations: int = 5,
) -> dict[str, Any]:
    if iterations < 1:
        raise ValueError("iterations must be >= 1")
    durations: list[float] = []
    mapped_events = 0
    for _ in range(iterations):
        started = perf_counter()
        for event in events:
            apply_mapping(event, mapping, custom_transforms)
            mapped_events += 1
        durations.append(perf_counter() - started)
    event_count = len(events)
    best = min(durations)
    return {
        "events": event_count,
        "iterations": iterations,
        "total_mapped_events": mapped_events,
        "best_seconds": round(best, 6),
        "median_seconds": round(median(durations), 6),
        "events_per_second": round((event_count / best) if best and event_count else 0.0, 2),
    }
