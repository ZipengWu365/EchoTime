"""Shared profiling context objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass(slots=True)
class ProfilingContext:
    """Runtime configuration for profiling and plugin execution."""

    domain: str | None = None
    timestamps: Any | Sequence[Any] | None = None
    time_axis: int = 0
    channel_axis: int | None = -1
    subject_axis: int = 0
    sampling_rate: float | None = None
    tr: float | None = None
    channel_names: list[str] | None = None
    roi_names: list[str] | None = None
    network_labels: list[str] | None = None
    subject_ids: list[str] | None = None
    extra_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def resolved_domain(self) -> str:
        return (self.domain or "generic").lower()

    @property
    def channel_labels(self) -> list[str] | None:
        if self.roi_names is not None:
            return list(self.roi_names)
        if self.channel_names is not None:
            return list(self.channel_names)
        return None
