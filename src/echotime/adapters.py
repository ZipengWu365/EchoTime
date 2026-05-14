"""Input models, adaptation, and normalization utilities."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence

import numpy as np

from .context import ProfilingContext


@dataclass(slots=True)
class SubjectData:
    values: np.ndarray
    timestamps: np.ndarray | None
    missing_fraction: float
    channel_timestamps: list[np.ndarray] | None = None
    event_timestamps: np.ndarray | None = None
    event_channels: np.ndarray | None = None
    event_values: np.ndarray | None = None
    event_types: list[str] | None = None
    observation_mode: str = "dense"


@dataclass(slots=True)
class NormalizedDataset:
    subjects: list[SubjectData]
    metadata: dict[str, Any]


@dataclass(slots=True)
class FMRIInput:
    """Typed input wrapper for neuroimaging time-series collections."""

    values: Any
    tr: float | None = None
    timestamps: Any | Sequence[Any] | None = None
    roi_names: Sequence[str] | None = None
    network_labels: Sequence[str] | None = None
    subject_ids: Sequence[str] | None = None
    time_axis: int = 0
    channel_axis: int | None = -1
    subject_axis: int = 0


@dataclass(slots=True)
class EEGInput:
    """Typed input wrapper for electrophysiology time-series collections."""

    values: Any
    sampling_rate: float | None = None
    timestamps: Any | Sequence[Any] | None = None
    channel_names: Sequence[str] | None = None
    subject_ids: Sequence[str] | None = None
    montage_name: str | None = None
    time_axis: int = 0
    channel_axis: int | None = -1
    subject_axis: int = 0


@dataclass(slots=True)
class IrregularSubjectInput:
    """One subject with irregular timestamps.

    Univariate subjects can provide 1D ``values`` and 1D ``timestamps``.
    Multichannel asynchronous subjects can provide a list/tuple of 1D value arrays and
    a parallel list/tuple of timestamp arrays, one per channel.
    """

    values: Any
    timestamps: Any
    channel_names: Sequence[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class IrregularTimeSeriesInput:
    """Typed wrapper for irregularly sampled time-series datasets."""

    subjects: IrregularSubjectInput | Sequence[IrregularSubjectInput]
    domain: str | None = None
    channel_names: Sequence[str] | None = None
    subject_ids: Sequence[str] | None = None
    sampling_rate: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EventStreamInput:
    """Typed wrapper for sparse event streams.

    Parameters describe a long-form event table:
    ``timestamps`` is required; ``channels`` or ``event_types`` can specify event classes;
    ``values`` are optional marks or amplitudes and default to 1.0; ``subjects`` is optional.
    """

    timestamps: Any
    channels: Any | None = None
    values: Any | None = None
    subjects: Any | None = None
    event_types: Any | None = None
    channel_names: Sequence[str] | None = None
    subject_ids: Sequence[str] | None = None
    domain: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class DatasetAdaptor(Protocol):
    name: str

    def can_handle(self, data: Any, context: ProfilingContext) -> bool:
        ...

    def adapt(self, data: Any, context: ProfilingContext) -> NormalizedDataset:
        ...


_TABLE_TIMESTAMP_KEYS = ("timestamp", "timestamps", "time", "times")
_TABLE_VALUE_KEYS = ("value", "values", "measurement", "measure", "mark", "magnitude")
_TABLE_CHANNEL_KEYS = ("channel", "channels", "channel_id", "series", "variable", "metric", "sensor", "roi")
_TABLE_SUBJECT_KEYS = ("subject", "subjects", "subject_id", "patient", "participant", "case", "episode", "trial")
_TABLE_EVENT_TYPE_KEYS = ("event_type", "event", "type", "code", "label")


def _to_numpy(obj: Any) -> np.ndarray:
    if hasattr(obj, "to_numpy"):
        return np.asarray(obj.to_numpy(), dtype=float)
    return np.asarray(obj, dtype=float)


def _infer_sampling_rate(timestamps: np.ndarray | None) -> float | None:
    if timestamps is None:
        return None
    ts = np.asarray(timestamps, dtype=float).reshape(-1)
    ts = ts[np.isfinite(ts)]
    if ts.size < 3:
        return None
    delta = np.diff(ts)
    delta = delta[delta > 0]
    if delta.size < 2:
        return None
    step = float(np.median(delta))
    if step <= 0:
        return None
    return float(1.0 / step)


def _aggregate_time_series(timestamps: np.ndarray, values: np.ndarray, *, reducer: str = "mean") -> tuple[np.ndarray, np.ndarray]:
    ts = np.asarray(timestamps, dtype=float).reshape(-1)
    vals = np.asarray(values, dtype=float).reshape(-1)
    mask = np.isfinite(ts) & np.isfinite(vals)
    ts = ts[mask]
    vals = vals[mask]
    if ts.size == 0:
        return np.asarray([], dtype=float), np.asarray([], dtype=float)
    order = np.argsort(ts, kind="mergesort")
    ts = ts[order]
    vals = vals[order]
    unique_ts, inverse = np.unique(ts, return_inverse=True)
    if unique_ts.size == ts.size:
        return unique_ts, vals
    out = np.zeros(unique_ts.size, dtype=float)
    counts = np.zeros(unique_ts.size, dtype=float)
    for idx, value in zip(inverse, vals):
        out[idx] += value
        counts[idx] += 1.0
    if reducer == "mean":
        counts = np.where(counts <= 0, 1.0, counts)
        out = out / counts
    return unique_ts, out


def _prepare_subject(
    values: Any,
    *,
    time_axis: int,
    channel_axis: int | None,
    timestamps: Any | None,
) -> SubjectData:
    arr = _to_numpy(values)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    elif arr.ndim == 2:
        time_axis = time_axis % 2
        channel_axis = 1 if channel_axis is None else channel_axis % 2
        if time_axis == channel_axis:
            raise ValueError("time_axis and channel_axis must refer to different dimensions for 2D input.")
        arr = np.moveaxis(arr, [time_axis, channel_axis], [0, 1])
    else:
        raise ValueError("Each subject entry must be 1D or 2D.")

    arr = arr.astype(float, copy=False)
    missing_fraction = float(np.mean(~np.isfinite(arr))) if arr.size else 0.0
    ts = None if timestamps is None else np.asarray(timestamps, dtype=float).reshape(-1)
    if ts is not None and ts.shape[0] != arr.shape[0]:
        raise ValueError("timestamps must have the same length as the time axis.")
    channel_timestamps = None if ts is None else [ts.copy() for _ in range(arr.shape[1])]
    return SubjectData(values=arr, timestamps=ts, missing_fraction=missing_fraction, channel_timestamps=channel_timestamps, observation_mode="dense")


def _prepare_irregular_subject(entry: IrregularSubjectInput) -> SubjectData:
    values = entry.values
    timestamps = entry.timestamps

    if isinstance(values, (list, tuple)) or isinstance(timestamps, (list, tuple)):
        if not isinstance(values, (list, tuple)) or not isinstance(timestamps, (list, tuple)):
            raise ValueError("Irregular multichannel subjects must provide parallel lists/tuples for values and timestamps.")
        if len(values) != len(timestamps):
            raise ValueError("Irregular multichannel values and timestamps must have the same number of channels.")
        channel_ts: list[np.ndarray] = []
        channel_vals: list[np.ndarray] = []
        for val, ts in zip(values, timestamps):
            ts_clean, val_clean = _aggregate_time_series(np.asarray(ts, dtype=float), np.asarray(val, dtype=float), reducer="mean")
            channel_ts.append(ts_clean)
            channel_vals.append(val_clean)
    else:
        values_arr = np.asarray(values, dtype=float)
        timestamps_arr = np.asarray(timestamps, dtype=float)
        if values_arr.ndim == 1 and timestamps_arr.ndim == 1:
            ts_clean, val_clean = _aggregate_time_series(timestamps_arr, values_arr, reducer="mean")
            channel_ts = [ts_clean]
            channel_vals = [val_clean]
        elif values_arr.ndim == 2 and timestamps_arr.ndim == 2 and values_arr.shape == timestamps_arr.shape:
            channel_ts = []
            channel_vals = []
            for col in range(values_arr.shape[1]):
                ts_clean, val_clean = _aggregate_time_series(timestamps_arr[:, col], values_arr[:, col], reducer="mean")
                channel_ts.append(ts_clean)
                channel_vals.append(val_clean)
        else:
            raise ValueError(
                "IrregularSubjectInput must be univariate arrays, parallel channel lists, or 2D values/timestamps with matching shape."
            )

    nonempty_ts = [ts for ts in channel_ts if ts.size > 0]
    if not nonempty_ts:
        matrix = np.zeros((0, max(1, len(channel_ts))), dtype=float)
        return SubjectData(values=matrix, timestamps=np.asarray([], dtype=float), missing_fraction=0.0, channel_timestamps=channel_ts, observation_mode="irregular")

    union_ts = np.unique(np.concatenate(nonempty_ts))
    matrix = np.full((union_ts.size, len(channel_ts)), np.nan, dtype=float)
    for col, (ts, vals) in enumerate(zip(channel_ts, channel_vals)):
        if ts.size == 0:
            continue
        idx = np.searchsorted(union_ts, ts)
        matrix[idx, col] = vals
    missing_fraction = float(np.mean(~np.isfinite(matrix))) if matrix.size else 0.0
    return SubjectData(
        values=matrix,
        timestamps=union_ts,
        missing_fraction=missing_fraction,
        channel_timestamps=channel_ts,
        observation_mode="irregular",
    )


def _prepare_event_stream_subject(
    timestamps: Any,
    *,
    channels: Any | None = None,
    values: Any | None = None,
    event_types: Any | None = None,
    channel_names: Sequence[str] | None = None,
) -> tuple[SubjectData, list[str]]:
    ts = np.asarray(timestamps, dtype=float).reshape(-1)
    if values is None:
        vals = np.ones(ts.shape[0], dtype=float)
    else:
        vals = np.asarray(values, dtype=float).reshape(-1)
    if vals.shape[0] != ts.shape[0]:
        raise ValueError("EventStreamInput values must have the same length as timestamps.")

    if channels is not None:
        raw_channels = np.asarray(channels, dtype=object).reshape(-1)
        if raw_channels.shape[0] != ts.shape[0]:
            raise ValueError("EventStreamInput channels must have the same length as timestamps.")
    elif event_types is not None:
        raw_channels = np.asarray(event_types, dtype=object).reshape(-1)
        if raw_channels.shape[0] != ts.shape[0]:
            raise ValueError("EventStreamInput event_types must have the same length as timestamps.")
    else:
        raw_channels = np.zeros(ts.shape[0], dtype=int)

    raw_event_types = None
    if event_types is not None:
        raw_event_types = np.asarray(event_types, dtype=object).reshape(-1)
        if raw_event_types.shape[0] != ts.shape[0]:
            raise ValueError("EventStreamInput event_types must have the same length as timestamps.")

    mask = np.isfinite(ts) & np.isfinite(vals)
    ts = ts[mask]
    vals = vals[mask]
    raw_channels = raw_channels[mask]
    if raw_event_types is not None:
        raw_event_types = raw_event_types[mask]

    if ts.size == 0:
        matrix = np.zeros((0, max(1, len(channel_names or []))), dtype=float)
        subject = SubjectData(
            values=matrix,
            timestamps=np.asarray([], dtype=float),
            missing_fraction=0.0,
            channel_timestamps=None,
            event_timestamps=np.asarray([], dtype=float),
            event_channels=np.asarray([], dtype=int),
            event_values=np.asarray([], dtype=float),
            event_types=[] if raw_event_types is None else [],
            observation_mode="event_stream",
        )
        return subject, list(channel_names or ["event"])

    order = np.argsort(ts, kind="mergesort")
    ts = ts[order]
    vals = vals[order]
    raw_channels = raw_channels[order]
    if raw_event_types is not None:
        raw_event_types = raw_event_types[order]

    if channel_names is not None and len(channel_names) > 0:
        labels = [str(name) for name in channel_names]
        lookup = {label: idx for idx, label in enumerate(labels)}
        for key in raw_channels:
            label = str(key)
            if label not in lookup:
                lookup[label] = len(labels)
                labels.append(label)
        channel_idx = np.asarray([lookup[str(key)] for key in raw_channels], dtype=int)
    else:
        lookup: dict[str, int] = {}
        labels = []
        mapped = []
        for key in raw_channels:
            label = str(key)
            if label not in lookup:
                lookup[label] = len(labels)
                labels.append(label)
            mapped.append(lookup[label])
        channel_idx = np.asarray(mapped, dtype=int)

    unique_ts = np.unique(ts)
    matrix = np.zeros((unique_ts.size, len(labels)), dtype=float)
    time_lookup = {float(t): idx for idx, t in enumerate(unique_ts)}
    for t, c, v in zip(ts, channel_idx, vals):
        matrix[time_lookup[float(t)], int(c)] += float(v)

    channel_timestamps = [ts[channel_idx == col] for col in range(len(labels))]
    subject = SubjectData(
        values=matrix,
        timestamps=unique_ts,
        missing_fraction=0.0,
        channel_timestamps=channel_timestamps,
        event_timestamps=ts,
        event_channels=channel_idx,
        event_values=vals,
        event_types=None if raw_event_types is None else [str(item) for item in raw_event_types.tolist()],
        observation_mode="event_stream",
    )
    return subject, labels


def normalize_dataset(
    data: Any,
    *,
    timestamps: Any | Sequence[Any] | None = None,
    time_axis: int = 0,
    channel_axis: int | None = -1,
    subject_axis: int = 0,
) -> NormalizedDataset:
    """Normalize user input into a list of subject arrays of shape (time, channels)."""
    subjects: list[SubjectData] = []

    if isinstance(data, (list, tuple)):
        ts_list = [None] * len(data)
        if timestamps is not None:
            if not isinstance(timestamps, (list, tuple)) or len(timestamps) != len(data):
                raise ValueError("For list/tuple input, timestamps must be a list/tuple with one entry per subject.")
            ts_list = list(timestamps)
        for item, ts in zip(data, ts_list):
            subjects.append(_prepare_subject(item, time_axis=time_axis, channel_axis=channel_axis, timestamps=ts))
    else:
        arr = _to_numpy(data)
        if arr.ndim == 1:
            subjects = [_prepare_subject(arr, time_axis=0, channel_axis=None, timestamps=timestamps)]
        elif arr.ndim == 2:
            subjects = [_prepare_subject(arr, time_axis=time_axis, channel_axis=channel_axis, timestamps=timestamps)]
        elif arr.ndim == 3:
            if subject_axis == 0 and time_axis == 0 and (channel_axis is None or channel_axis == -1):
                time_axis = 1
                channel_axis = 2
            subject_axis = subject_axis % 3
            time_axis = time_axis % 3
            channel_axis = 2 if channel_axis is None else channel_axis % 3
            if len({subject_axis, time_axis, channel_axis}) != 3:
                raise ValueError("subject_axis, time_axis, and channel_axis must refer to different dimensions for 3D input.")
            arr = np.moveaxis(arr, [subject_axis, time_axis, channel_axis], [0, 1, 2])
            if timestamps is None:
                ts_list = [None] * arr.shape[0]
            elif isinstance(timestamps, (list, tuple)):
                if len(timestamps) != arr.shape[0]:
                    raise ValueError("For 3D input, timestamps must either be a shared array or a list matching the subject count.")
                ts_list = list(timestamps)
            else:
                ts_list = [timestamps] * arr.shape[0]
            for idx in range(arr.shape[0]):
                subjects.append(_prepare_subject(arr[idx], time_axis=0, channel_axis=1, timestamps=ts_list[idx]))
        else:
            raise ValueError("Input data must be 1D, 2D, 3D, or a list/tuple of 1D/2D arrays.")

    if not subjects:
        raise ValueError("Input data did not contain any subjects.")

    lengths = [subject.values.shape[0] for subject in subjects]
    channel_counts = [subject.values.shape[1] for subject in subjects]
    sample_rates = [_infer_sampling_rate(subject.timestamps) for subject in subjects]
    finite_rates = [rate for rate in sample_rates if rate is not None and np.isfinite(rate)]
    observation_modes = {subject.observation_mode for subject in subjects}
    event_total = int(sum(0 if subject.event_timestamps is None else subject.event_timestamps.size for subject in subjects))
    metadata = {
        "input_kind": type(data).__name__,
        "n_subjects": int(len(subjects)),
        "n_channels_total": int(sum(channel_counts)),
        "n_channels_median": int(np.median(channel_counts)),
        "n_channels_max": int(np.max(channel_counts)),
        "length_min": int(np.min(lengths)),
        "length_median": int(np.median(lengths)),
        "length_max": int(np.max(lengths)),
        "has_timestamps": any(subject.timestamps is not None for subject in subjects),
        "mean_missing_fraction": float(np.mean([subject.missing_fraction for subject in subjects])),
        "sampling_rate_median": float(np.median(finite_rates)) if finite_rates else None,
        "observation_mode": next(iter(observation_modes)) if len(observation_modes) == 1 else "mixed",
        "n_events_total": event_total,
    }
    return NormalizedDataset(subjects=subjects, metadata=metadata)


def _merge_context_metadata(normalized: NormalizedDataset, context: ProfilingContext) -> NormalizedDataset:
    metadata = dict(normalized.metadata)
    metadata["domain"] = context.resolved_domain
    if context.sampling_rate is not None:
        metadata["sampling_rate"] = float(context.sampling_rate)
    elif context.tr is not None and context.tr > 0:
        metadata["sampling_rate"] = float(1.0 / context.tr)
        metadata["tr"] = float(context.tr)
    elif metadata.get("sampling_rate_median") is not None:
        metadata["sampling_rate"] = float(metadata["sampling_rate_median"])
    if context.tr is not None:
        metadata["tr"] = float(context.tr)
    if context.channel_labels is not None:
        metadata["channel_labels"] = list(context.channel_labels)
    if context.network_labels is not None:
        metadata["network_labels"] = list(context.network_labels)
    if context.subject_ids is not None:
        metadata["subject_ids"] = list(context.subject_ids)
    metadata.update(context.extra_metadata)
    return NormalizedDataset(subjects=normalized.subjects, metadata=metadata)


def _get_info_value(info: Any, key: str) -> Any:
    if info is None:
        return None
    if isinstance(info, dict):
        return info.get(key)
    getter = getattr(info, "get", None)
    if callable(getter):
        try:
            return getter(key)
        except TypeError:
            pass
    return getattr(info, key, None)


def _extract_coord(obj: Any, name: str) -> Any | None:
    coords = getattr(obj, "coords", None)
    if coords is None:
        return None
    try:
        value = coords[name]
    except Exception:
        return None
    if hasattr(value, "values"):
        return value.values
    return value


def _as_record_list(data: Any) -> list[dict[str, Any]] | None:
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return [dict(row) for row in data]
    if hasattr(data, "columns"):
        columns = [str(col) for col in list(getattr(data, "columns"))]
        rows = []
        for idx in range(len(data)):
            row = {}
            for col in columns:
                value = data[col][idx]
                if hasattr(value, "item"):
                    try:
                        value = value.item()
                    except Exception:
                        pass
                row[col] = value
            rows.append(row)
        return rows
    if isinstance(data, dict):
        keys = list(data.keys())
        if not keys:
            return None
        lengths = []
        for key in keys:
            value = data[key]
            if isinstance(value, (list, tuple, np.ndarray)):
                lengths.append(len(value))
            else:
                return None
        if len(set(lengths)) != 1:
            return None
        rows = []
        length = lengths[0]
        for idx in range(length):
            row = {key: data[key][idx] for key in keys}
            rows.append(row)
        return rows
    return None


def _find_first_key(row: dict[str, Any], candidates: Sequence[str]) -> str | None:
    lower = {str(key).lower(): key for key in row.keys()}
    for candidate in candidates:
        if candidate in lower:
            return str(lower[candidate])
    return None


class GenericArrayAdaptor:
    name = "generic"

    def can_handle(self, data: Any, context: ProfilingContext) -> bool:
        return not isinstance(data, (FMRIInput, EEGInput, IrregularTimeSeriesInput, EventStreamInput))

    def adapt(self, data: Any, context: ProfilingContext) -> NormalizedDataset:
        normalized = normalize_dataset(
            data,
            timestamps=context.timestamps,
            time_axis=context.time_axis,
            channel_axis=context.channel_axis,
            subject_axis=context.subject_axis,
        )
        return _merge_context_metadata(normalized, context)


class FMRIAdaptor:
    name = "fmri"

    def can_handle(self, data: Any, context: ProfilingContext) -> bool:
        return isinstance(data, FMRIInput)

    def adapt(self, data: Any, context: ProfilingContext) -> NormalizedDataset:
        assert isinstance(data, FMRIInput)
        merged = ProfilingContext(
            domain="fmri",
            timestamps=data.timestamps if data.timestamps is not None else context.timestamps,
            time_axis=data.time_axis if data.time_axis is not None else context.time_axis,
            channel_axis=data.channel_axis if data.channel_axis is not None else context.channel_axis,
            subject_axis=data.subject_axis if data.subject_axis is not None else context.subject_axis,
            sampling_rate=context.sampling_rate,
            tr=data.tr if data.tr is not None else context.tr,
            roi_names=list(data.roi_names) if data.roi_names is not None else context.roi_names,
            network_labels=list(data.network_labels) if data.network_labels is not None else context.network_labels,
            subject_ids=list(data.subject_ids) if data.subject_ids is not None else context.subject_ids,
            extra_metadata=dict(context.extra_metadata),
        )
        normalized = normalize_dataset(
            data.values,
            timestamps=merged.timestamps,
            time_axis=merged.time_axis,
            channel_axis=merged.channel_axis,
            subject_axis=merged.subject_axis,
        )
        return _merge_context_metadata(normalized, merged)


class EEGAdaptor:
    name = "eeg"

    def can_handle(self, data: Any, context: ProfilingContext) -> bool:
        return isinstance(data, EEGInput)

    def adapt(self, data: Any, context: ProfilingContext) -> NormalizedDataset:
        assert isinstance(data, EEGInput)
        merged = ProfilingContext(
            domain="eeg",
            timestamps=data.timestamps if data.timestamps is not None else context.timestamps,
            time_axis=data.time_axis if data.time_axis is not None else context.time_axis,
            channel_axis=data.channel_axis if data.channel_axis is not None else context.channel_axis,
            subject_axis=data.subject_axis if data.subject_axis is not None else context.subject_axis,
            sampling_rate=data.sampling_rate if data.sampling_rate is not None else context.sampling_rate,
            tr=context.tr,
            channel_names=list(data.channel_names) if data.channel_names is not None else context.channel_names,
            roi_names=context.roi_names,
            network_labels=context.network_labels,
            subject_ids=list(data.subject_ids) if data.subject_ids is not None else context.subject_ids,
            extra_metadata={**dict(context.extra_metadata), **({"montage_name": data.montage_name} if data.montage_name else {})},
        )
        normalized = normalize_dataset(
            data.values,
            timestamps=merged.timestamps,
            time_axis=merged.time_axis,
            channel_axis=merged.channel_axis,
            subject_axis=merged.subject_axis,
        )
        return _merge_context_metadata(normalized, merged)


class IrregularTimeSeriesAdaptor:
    name = "irregular"

    def can_handle(self, data: Any, context: ProfilingContext) -> bool:
        return isinstance(data, IrregularTimeSeriesInput)

    def adapt(self, data: Any, context: ProfilingContext) -> NormalizedDataset:
        assert isinstance(data, IrregularTimeSeriesInput)
        subject_entries = data.subjects if isinstance(data.subjects, (list, tuple)) else [data.subjects]
        subjects = [_prepare_irregular_subject(entry) for entry in subject_entries]

        channel_counts = [subject.values.shape[1] for subject in subjects]
        lengths = [subject.values.shape[0] for subject in subjects]
        sample_rates = [_infer_sampling_rate(subject.timestamps) for subject in subjects]
        finite_rates = [rate for rate in sample_rates if rate is not None and np.isfinite(rate)]
        metadata = {
            "input_kind": type(data).__name__,
            "n_subjects": int(len(subjects)),
            "n_channels_total": int(sum(channel_counts)),
            "n_channels_median": int(np.median(channel_counts)) if channel_counts else 0,
            "n_channels_max": int(np.max(channel_counts)) if channel_counts else 0,
            "length_min": int(np.min(lengths)) if lengths else 0,
            "length_median": int(np.median(lengths)) if lengths else 0,
            "length_max": int(np.max(lengths)) if lengths else 0,
            "has_timestamps": True,
            "mean_missing_fraction": float(np.mean([subject.missing_fraction for subject in subjects])) if subjects else 0.0,
            "sampling_rate_median": float(np.median(finite_rates)) if finite_rates else None,
            "observation_mode": "irregular",
            "n_events_total": 0,
            "native_adaptor": "irregular",
        }
        merged = ProfilingContext(
            domain=data.domain or context.domain,
            timestamps=context.timestamps,
            time_axis=context.time_axis,
            channel_axis=context.channel_axis,
            subject_axis=context.subject_axis,
            sampling_rate=data.sampling_rate if data.sampling_rate is not None else context.sampling_rate,
            tr=context.tr,
            channel_names=list(data.channel_names) if data.channel_names is not None else context.channel_names,
            roi_names=context.roi_names,
            network_labels=context.network_labels,
            subject_ids=list(data.subject_ids) if data.subject_ids is not None else context.subject_ids,
            extra_metadata={**dict(context.extra_metadata), **dict(data.metadata)},
        )
        normalized = NormalizedDataset(subjects=subjects, metadata=metadata)
        return _merge_context_metadata(normalized, merged)


class EventStreamAdaptor:
    name = "event_stream"

    def can_handle(self, data: Any, context: ProfilingContext) -> bool:
        return isinstance(data, EventStreamInput)

    def adapt(self, data: Any, context: ProfilingContext) -> NormalizedDataset:
        assert isinstance(data, EventStreamInput)
        timestamps = np.asarray(data.timestamps, dtype=float).reshape(-1)
        n = timestamps.shape[0]
        values = np.ones(n, dtype=float) if data.values is None else np.asarray(data.values, dtype=float).reshape(-1)
        if values.shape[0] != n:
            raise ValueError("EventStreamInput values must align with timestamps.")
        channels = None if data.channels is None else np.asarray(data.channels, dtype=object).reshape(-1)
        if channels is not None and channels.shape[0] != n:
            raise ValueError("EventStreamInput channels must align with timestamps.")
        event_types = None if data.event_types is None else np.asarray(data.event_types, dtype=object).reshape(-1)
        if event_types is not None and event_types.shape[0] != n:
            raise ValueError("EventStreamInput event_types must align with timestamps.")
        subjects_raw = None if data.subjects is None else np.asarray(data.subjects, dtype=object).reshape(-1)
        if subjects_raw is not None and subjects_raw.shape[0] != n:
            raise ValueError("EventStreamInput subjects must align with timestamps.")

        if subjects_raw is None:
            unique_subjects = [None]
            masks = [np.ones(n, dtype=bool)]
        else:
            unique_subjects = []
            masks = []
            for label in subjects_raw.tolist():
                if label not in unique_subjects:
                    unique_subjects.append(label)
            for label in unique_subjects:
                masks.append(subjects_raw == label)

        subjects: list[SubjectData] = []
        derived_channel_names: list[str] | None = list(data.channel_names) if data.channel_names is not None else None
        for mask in masks:
            subject, labels = _prepare_event_stream_subject(
                timestamps[mask],
                channels=None if channels is None else channels[mask],
                values=values[mask],
                event_types=None if event_types is None else event_types[mask],
                channel_names=derived_channel_names,
            )
            if derived_channel_names is None:
                derived_channel_names = labels
            else:
                for label in labels:
                    if label not in derived_channel_names:
                        derived_channel_names.append(label)
            subjects.append(subject)

        channel_counts = [subject.values.shape[1] for subject in subjects]
        lengths = [subject.values.shape[0] for subject in subjects]
        sample_rates = [_infer_sampling_rate(subject.timestamps) for subject in subjects]
        finite_rates = [rate for rate in sample_rates if rate is not None and np.isfinite(rate)]
        metadata = {
            "input_kind": type(data).__name__,
            "n_subjects": int(len(subjects)),
            "n_channels_total": int(sum(channel_counts)),
            "n_channels_median": int(np.median(channel_counts)) if channel_counts else 0,
            "n_channels_max": int(np.max(channel_counts)) if channel_counts else 0,
            "length_min": int(np.min(lengths)) if lengths else 0,
            "length_median": int(np.median(lengths)) if lengths else 0,
            "length_max": int(np.max(lengths)) if lengths else 0,
            "has_timestamps": True,
            "mean_missing_fraction": 0.0,
            "sampling_rate_median": float(np.median(finite_rates)) if finite_rates else None,
            "observation_mode": "event_stream",
            "n_events_total": int(n),
            "native_adaptor": "event_stream",
        }
        merged = ProfilingContext(
            domain=data.domain or context.domain,
            timestamps=context.timestamps,
            time_axis=context.time_axis,
            channel_axis=context.channel_axis,
            subject_axis=context.subject_axis,
            sampling_rate=context.sampling_rate,
            tr=context.tr,
            channel_names=derived_channel_names if derived_channel_names is not None else context.channel_names,
            roi_names=context.roi_names,
            network_labels=context.network_labels,
            subject_ids=list(data.subject_ids) if data.subject_ids is not None else ([str(x) for x in unique_subjects if x is not None] or context.subject_ids),
            extra_metadata={**dict(context.extra_metadata), **dict(data.metadata)},
        )
        normalized = NormalizedDataset(subjects=subjects, metadata=metadata)
        return _merge_context_metadata(normalized, merged)


class LongTableAdaptor:
    """Duck-typed adaptor for long-form record tables from CSV/JSON/DataFrame-like inputs."""

    name = "record_table"

    def can_handle(self, data: Any, context: ProfilingContext) -> bool:
        records = _as_record_list(data)
        if not records:
            return False
        timestamp_key = _find_first_key(records[0], _TABLE_TIMESTAMP_KEYS)
        value_key = _find_first_key(records[0], _TABLE_VALUE_KEYS)
        return timestamp_key is not None and value_key is not None

    def adapt(self, data: Any, context: ProfilingContext) -> NormalizedDataset:
        records = _as_record_list(data)
        if not records:
            raise ValueError("record_table adaptor expected a non-empty list/DataFrame-like table.")

        first = records[0]
        timestamp_key = _find_first_key(first, _TABLE_TIMESTAMP_KEYS)
        value_key = _find_first_key(first, _TABLE_VALUE_KEYS)
        if timestamp_key is None or value_key is None:
            raise ValueError("record_table adaptor requires timestamp/time and value columns.")
        channel_key = _find_first_key(first, _TABLE_CHANNEL_KEYS)
        subject_key = _find_first_key(first, _TABLE_SUBJECT_KEYS)
        event_type_key = _find_first_key(first, _TABLE_EVENT_TYPE_KEYS)

        timestamps = []
        values = []
        channels = [] if channel_key is not None else None
        subjects = [] if subject_key is not None else None
        event_types = [] if event_type_key is not None else None
        for row in records:
            timestamps.append(float(row[timestamp_key]))
            values.append(float(row[value_key]))
            if channel_key is not None:
                channels.append(row[channel_key])
            if subject_key is not None:
                subjects.append(row[subject_key])
            if event_type_key is not None:
                event_types.append(row[event_type_key])

        event_input = EventStreamInput(
            timestamps=np.asarray(timestamps, dtype=float),
            channels=None if channels is None else np.asarray(channels, dtype=object),
            values=np.asarray(values, dtype=float),
            subjects=None if subjects is None else np.asarray(subjects, dtype=object),
            event_types=None if event_types is None else np.asarray(event_types, dtype=object),
            domain=context.domain,
            metadata={**dict(context.extra_metadata), "native_adaptor": "record_table"},
        )
        return EventStreamAdaptor().adapt(event_input, context)


class MNEObjectAdaptor:
    """Duck-typed adaptor for MNE Raw/Epochs/Evoked-like objects."""

    name = "mne"

    def can_handle(self, data: Any, context: ProfilingContext) -> bool:
        return hasattr(data, "get_data") and hasattr(data, "info")

    def adapt(self, data: Any, context: ProfilingContext) -> NormalizedDataset:
        raw = data.get_data()
        arr = np.asarray(raw, dtype=float)
        info = getattr(data, "info", None)
        sfreq = _get_info_value(info, "sfreq")
        ch_names = getattr(data, "ch_names", None) or _get_info_value(info, "ch_names")
        times = getattr(data, "times", None)
        domain = context.domain or "eeg"

        if arr.ndim == 2:
            normalized = normalize_dataset(arr, timestamps=times, time_axis=1, channel_axis=0, subject_axis=0)
        elif arr.ndim == 3:
            normalized = normalize_dataset(arr, timestamps=times, time_axis=2, channel_axis=1, subject_axis=0)
        else:
            raise ValueError("Unsupported MNE-like object: get_data() must return 2D or 3D arrays.")

        merged = ProfilingContext(
            domain=domain,
            timestamps=context.timestamps,
            time_axis=context.time_axis,
            channel_axis=context.channel_axis,
            subject_axis=context.subject_axis,
            sampling_rate=float(sfreq) if sfreq is not None else context.sampling_rate,
            tr=context.tr,
            channel_names=list(ch_names) if ch_names is not None else context.channel_names,
            roi_names=context.roi_names,
            network_labels=context.network_labels,
            subject_ids=context.subject_ids,
            extra_metadata={**dict(context.extra_metadata), "native_adaptor": "mne", "source_object_type": type(data).__name__},
        )
        return _merge_context_metadata(normalized, merged)


class XarrayDataArrayAdaptor:
    """Duck-typed adaptor for xarray.DataArray-like objects."""

    name = "xarray"

    _TIME_NAMES = {"time", "times", "sample", "samples", "frame", "frames"}
    _CHANNEL_NAMES = {"channel", "channels", "roi", "rois", "region", "regions", "sensor", "sensors", "node", "nodes", "feature", "features"}
    _SUBJECT_NAMES = {"subject", "subjects", "participant", "participants", "trial", "trials", "epoch", "epochs"}

    def can_handle(self, data: Any, context: ProfilingContext) -> bool:
        return hasattr(data, "dims") and hasattr(data, "values")

    def adapt(self, data: Any, context: ProfilingContext) -> NormalizedDataset:
        arr = np.asarray(getattr(data, "values"), dtype=float)
        dims = tuple(str(dim).lower() for dim in getattr(data, "dims"))
        if arr.ndim != len(dims):
            raise ValueError("xarray-like objects must expose values with the same dimensionality as dims.")

        time_dim = next((idx for idx, name in enumerate(dims) if name in self._TIME_NAMES), context.time_axis % max(arr.ndim, 1))
        remaining = [idx for idx in range(arr.ndim) if idx != time_dim]
        channel_dim = next((idx for idx, name in enumerate(dims) if name in self._CHANNEL_NAMES and idx != time_dim), None)
        subject_dim = next((idx for idx, name in enumerate(dims) if name in self._SUBJECT_NAMES and idx not in {time_dim, channel_dim}), None)

        if arr.ndim == 1:
            normalized = normalize_dataset(arr, timestamps=_extract_coord(data, getattr(data, "dims")[time_dim]), time_axis=0, channel_axis=None, subject_axis=0)
        elif arr.ndim == 2:
            if channel_dim is None:
                channel_dim = remaining[0]
            normalized = normalize_dataset(
                arr,
                timestamps=_extract_coord(data, getattr(data, "dims")[time_dim]),
                time_axis=time_dim,
                channel_axis=channel_dim,
                subject_axis=0,
            )
        elif arr.ndim == 3:
            if subject_dim is None:
                for idx in range(arr.ndim):
                    if idx not in {time_dim, channel_dim}:
                        subject_dim = idx
                        break
            if channel_dim is None:
                for idx in range(arr.ndim):
                    if idx not in {time_dim, subject_dim}:
                        channel_dim = idx
                        break
            if subject_dim is None or channel_dim is None:
                raise ValueError("Could not infer subject and channel dimensions from the xarray-like object.")
            normalized = normalize_dataset(
                arr,
                timestamps=_extract_coord(data, getattr(data, "dims")[time_dim]),
                time_axis=time_dim,
                channel_axis=channel_dim,
                subject_axis=subject_dim,
            )
        else:
            raise ValueError("xarray-like adaptor currently supports 1D, 2D, or 3D DataArray-like inputs.")

        channel_dim_name = getattr(data, "dims")[channel_dim] if channel_dim is not None and arr.ndim > 1 else None
        subject_dim_name = getattr(data, "dims")[subject_dim] if subject_dim is not None and arr.ndim > 2 else None
        channel_names = None if channel_dim_name is None else _extract_coord(data, channel_dim_name)
        subject_ids = None if subject_dim_name is None else _extract_coord(data, subject_dim_name)
        merged = ProfilingContext(
            domain=context.domain,
            timestamps=context.timestamps,
            time_axis=context.time_axis,
            channel_axis=context.channel_axis,
            subject_axis=context.subject_axis,
            sampling_rate=context.sampling_rate,
            tr=context.tr,
            channel_names=list(channel_names) if channel_names is not None else context.channel_names,
            roi_names=context.roi_names,
            network_labels=context.network_labels,
            subject_ids=list(subject_ids) if subject_ids is not None else context.subject_ids,
            extra_metadata={**dict(context.extra_metadata), "native_adaptor": "xarray", "source_object_type": type(data).__name__},
        )
        return _merge_context_metadata(normalized, merged)
