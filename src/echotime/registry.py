"""Extension registry for adaptors and metric plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .adapters import DatasetAdaptor, GenericArrayAdaptor, NormalizedDataset
from .context import ProfilingContext


@dataclass(slots=True)
class PluginResult:
    metrics: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


class MetricPlugin(Protocol):
    name: str

    def applies(self, normalized: NormalizedDataset, context: ProfilingContext) -> bool:
        ...

    def compute(self, normalized: NormalizedDataset, context: ProfilingContext) -> PluginResult:
        ...


@dataclass(slots=True)
class ExtensionRegistry:
    adaptors: list[DatasetAdaptor]
    plugins: list[MetricPlugin]

    def resolve_adaptor(self, data: Any, context: ProfilingContext) -> DatasetAdaptor:
        for adaptor in self.adaptors:
            if adaptor.can_handle(data, context):
                return adaptor
        raise ValueError("No registered adaptor could handle the provided input.")

    def active_plugins(self, normalized: NormalizedDataset, context: ProfilingContext) -> list[MetricPlugin]:
        return [plugin for plugin in self.plugins if plugin.applies(normalized, context)]

    def register_adaptor(self, adaptor: DatasetAdaptor) -> None:
        self.adaptors.insert(0, adaptor)

    def register_plugin(self, plugin: MetricPlugin) -> None:
        self.plugins.insert(0, plugin)


_GENERIC_ADAPTOR = GenericArrayAdaptor()
_CUSTOM_ADAPTORS: list[DatasetAdaptor] = []
_CUSTOM_PLUGINS: list[MetricPlugin] = []


def _builtins() -> ExtensionRegistry:
    from .adapters import (
        EEGAdaptor,
        EventStreamAdaptor,
        FMRIAdaptor,
        IrregularTimeSeriesAdaptor,
        MNEObjectAdaptor,
        XarrayDataArrayAdaptor,
    )
    from .longitudinal import LongitudinalMetricsPlugin
    from .plugins import EEGBandpowerPlugin, EventStreamPlugin, FMRIMetricsPlugin, IrregularObservationPlugin, NetworkMetricsPlugin
    from .tabular import EnhancedLongTableAdaptor, PandasDataFrameAdaptor, TabularFileAdaptor

    adaptors = list(_CUSTOM_ADAPTORS) + [
        FMRIAdaptor(),
        EEGAdaptor(),
        IrregularTimeSeriesAdaptor(),
        EventStreamAdaptor(),
        TabularFileAdaptor(),
        PandasDataFrameAdaptor(),
        EnhancedLongTableAdaptor(),
        MNEObjectAdaptor(),
        XarrayDataArrayAdaptor(),
        _GENERIC_ADAPTOR,
    ]
    plugins = list(_CUSTOM_PLUGINS) + [
        IrregularObservationPlugin(),
        EventStreamPlugin(),
        NetworkMetricsPlugin(),
        FMRIMetricsPlugin(),
        EEGBandpowerPlugin(),
        LongitudinalMetricsPlugin(),
    ]
    return ExtensionRegistry(adaptors=adaptors, plugins=plugins)


def get_registry() -> ExtensionRegistry:
    return _builtins()


def register_adaptor(adaptor: DatasetAdaptor) -> None:
    _CUSTOM_ADAPTORS.insert(0, adaptor)


def register_plugin(plugin: MetricPlugin) -> None:
    _CUSTOM_PLUGINS.insert(0, plugin)


def clear_custom_extensions() -> None:
    _CUSTOM_ADAPTORS.clear()
    _CUSTOM_PLUGINS.clear()
