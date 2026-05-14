"""Native pandas/tabular adaptors and richer long-table handling."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from .adapters import (
    DatasetAdaptor,
    EventStreamAdaptor,
    EventStreamInput,
    IrregularSubjectInput,
    NormalizedDataset,
    _TABLE_CHANNEL_KEYS,
    _TABLE_EVENT_TYPE_KEYS,
    _TABLE_SUBJECT_KEYS,
    _TABLE_TIMESTAMP_KEYS,
    _TABLE_VALUE_KEYS,
    _aggregate_time_series,
    _as_record_list,
    _find_first_key,
    _infer_sampling_rate,
    _merge_context_metadata,
    _prepare_event_stream_subject,
    _prepare_irregular_subject,
    normalize_dataset,
)
from .context import ProfilingContext

_TABLE_VISIT_KEYS = ("visit", "visit_id", "session", "session_id", "encounter", "encounter_id", "wave", "day", "epoch")
_TABLE_DEVICE_KEYS = ("device", "device_id", "source", "wearable", "sensor_platform", "modality")
_TABLE_PHASE_KEYS = ("phase", "study_phase", "arm", "condition", "segment", "period")
_SUPPORTED_FILE_SUFFIXES = {".parquet", ".pq", ".csv", ".tsv", ".json", ".jsonl"}


def _maybe_import_pandas() -> Any | None:
    try:
        import pandas as pd  # type: ignore
    except Exception:
        return None
    return pd


def _as_path(value: Any) -> Path | None:
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        return Path(value)
    return None


def _coerce_single_time(value: Any) -> float:
    if isinstance(value, (np.floating, np.integer, float, int)):
        return float(value)
    if isinstance(value, datetime):
        return float(value.timestamp())
    if isinstance(value, date):
        return float(datetime.combine(value, datetime.min.time()).timestamp())

    arr = np.asarray([value])
    if np.issubdtype(arr.dtype, np.datetime64):
        return float(arr.astype("datetime64[ns]").astype("int64")[0] / 1e9)

    pd = _maybe_import_pandas()
    if pd is not None:
        try:
            dt = pd.to_datetime([value], errors="coerce")
            if not bool(pd.isna(dt[0])):
                return float(dt.view("int64")[0] / 1e9)
        except Exception:
            pass

    return float(value)


def _coerce_time_array(values: Any) -> np.ndarray | None:
    if values is None:
        return None
    arr = np.asarray(values)
    if arr.ndim == 0:
        arr = arr.reshape(1)
    if np.issubdtype(arr.dtype, np.datetime64):
        return arr.astype("datetime64[ns]").astype("int64").astype(float) / 1e9
    try:
        return np.asarray(arr, dtype=float)
    except Exception:
        pd = _maybe_import_pandas()
        if pd is not None:
            try:
                dt = pd.to_datetime(arr, errors="coerce")
                mask = ~pd.isna(dt)
                if bool(np.all(mask)):
                    return np.asarray(dt.view("int64"), dtype=float) / 1e9
            except Exception:
                pass
        try:
            out = np.asarray([_coerce_single_time(v) for v in arr.tolist()], dtype=float)
            return out
        except Exception:
            return None


def _normalize_label(value: Any, prefix: str) -> str:
    if value is None:
        return prefix
    text = str(value)
    return text if text else prefix


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except Exception:
        return None
    return out if np.isfinite(out) else None


def _majority_label(items: Sequence[Any]) -> str | None:
    values = [str(item) for item in items if item is not None and str(item) != ""]
    if not values:
        return None
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0]


def _sort_key_for_visit(label: str, anchor: float) -> tuple[int, float, str]:
    try:
        numeric = float(label)
        return (0, numeric, label)
    except Exception:
        return (1, anchor, label)


def _load_tabular_file(path: Path) -> Any:
    pd = _maybe_import_pandas()
    if pd is None:
        raise ImportError(
            "Tabular file profiling for DataFrame/CSV/Parquet inputs requires pandas. "
            "Install echotime with a pandas-capable environment to use this adaptor."
        )
    suffix = path.suffix.lower()
    if suffix in {".parquet", ".pq"}:
        try:
            return pd.read_parquet(path)
        except Exception as exc:
            raise ImportError(
                "Reading parquet inputs requires a parquet engine such as pyarrow or fastparquet."
            ) from exc
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t")
    if suffix == ".json":
        try:
            return pd.read_json(path)
        except ValueError:
            return pd.read_json(path, lines=True)
    if suffix == ".jsonl":
        return pd.read_json(path, lines=True)
    raise ValueError(f"Unsupported tabular file suffix: {suffix}")


def _frame_time_key(df: Any) -> str | None:
    columns = {str(col).lower(): str(col) for col in getattr(df, "columns", [])}
    for candidate in _TABLE_TIMESTAMP_KEYS:
        if candidate in columns:
            return columns[candidate]
    return None


def _frame_value_key(df: Any) -> str | None:
    columns = {str(col).lower(): str(col) for col in getattr(df, "columns", [])}
    for candidate in _TABLE_VALUE_KEYS:
        if candidate in columns:
            return columns[candidate]
    return None


def _frame_long_id_keys(df: Any) -> dict[str, str | None]:
    first_row = {str(col): None for col in getattr(df, "columns", [])}
    return {
        "subject": _find_first_key(first_row, _TABLE_SUBJECT_KEYS),
        "visit": _find_first_key(first_row, _TABLE_VISIT_KEYS),
        "channel": _find_first_key(first_row, _TABLE_CHANNEL_KEYS),
        "device": _find_first_key(first_row, _TABLE_DEVICE_KEYS),
        "phase": _find_first_key(first_row, _TABLE_PHASE_KEYS),
        "event_type": _find_first_key(first_row, _TABLE_EVENT_TYPE_KEYS),
    }


def _build_records_from_wide_frame(df: Any) -> list[dict[str, Any]]:
    time_key = _frame_time_key(df)
    if time_key is None:
        raise ValueError("wide-frame conversion requires an explicit time/timestamp column.")
    keys = _frame_long_id_keys(df)
    excluded = {time_key}
    excluded.update(value for value in keys.values() if value is not None)

    measurement_columns: list[str] = []
    for column in getattr(df, "columns", []):
        name = str(column)
        if name in excluded:
            continue
        series = df[name]
        try:
            numeric = np.asarray(series, dtype=float)
        except Exception:
            continue
        if np.any(np.isfinite(numeric)):
            measurement_columns.append(name)

    if not measurement_columns:
        raise ValueError("No numeric measurement columns were available for wide-frame conversion.")

    records: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        base = {time_key: row[time_key]}
        for key_name, key in keys.items():
            if key is not None:
                base[key] = row.get(key)
        for column in measurement_columns:
            value = _safe_float(row.get(column))
            if value is None:
                continue
            rec = dict(base)
            rec["value"] = value
            rec["channel"] = column
            records.append(rec)
    return records


def _prepare_irregular_records_dataset(records: list[dict[str, Any]], context: ProfilingContext, *, native_adaptor: str) -> NormalizedDataset:
    first = records[0]
    timestamp_key = _find_first_key(first, _TABLE_TIMESTAMP_KEYS)
    value_key = _find_first_key(first, _TABLE_VALUE_KEYS)
    channel_key = _find_first_key(first, _TABLE_CHANNEL_KEYS)
    subject_key = _find_first_key(first, _TABLE_SUBJECT_KEYS)
    visit_key = _find_first_key(first, _TABLE_VISIT_KEYS)
    device_key = _find_first_key(first, _TABLE_DEVICE_KEYS)
    phase_key = _find_first_key(first, _TABLE_PHASE_KEYS)

    assert timestamp_key is not None and value_key is not None

    grouped_rows: dict[tuple[str, str], list[tuple[float, str, float, dict[str, Any]]]] = defaultdict(list)
    parent_order: list[str] = []
    channel_order: list[str] = []
    seen_channels: set[str] = set()

    for row in records:
        timestamp = _coerce_single_time(row[timestamp_key])
        value = _safe_float(row.get(value_key))
        if value is None or not np.isfinite(timestamp):
            continue
        parent_subject = _normalize_label(row.get(subject_key) if subject_key is not None else None, "subject_0")
        if parent_subject not in parent_order:
            parent_order.append(parent_subject)
        visit_id = _normalize_label(row.get(visit_key) if visit_key is not None else None, "visit_0")
        channel_label = _normalize_label(row.get(channel_key) if channel_key is not None else None, "value")
        if channel_label not in seen_channels:
            channel_order.append(channel_label)
            seen_channels.add(channel_label)
        grouped_rows[(parent_subject, visit_id)].append((timestamp, channel_label, float(value), row))

    parent_groups: dict[str, list[tuple[str, list[tuple[float, str, float, dict[str, Any]]]]]] = defaultdict(list)
    for (parent_subject, visit_id), rows in grouped_rows.items():
        parent_groups[parent_subject].append((visit_id, rows))

    subjects = []
    visit_parent_subject_ids: list[str] = []
    visit_ids: list[str] = []
    visit_orders: list[int] = []
    visit_anchors: list[float] = []
    visit_devices: list[str] = []
    visit_phases: list[str] = []

    for parent_subject in parent_order:
        groups = parent_groups[parent_subject]
        sortable: list[tuple[str, float, list[tuple[float, str, float, dict[str, Any]]]]] = []
        for visit_id, rows in groups:
            anchors = [item[0] for item in rows]
            anchor = float(np.min(anchors)) if anchors else float("nan")
            sortable.append((visit_id, anchor, rows))
        sortable.sort(key=lambda item: _sort_key_for_visit(item[0], item[1]))

        for visit_order, (visit_id, anchor, rows) in enumerate(sortable):
            per_channel: dict[str, tuple[list[float], list[float]]] = {
                label: ([], []) for label in channel_order
            }
            devices: list[Any] = []
            phases: list[Any] = []
            for timestamp, channel_label, value, raw_row in rows:
                ts_list, val_list = per_channel[channel_label]
                ts_list.append(timestamp)
                val_list.append(value)
                if device_key is not None:
                    devices.append(raw_row.get(device_key))
                if phase_key is not None:
                    phases.append(raw_row.get(phase_key))
            values_list = [np.asarray(per_channel[label][1], dtype=float) for label in channel_order]
            timestamps_list = [np.asarray(per_channel[label][0], dtype=float) for label in channel_order]
            subject = _prepare_irregular_subject(
                IrregularSubjectInput(
                    values=values_list,
                    timestamps=timestamps_list,
                    channel_names=channel_order,
                    metadata={"parent_subject_id": parent_subject, "visit_id": visit_id},
                )
            )
            subjects.append(subject)
            visit_parent_subject_ids.append(parent_subject)
            visit_ids.append(visit_id)
            visit_orders.append(int(visit_order))
            visit_anchors.append(float(anchor) if np.isfinite(anchor) else float(visit_order))
            visit_devices.append(_majority_label(devices) or "")
            visit_phases.append(_majority_label(phases) or "")

    if not subjects:
        raise ValueError("No finite rows were available after parsing the long table.")

    lengths = [subject.values.shape[0] for subject in subjects]
    channel_counts = [subject.values.shape[1] for subject in subjects]
    sample_rates = [_infer_sampling_rate(subject.timestamps) for subject in subjects]
    finite_rates = [rate for rate in sample_rates if rate is not None and np.isfinite(rate)]
    counts_by_parent = [visit_parent_subject_ids.count(parent) for parent in parent_order]

    metadata = {
        "input_kind": "record_table",
        "native_adaptor": native_adaptor,
        "table_semantics": "irregular_long_table",
        "n_subjects": int(len(parent_order)),
        "n_visit_units": int(len(subjects)),
        "n_visits_total": int(len(subjects)),
        "mean_visits_per_subject": float(np.mean(counts_by_parent)) if counts_by_parent else 1.0,
        "max_visits_per_subject": int(np.max(counts_by_parent)) if counts_by_parent else 1,
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
        "channel_labels": list(channel_order),
        "subject_ids": list(parent_order),
        "longitudinal_mode": bool(visit_key is not None or any(count > 1 for count in counts_by_parent)),
        "longitudinal_parent_subject_ids": list(visit_parent_subject_ids),
        "longitudinal_visit_ids": list(visit_ids),
        "longitudinal_visit_orders": list(visit_orders),
        "longitudinal_visit_anchors": list(visit_anchors),
    }
    if any(label for label in visit_devices):
        metadata["longitudinal_visit_devices"] = list(visit_devices)
    if any(label for label in visit_phases):
        metadata["longitudinal_visit_phases"] = list(visit_phases)

    normalized = NormalizedDataset(subjects=subjects, metadata=metadata)
    merged = ProfilingContext(
        domain=context.domain,
        timestamps=context.timestamps,
        time_axis=context.time_axis,
        channel_axis=context.channel_axis,
        subject_axis=context.subject_axis,
        sampling_rate=context.sampling_rate,
        tr=context.tr,
        channel_names=list(channel_order),
        roi_names=context.roi_names,
        network_labels=context.network_labels,
        subject_ids=list(parent_order),
        extra_metadata=dict(context.extra_metadata),
    )
    return _merge_context_metadata(normalized, merged)


def _prepare_event_records_dataset(records: list[dict[str, Any]], context: ProfilingContext, *, native_adaptor: str) -> NormalizedDataset:
    first = records[0]
    timestamp_key = _find_first_key(first, _TABLE_TIMESTAMP_KEYS)
    value_key = _find_first_key(first, _TABLE_VALUE_KEYS)
    channel_key = _find_first_key(first, _TABLE_CHANNEL_KEYS)
    subject_key = _find_first_key(first, _TABLE_SUBJECT_KEYS)
    event_type_key = _find_first_key(first, _TABLE_EVENT_TYPE_KEYS)
    visit_key = _find_first_key(first, _TABLE_VISIT_KEYS)
    device_key = _find_first_key(first, _TABLE_DEVICE_KEYS)
    phase_key = _find_first_key(first, _TABLE_PHASE_KEYS)

    assert timestamp_key is not None and value_key is not None

    timestamps: list[float] = []
    values: list[float] = []
    channels: list[Any] = []
    composite_subjects: list[str] = []
    event_types: list[Any] = []

    group_anchor: dict[str, float] = {}
    group_parent: dict[str, str] = {}
    group_visit: dict[str, str] = {}
    group_device: dict[str, list[Any]] = defaultdict(list)
    group_phase: dict[str, list[Any]] = defaultdict(list)
    parent_order: list[str] = []

    for row in records:
        timestamp = _coerce_single_time(row[timestamp_key])
        value = _safe_float(row.get(value_key))
        if value is None or not np.isfinite(timestamp):
            continue
        parent_subject = _normalize_label(row.get(subject_key) if subject_key is not None else None, "subject_0")
        if parent_subject not in parent_order:
            parent_order.append(parent_subject)
        visit_id = _normalize_label(row.get(visit_key) if visit_key is not None else None, "visit_0")
        composite_subject = f"{parent_subject}::{visit_id}" if visit_key is not None else parent_subject
        timestamps.append(timestamp)
        values.append(value)
        channels.append(row.get(channel_key) if channel_key is not None else (row.get(event_type_key) if event_type_key is not None else "event"))
        composite_subjects.append(composite_subject)
        event_types.append(row.get(event_type_key) if event_type_key is not None else None)
        group_parent[composite_subject] = parent_subject
        group_visit[composite_subject] = visit_id
        group_anchor[composite_subject] = min(timestamp, group_anchor.get(composite_subject, timestamp))
        if device_key is not None:
            group_device[composite_subject].append(row.get(device_key))
        if phase_key is not None:
            group_phase[composite_subject].append(row.get(phase_key))

    if not timestamps:
        raise ValueError("No finite rows were available after parsing the event table.")

    event_input = EventStreamInput(
        timestamps=np.asarray(timestamps, dtype=float),
        channels=np.asarray(channels, dtype=object),
        values=np.asarray(values, dtype=float),
        subjects=np.asarray(composite_subjects, dtype=object),
        event_types=None if event_type_key is None else np.asarray(event_types, dtype=object),
        domain=context.domain,
        metadata={**dict(context.extra_metadata), "native_adaptor": native_adaptor},
    )
    normalized = EventStreamAdaptor().adapt(event_input, context)

    composite_order = []
    seen: set[str] = set()
    for label in composite_subjects:
        if label not in seen:
            composite_order.append(label)
            seen.add(label)
    visit_parent_subject_ids = [group_parent[label] for label in composite_order]
    visit_ids = [group_visit[label] for label in composite_order]
    visit_anchors = [group_anchor[label] for label in composite_order]

    counts_by_parent = [visit_parent_subject_ids.count(parent) for parent in parent_order]
    metadata = dict(normalized.metadata)
    metadata.update(
        {
            "native_adaptor": native_adaptor,
            "table_semantics": "event_long_table",
            "n_subjects": int(len(parent_order)),
            "n_visit_units": int(len(composite_order)),
            "n_visits_total": int(len(composite_order)),
            "mean_visits_per_subject": float(np.mean(counts_by_parent)) if counts_by_parent else 1.0,
            "max_visits_per_subject": int(np.max(counts_by_parent)) if counts_by_parent else 1,
            "subject_ids": list(parent_order),
            "longitudinal_mode": bool(visit_key is not None or any(count > 1 for count in counts_by_parent)),
            "longitudinal_parent_subject_ids": list(visit_parent_subject_ids),
            "longitudinal_visit_ids": list(visit_ids),
            "longitudinal_visit_orders": [int(order) for order, _ in enumerate(composite_order)],
            "longitudinal_visit_anchors": list(visit_anchors),
        }
    )
    devices = [_majority_label(group_device[label]) or "" for label in composite_order]
    phases = [_majority_label(group_phase[label]) or "" for label in composite_order]
    if any(label for label in devices):
        metadata["longitudinal_visit_devices"] = devices
    if any(label for label in phases):
        metadata["longitudinal_visit_phases"] = phases
    return NormalizedDataset(subjects=normalized.subjects, metadata=metadata)


class EnhancedLongTableAdaptor:
    """Richer long-table adaptor for irregular panels, event tables, and longitudinal cohorts."""

    name = "record_table_v2"

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
            raise ValueError("record_table_v2 adaptor expected a non-empty list/DataFrame-like table.")
        first = records[0]
        event_type_key = _find_first_key(first, _TABLE_EVENT_TYPE_KEYS)
        native_adaptor = str(context.extra_metadata.get("native_adaptor", "record_table"))
        if event_type_key is not None:
            return _prepare_event_records_dataset(records, context, native_adaptor=native_adaptor)
        return _prepare_irregular_records_dataset(records, context, native_adaptor=native_adaptor)


class PandasDataFrameAdaptor:
    """Native adaptor for pandas.DataFrame inputs, including wide and long tabular forms."""

    name = "pandas"

    def can_handle(self, data: Any, context: ProfilingContext) -> bool:
        pd = _maybe_import_pandas()
        return bool(pd is not None and isinstance(data, pd.DataFrame))

    def adapt(self, data: Any, context: ProfilingContext) -> NormalizedDataset:
        pd = _maybe_import_pandas()
        if pd is None:
            raise ImportError("pandas is required for DataFrame adaptation.")
        assert isinstance(data, pd.DataFrame)

        df = data.copy()
        native_label = str(context.extra_metadata.get("native_adaptor", "pandas"))
        child_context = ProfilingContext(
            domain=context.domain,
            timestamps=context.timestamps,
            time_axis=context.time_axis,
            channel_axis=context.channel_axis,
            subject_axis=context.subject_axis,
            sampling_rate=context.sampling_rate,
            tr=context.tr,
            channel_names=context.channel_names,
            roi_names=context.roi_names,
            network_labels=context.network_labels,
            subject_ids=context.subject_ids,
            extra_metadata={**dict(context.extra_metadata), "native_adaptor": native_label, "source_object_type": type(data).__name__},
        )

        if isinstance(df.index, pd.MultiIndex):
            records = df.reset_index().to_dict(orient="records")
            return EnhancedLongTableAdaptor().adapt(records, child_context)

        time_key = _frame_time_key(df)
        value_key = _frame_value_key(df)
        id_keys = _frame_long_id_keys(df)
        has_long_keys = any(value is not None for value in id_keys.values())

        if time_key is not None and value_key is not None:
            return EnhancedLongTableAdaptor().adapt(df.to_dict(orient="records"), child_context)

        if time_key is not None and value_key is None:
            try:
                records = _build_records_from_wide_frame(df)
            except Exception:
                records = []
            if records:
                return EnhancedLongTableAdaptor().adapt(records, child_context)

        if has_long_keys and time_key is not None:
            records = _build_records_from_wide_frame(df)
            return EnhancedLongTableAdaptor().adapt(records, child_context)

        timestamps = None
        if time_key is not None and time_key in df.columns:
            timestamps = _coerce_time_array(df[time_key].to_numpy())
            df = df.drop(columns=[time_key])
        else:
            index_ts = _coerce_time_array(df.index.to_numpy())
            if index_ts is not None and index_ts.shape[0] == len(df) and not isinstance(df.index, pd.RangeIndex):
                timestamps = index_ts

        numeric_df = df.select_dtypes(include=[np.number, bool]).astype(float)
        if numeric_df.shape[1] == 0:
            raise ValueError(
                "The pandas DataFrame adaptor could not find numeric measurement columns. "
                "Use a long table with timestamp/value columns or provide numeric channel columns."
            )
        normalized = normalize_dataset(
            numeric_df.to_numpy(),
            timestamps=timestamps,
            time_axis=0,
            channel_axis=1,
            subject_axis=0,
        )
        merged = ProfilingContext(
            domain=context.domain,
            timestamps=context.timestamps,
            time_axis=context.time_axis,
            channel_axis=context.channel_axis,
            subject_axis=context.subject_axis,
            sampling_rate=context.sampling_rate,
            tr=context.tr,
            channel_names=[str(col) for col in numeric_df.columns],
            roi_names=context.roi_names,
            network_labels=context.network_labels,
            subject_ids=context.subject_ids,
            extra_metadata={**dict(context.extra_metadata), "native_adaptor": native_label, "source_object_type": type(data).__name__},
        )
        return _merge_context_metadata(normalized, merged)


class TabularFileAdaptor:
    """Read CSV/JSON/Parquet-like files through pandas and reuse the native DataFrame adaptor."""

    name = "tabular_file"

    def can_handle(self, data: Any, context: ProfilingContext) -> bool:
        path = _as_path(data)
        return bool(path is not None and path.suffix.lower() in _SUPPORTED_FILE_SUFFIXES)

    def adapt(self, data: Any, context: ProfilingContext) -> NormalizedDataset:
        path = _as_path(data)
        if path is None:
            raise ValueError("tabular_file adaptor expected a path-like input.")
        df = _load_tabular_file(path)
        suffix = path.suffix.lower()
        native_adaptor = "parquet_path" if suffix in {".parquet", ".pq"} else "tabular_file"
        child_context = ProfilingContext(
            domain=context.domain,
            timestamps=context.timestamps,
            time_axis=context.time_axis,
            channel_axis=context.channel_axis,
            subject_axis=context.subject_axis,
            sampling_rate=context.sampling_rate,
            tr=context.tr,
            channel_names=context.channel_names,
            roi_names=context.roi_names,
            network_labels=context.network_labels,
            subject_ids=context.subject_ids,
            extra_metadata={**dict(context.extra_metadata), "native_adaptor": native_adaptor, "source_path": str(path)},
        )
        return PandasDataFrameAdaptor().adapt(df, child_context)
