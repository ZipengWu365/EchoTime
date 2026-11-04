"""Immutable, lazily prepared inputs for repeated raw-series comparisons.

The features in this module use the same interpolation, normalization and channel
policy as :func:`echotime.compare_series`.  They are deliberately separate from
the low-level distance API, whose cleaning and normalization rules differ.
"""

from __future__ import annotations

import hashlib
import operator
from typing import Any, Callable

import numpy as np
from scipy.stats import rankdata


PREPARED_SEMANTICS_VERSION = "raw-series-v1"


def _readonly_array(values: Any, *, dtype: Any = float) -> np.ndarray:
    """Copy into immutable storage, including against ``setflags(write=True)``."""
    source = np.asarray(values, dtype=dtype)
    array = np.ascontiguousarray(source)
    return np.frombuffer(array.tobytes(), dtype=array.dtype).reshape(source.shape)


class PreparedChannel:
    """A read-only trajectory and lazily cached features derived from it.

    ``spectrum`` is the spectrum of the standardized first differences, as used
    by the strict raw-series score.  ``bin_codes`` follows NumPy's equal-width
    histogram endpoint convention.  Cached ranks and bins may only be reused
    when a comparison keeps every observation; a pair-specific finite mask can
    change both the ranks and the histogram edges.
    """

    __slots__ = ("_values", "_cache")

    def __init__(self, values: Any) -> None:
        object.__setattr__(self, "_values", _readonly_array(values).reshape(-1))
        object.__setattr__(self, "_cache", {})

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("PreparedChannel is immutable")

    def _cached(self, key: Any, factory: Callable[[], Any]) -> Any:
        if key not in self._cache:
            self._cache[key] = factory()
        return self._cache[key]

    @property
    def values(self) -> np.ndarray:
        return self._values

    @property
    def all_finite(self) -> bool:
        return self._cached("all_finite", lambda: bool(np.all(np.isfinite(self.values))))

    @property
    def std(self) -> float:
        return self._cached("std", lambda: float(np.std(self.values)))

    @property
    def difference(self) -> np.ndarray:
        from .similarity import _difference_view

        return self._cached("difference", lambda: _readonly_array(_difference_view(self.values)))

    @property
    def trend(self) -> np.ndarray:
        from .similarity import _smooth_trend

        return self._cached("trend", lambda: _readonly_array(_smooth_trend(self.values)))

    @property
    def trend_difference(self) -> np.ndarray:
        from .similarity import _difference_view

        return self._cached("trend_difference", lambda: _readonly_array(_difference_view(self.trend)))

    @property
    def spectrum(self) -> tuple[np.ndarray, np.ndarray]:
        from .similarity import _normalized_spectrum

        def calculate() -> tuple[np.ndarray, np.ndarray]:
            frequencies, power = _normalized_spectrum(self.difference)
            return _readonly_array(frequencies), _readonly_array(power)

        return self._cached("difference_spectrum", calculate)

    @property
    def ranks(self) -> np.ndarray:
        if not self.all_finite:
            raise ValueError("Cached ranks require a fully finite trajectory")
        return self._cached("ranks", lambda: _readonly_array(rankdata(self.values, method="average")))

    def bin_codes(self, bins: int) -> np.ndarray:
        """Return equal-width histogram codes, including the rightmost edge."""
        bins = operator.index(bins)
        if bins < 1:
            raise ValueError("bins must be a positive integer")
        if not self.all_finite:
            raise ValueError("Cached histogram codes require a fully finite trajectory")

        def calculate() -> np.ndarray:
            edges = np.histogram_bin_edges(self.values, bins=bins)
            codes = np.searchsorted(edges, self.values, side="right") - 1
            codes[self.values == edges[-1]] -= 1
            return _readonly_array(codes, dtype=np.int64)

        return self._cached(("bin_codes", bins), calculate)

    @property
    def monotonic_fraction(self) -> float:
        from .similarity import _monotonic_fraction

        return self._cached("monotonic_fraction", lambda: _monotonic_fraction(self.values))

    def __reduce__(self) -> tuple[Any, tuple[np.ndarray]]:
        # Rebuild the immutable backing storage rather than unpickling writable
        # NumPy arrays into the cache.  Derived features can be recreated lazily.
        return type(self), (self.values,)


class PreparedSeries:
    """Own an immutable input snapshot and reuse exact per-series features.

    Parameters use the existing :func:`echotime.compare_series` semantics.  Raw
    values are converted to time-by-channel layout using its legacy heuristic;
    timestamps follow its legacy validation.  Resampling is lazy and preserves
    its missing-data behavior, including all-NaN channels with fewer than three
    finite observations.  Preparing a series does not certify that all five
    similarity components will be finite.

    A cache belongs only to this immutable input and ``n_points`` configuration.
    ``cache_key`` adds a content digest and semantic version when a caller needs
    an external key.  Mutating the original input after construction cannot
    affect either the snapshot or any derived feature.

    Channel counts are a *pair* decision.  For matching counts, callers use
    ``channel(i)``.  For mismatched counts, both sides use
    ``channel(aggregate=True)``: the standardized resampled trajectories are
    averaged first, and differences, trends and spectra are then computed from
    that aggregate.  Averaging per-channel features would change the score.
    """

    __slots__ = ("_raw_values", "_timestamps", "_n_points", "_cache")

    def __init__(self, data: Any, *, timestamps: Any | None = None, n_points: int = 256) -> None:
        from .similarity import _as_matrix, _normalize_channel_layout, _valid_timestamps

        points = operator.index(n_points)
        if points < 1:
            raise ValueError("n_points must be a positive integer")
        raw = _normalize_channel_layout(_as_matrix(data))
        ts = _valid_timestamps(timestamps, raw.shape[0])
        object.__setattr__(self, "_raw_values", _readonly_array(raw))
        object.__setattr__(self, "_timestamps", None if ts is None else _readonly_array(ts))
        object.__setattr__(self, "_n_points", points)
        object.__setattr__(self, "_cache", {})

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("PreparedSeries is immutable; construct another snapshot to change its configuration")

    @property
    def raw_values(self) -> np.ndarray:
        return self._raw_values

    @property
    def timestamps(self) -> np.ndarray | None:
        return self._timestamps

    @property
    def n_points(self) -> int:
        return self._n_points

    @property
    def n_channels(self) -> int:
        return self.raw_values.shape[1]

    @property
    def resampled(self) -> np.ndarray:
        from .similarity import _resampled_multichannel

        if "resampled" not in self._cache:
            values = _resampled_multichannel(self.raw_values, timestamps=self.timestamps, n_points=self.n_points)
            self._cache["resampled"] = _readonly_array(values)
        return self._cache["resampled"]

    def channel(self, index: int = 0, *, aggregate: bool = False) -> PreparedChannel:
        """Get one cached channel, or the aggregate-before-features trajectory."""
        if aggregate:
            if index != 0:
                raise IndexError("The aggregate trajectory has only one channel")
            key = ("channel", "aggregate")
            if key not in self._cache:
                values = np.nanmean(self.resampled, axis=1)
                self._cache[key] = PreparedChannel(values)
        else:
            index = operator.index(index)
            if not 0 <= index < self.n_channels:
                raise IndexError("channel index out of range")
            key = ("channel", index)
            if key not in self._cache:
                self._cache[key] = PreparedChannel(self.resampled[:, index])
        return self._cache[key]

    @property
    def cache_key(self) -> tuple[Any, ...]:
        if "cache_key" not in self._cache:
            digest = hashlib.blake2b(digest_size=20)
            digest.update(self.raw_values.tobytes())
            digest.update(b"no-timestamps" if self.timestamps is None else self.timestamps.tobytes())
            self._cache["cache_key"] = (
                PREPARED_SEMANTICS_VERSION,
                self.raw_values.shape,
                self.raw_values.dtype.str,
                self.n_points,
                "legacy_auto_channels",
                digest.hexdigest(),
            )
        return self._cache["cache_key"]

    def __reduce__(self) -> tuple[Any, tuple[Any, ...]]:
        return _restore_prepared_series, (self.raw_values, self.timestamps, self.n_points)

    def __repr__(self) -> str:
        return f"PreparedSeries(shape={self.raw_values.shape}, n_points={self.n_points})"


def _restore_prepared_series(values: np.ndarray, timestamps: np.ndarray | None, n_points: int) -> PreparedSeries:
    return PreparedSeries(values, timestamps=timestamps, n_points=n_points)
