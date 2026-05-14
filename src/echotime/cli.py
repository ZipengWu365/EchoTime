"""Command-line interface for EchoTime."""

from __future__ import annotations

import argparse
import json
import locale
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np

from .agent import agent_drive, agent_driving_guide
from .agent_tools import mcp_tool_descriptors, openai_function_schemas, tool_schemas, ts_compare, ts_profile
from .gallery import case_gallery
from .guide import about, api_reference, docs_index, environment_matrix, scenario_guide, user_guide, workflow_recommendation
from .hotcases import hot_case_gallery, similarity_playbook
from .compat import compatibility_guide, write_compatibility_constraints
from .consistency import asset_consistency_report
from .homepage import project_homepage_html
from .playground import project_playground_html
from .sitebundle import write_pages_bundle
from .launchpad import project_launchpad_html
from .doctor import environment_doctor
from .demo_server import run_demo_server
from .positioning import agent_manifest, coverage_matrix, ecosystem_positioning, tooling_router
from .profile import profile_dataset
from .repo_docs import agent_schema_guide, case_studies_guide, doctor_guide, github_readme, installation_guide, integration_templates_guide, live_demo_guide, pages_deploy_guide, pypi_long_description, quickstart_guide, routing_contract_guide, starter_datasets_guide, start_here_guide, trust_guide, utility_benchmark_guide, zero_install_guide
from .schema import schema_dict
from .similarity import compare_profiles, compare_series
from .similarity_method_atlas import similarity_method_atlas_guide


_TABLE_KEYS = {"timestamp", "timestamps", "time", "times"}


def _load_numeric_array(path: Path, npz_key: str | None = None) -> Any:
    suffix = path.suffix.lower()
    if suffix == ".npy":
        return np.load(path, allow_pickle=True)
    if suffix == ".npz":
        archive = np.load(path, allow_pickle=True)
        if npz_key is None:
            keys = list(archive.keys())
            if not keys:
                raise ValueError("The .npz archive did not contain any arrays.")
            npz_key = keys[0]
        return archive[npz_key]
    if suffix in {".csv", ".txt"}:
        delimiter = "," if suffix == ".csv" else None
        return np.genfromtxt(path, delimiter=delimiter)
    raise ValueError(f"Unsupported numeric input format: {suffix}")


def _load_table(path: Path) -> Any:
    suffix = path.suffix.lower()
    if suffix in {".parquet", ".pq", ".tsv", ".jsonl", ".json", ".csv"}:
        return path
    raise ValueError(f"Unsupported table input format: {suffix}. Use .csv, .tsv, .json, .jsonl, or .parquet for table mode.")


def _detect_table_csv(path: Path) -> bool:
    if path.suffix.lower() != ".csv":
        return False
    try:
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
    except Exception:
        return False
    header = {part.strip().lower() for part in first_line.split(",")}
    return bool(header & _TABLE_KEYS)


def _load_input(path: Path, *, input_mode: str, npz_key: str | None) -> Any:
    if input_mode == "array":
        return _load_numeric_array(path, npz_key=npz_key)
    if input_mode == "table":
        return _load_table(path)
    if path.suffix.lower() in {".json", ".jsonl", ".parquet", ".pq", ".tsv"}:
        return _load_table(path)
    if _detect_table_csv(path):
        return _load_table(path)
    return _load_numeric_array(path, npz_key=npz_key)


def _load_labels(path: Path | None) -> list[str] | None:
    if path is None:
        return None
    text = path.read_text(encoding="utf-8")
    if "," in text and "\n" not in text:
        items = [item.strip() for item in text.split(",")]
    else:
        items = [line.strip() for line in text.splitlines()]
    return [item for item in items if item]


def _render_guide(args: argparse.Namespace) -> str:
    guide_format = args.guide_format
    if args.guide == "about":
        return about(format=guide_format)
    if args.guide == "api":
        return api_reference(format=guide_format)
    if args.guide == "scenarios":
        return scenario_guide(domain=args.domain, environment=args.environment, scenario=args.scenario, format=guide_format)
    if args.guide == "environments":
        return environment_matrix(format=guide_format)
    if args.guide == "workflow":
        return workflow_recommendation(domain=args.domain, environment=args.environment, scenario=args.scenario, format=guide_format)
    if args.guide == "cases":
        return case_gallery(domain=args.domain, audience=args.audience, environment=args.environment, format=guide_format)
    if args.guide == "hot-cases":
        return hot_case_gallery(audience=args.audience, format=guide_format)
    if args.guide == "similarity":
        return similarity_playbook(format=guide_format)
    if args.guide == "agent-driving":
        return agent_driving_guide(format=guide_format)
    if args.guide == "homepage":
        html = project_homepage_html(version="0.17.1")
        if guide_format == "json":
            return json.dumps({"html": html}, indent=2)
        return html
    if args.guide == "playground":
        html = project_playground_html(version="0.17.1")
        if guide_format == "json":
            return json.dumps({"html": html}, indent=2)
        return html
    if args.guide == "start-here":
        if guide_format == "json":
            return json.dumps({"html": project_launchpad_html(version="0.17.1"), "markdown": start_here_guide(format="markdown")}, indent=2)
        return project_launchpad_html(version="0.17.1") if guide_format == "text" else start_here_guide(format=guide_format)
    if args.guide == "doctor":
        payload = environment_doctor(format="dict") if guide_format == "json" else doctor_guide(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "compatibility":
        payload = compatibility_guide(format="dict") if guide_format == "json" else compatibility_guide(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "asset-audit":
        payload = asset_consistency_report(format="dict") if guide_format == "json" else asset_consistency_report(format="markdown")
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "user-guide":
        return user_guide(format=guide_format)
    if args.guide == "ecosystem":
        return ecosystem_positioning(format=guide_format)
    if args.guide == "coverage":
        return coverage_matrix(format=guide_format)
    if args.guide == "agent-manifest":
        return json.dumps(agent_manifest(format="json"), indent=2) if guide_format == "json" else agent_manifest(format=guide_format)
    if args.guide == "github-readme":
        payload = github_readme(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "pypi-description":
        payload = pypi_long_description(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "routing":
        payload = tooling_router(args.task or "", format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "docs-index":
        return docs_index(format=guide_format)
    if args.guide == "quickstart":
        payload = quickstart_guide(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "installation":
        payload = installation_guide(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "zero-install":
        payload = zero_install_guide(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "pages":
        payload = pages_deploy_guide(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "live-demo":
        payload = live_demo_guide(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "integrations":
        payload = integration_templates_guide(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "case-studies":
        payload = case_studies_guide(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "trust":
        payload = trust_guide(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "starter-datasets":
        payload = starter_datasets_guide(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "agent-schemas":
        payload = agent_schema_guide(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "routing-contracts":
        payload = routing_contract_guide(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "utility-benchmark":
        payload = utility_benchmark_guide(format=guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    if args.guide == "similarity-methods":
        payload = similarity_method_atlas_guide(format="dict" if guide_format == "json" else guide_format)
        return json.dumps(payload, indent=2) if guide_format == "json" else payload
    raise ValueError(f"Unknown guide topic: {args.guide}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare time series with EchoTime, profile structural context when needed, run an agent-driven compact workflow, or print the built-in guides that explain the API, release surface, and supported environments."
        )
    )
    parser.add_argument("input", type=Path, nargs="?", help="Path to .npy, .npz, .csv, .tsv, .txt, .json, or .parquet input.")
    parser.add_argument("--timestamps", type=Path, default=None, help="Optional timestamp file (.npy, .npz, .csv, .txt) for the primary input.")
    parser.add_argument("--reference", type=Path, default=None, help="Optional second input. When provided, EchoTime can run similarity comparison or an agent-driven comparison workflow.")
    parser.add_argument("--reference-timestamps", type=Path, default=None, help="Optional timestamp file for the reference input.")
    parser.add_argument("--npz-key", type=str, default=None, help="Optional key to load from a .npz archive.")
    parser.add_argument("--input-mode", choices=["auto", "array", "table"], default="auto", help="How to interpret the primary input file.")
    parser.add_argument("--reference-input-mode", choices=["auto", "array", "table"], default="auto", help="How to interpret the reference input file in similarity mode.")
    parser.add_argument("--time-axis", type=int, default=0, help="Time axis. Default: 0 for 1D/2D and inferred as 1 for standard 3D (subjects, time, channels).")
    parser.add_argument("--channel-axis", type=int, default=-1, help="Channel axis for 2D/3D input. Default: -1.")
    parser.add_argument("--subject-axis", type=int, default=0, help="Subject axis for 3D input. Default: 0.")
    parser.add_argument("--domain", type=str, default="generic", help="Optional domain specialization, such as generic, fmri, eeg, clinical, wearable, traffic, product, or energy.")
    parser.add_argument("--environment", choices=["notebook", "python_script", "cli_batch", "pandas_pipeline", "neuro_stack", "ml_benchmark"], default=None, help="Optional environment filter for guide commands.")
    parser.add_argument("--audience", type=str, default="general", help="Audience label for guides and plain-language report outputs, for example general, clinical, product, neuroscience, or agent.")
    parser.add_argument("--scenario", type=str, default=None, help="Optional scenario key for guide commands.")
    parser.add_argument("--task", type=str, default=None, help="Optional free-text task description for tooling routing guides.")
    parser.add_argument("--sampling-rate", type=float, default=None, help="Optional sampling rate in Hz.")
    parser.add_argument("--tr", type=float, default=None, help="Optional fMRI TR in seconds.")
    parser.add_argument("--bootstrap", type=int, default=0, help="Optional number of bootstrap resamples for reliability intervals.")
    parser.add_argument("--random-state", type=int, default=None, help="Random seed for bootstrap resampling.")
    parser.add_argument("--channel-names", type=Path, default=None, help="Optional file containing channel names.")
    parser.add_argument("--roi-names", type=Path, default=None, help="Optional file containing ROI names.")
    parser.add_argument("--network-labels", type=Path, default=None, help="Optional file containing one network label per channel/ROI.")
    parser.add_argument("--similarity-mode", choices=["series", "profile"], default="series", help="In comparison mode, choose raw-series similarity or ontology-profile similarity.")
    parser.add_argument("--agent-goal", type=str, default=None, help="Optional agent-driving goal. When provided, EchoTime runs the agent layer instead of the plain profiling/similarity path.")
    parser.add_argument("--agent-budget", choices=["lean", "balanced", "deep"], default="lean", help="Token budget for the agent-driving layer.")
    parser.add_argument("--rolling-window", type=int, default=None, help="Optional rolling window for agent-driven comparison goals.")
    parser.add_argument("--rolling-step", type=int, default=1, help="Step size for agent-driven rolling similarity.")
    parser.add_argument("--no-stop-on-clear-signal", action="store_true", help="Do not let the agent layer stop early after a decisive raw-series result.")
    parser.add_argument("--format", choices=["text", "json", "markdown", "card-json", "card-markdown", "summary-card", "summary-card-json", "narrative", "schema-json", "similarity-json", "similarity-markdown", "similarity-summary", "similarity-narrative", "agent-json", "agent-markdown", "agent-context", "html-report", "html-similarity", "tool-json"], default="text", help="Output format for profiling, similarity, or agent-driving commands.")
    parser.add_argument("--guide", choices=["about", "api", "scenarios", "environments", "workflow", "cases", "hot-cases", "similarity", "similarity-methods", "agent-driving", "homepage", "playground", "start-here", "doctor", "compatibility", "asset-audit", "user-guide", "ecosystem", "coverage", "agent-manifest", "github-readme", "pypi-description", "routing", "docs-index", "quickstart", "installation", "zero-install", "pages", "live-demo", "integrations", "case-studies", "trust", "starter-datasets", "agent-schemas", "routing-contracts", "utility-benchmark"], default=None, help="Print a built-in guide instead of profiling input data.")
    parser.add_argument("--guide-format", choices=["text", "json", "markdown"], default="markdown", help="Output format for guide commands.")
    parser.add_argument("--output", type=Path, default=None, help="Optional output file.")
    parser.add_argument("--serve-demo", action="store_true", help="Run the local live demo server instead of profiling files.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host for the local live demo server.")
    parser.add_argument("--port", type=int, default=8765, help="Port for the local live demo server.")
    parser.add_argument("--open-browser", action="store_true", help="Open a browser automatically when starting the live demo server.")
    parser.add_argument("--export-pages", type=Path, default=None, help="Write the GitHub-Pages-ready static bundle to this directory and exit.")
    parser.add_argument("--write-constraints", type=Path, default=None, help="Write a compatibility constraints file to this path and exit.")
    parser.add_argument("--constraint-profile", choices=["clean-venv", "mixed-scientific-stack", "pages-only"], default="mixed-scientific-stack", help="Constraint profile to use with --write-constraints.")
    return parser


def _stdout_encoding() -> str:
    return (getattr(sys.stdout, "encoding", None) or locale.getpreferredencoding(False) or "utf-8").lower()


def _looks_like_html(text: str) -> bool:
    prefix = text.lstrip().lower()
    return prefix.startswith("<!doctype html>") or prefix.startswith("<html")


def _write_or_print(output: str, path: Path | None, *, fallback_html_name: str | None = None) -> None:
    if path is not None:
        path.write_text(output, encoding="utf-8")
        return
    text = output if output.endswith("\n") else output + "\n"
    encoding = _stdout_encoding()
    explicit_io_encoding = (os.environ.get("PYTHONIOENCODING") or "").lower()
    if fallback_html_name and _looks_like_html(text) and explicit_io_encoding and encoding not in {"utf-8", "utf8"}:
        target = Path.cwd() / fallback_html_name
        target.write_text(output, encoding="utf-8")
        msg = f"HTML output was written to {target} because the current terminal encoding is {encoding}. Open it in a browser or use --output.\n"
        sys.stdout.write(msg)
        sys.stdout.flush()
        return
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except UnicodeEncodeError:
        data = text.encode(encoding or "utf-8", errors="xmlcharrefreplace")
        buffer = getattr(sys.stdout, "buffer", None)
        if buffer is not None:
            buffer.write(data)
            buffer.flush()
        else:
            sys.stdout.write(data.decode(encoding or "utf-8", errors="ignore"))
            sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.guide is not None:
        fallback_name = None
        if args.output is None and args.guide in {"homepage", "playground", "start-here"}:
            fallback_name = f"echotime-{args.guide}.html"
        _write_or_print(_render_guide(args), args.output, fallback_html_name=fallback_name)
        return 0

    if args.write_constraints is not None:
        write_compatibility_constraints(args.write_constraints, profile=args.constraint_profile)
        _write_or_print(f"wrote compatibility constraints to {args.write_constraints}", args.output)
        return 0

    if args.serve_demo:
        run_demo_server(host=args.host, port=args.port, open_browser=args.open_browser)
        return 0

    if args.export_pages is not None:
        write_pages_bundle(args.export_pages, version="0.17.1")
        _write_or_print(f"wrote GitHub Pages bundle to {args.export_pages}", args.output)
        return 0

    if args.format == "schema-json":
        _write_or_print(json.dumps(schema_dict(), indent=2), args.output)
        return 0

    if args.input is None:
        parser.error("input is required unless --guide or --format schema-json is used.")

    data = _load_input(args.input, input_mode=args.input_mode, npz_key=args.npz_key)
    timestamps = None
    if args.timestamps is not None:
        timestamps = _load_numeric_array(args.timestamps, npz_key=args.npz_key)

    reference = None
    reference_timestamps = None
    if args.reference is not None:
        reference = _load_input(args.reference, input_mode=args.reference_input_mode, npz_key=args.npz_key)
        if args.reference_timestamps is not None:
            reference_timestamps = _load_numeric_array(args.reference_timestamps, npz_key=args.npz_key)

    if args.agent_goal is not None or args.format.startswith("agent-"):
        goal = args.agent_goal or ("compare these two inputs" if reference is not None else "understand this dataset")
        result = agent_drive(
            data,
            reference,
            goal=goal,
            budget=args.agent_budget,
            audience=args.audience,
            domain=args.domain,
            timestamps=timestamps,
            reference_timestamps=reference_timestamps,
            rolling_window=args.rolling_window,
            rolling_step=args.rolling_step,
            stop_on_clear_signal=not args.no_stop_on_clear_signal,
        )
        if args.format == "agent-json":
            output = result.to_json()
        elif args.format == "agent-context":
            output = result.to_context_markdown()
        else:
            output = result.to_markdown()
        _write_or_print(output, args.output)
        return 0

    if reference is not None:
        if args.format == "tool-json":
            output = json.dumps(ts_compare(
                data,
                reference,
                mode="profile" if args.similarity_mode == "profile" else "auto",
                budget=args.agent_budget,
                left_timestamps_ref=timestamps,
                right_timestamps_ref=reference_timestamps,
                left_name=args.input.stem,
                right_name=args.reference.stem,
            ), indent=2)
            _write_or_print(output, args.output)
            return 0
        if args.similarity_mode == "profile":
            report = compare_profiles(data, reference, left_name=args.input.stem, right_name=args.reference.stem)
        else:
            report = compare_series(
                data,
                reference,
                left_timestamps=timestamps,
                right_timestamps=reference_timestamps,
                left_name=args.input.stem,
                right_name=args.reference.stem,
            )
        if args.format in {"json", "similarity-json"}:
            output = report.to_json()
        elif args.format in {"markdown", "similarity-markdown", "text"}:
            output = report.to_markdown()
        elif args.format in {"summary-card", "similarity-summary"}:
            output = report.to_summary_card_markdown()
        elif args.format in {"narrative", "similarity-narrative"}:
            output = report.to_narrative_report()
        elif args.format == "html-similarity":
            output = report.to_html_report() if args.similarity_mode == "profile" else report.to_html_report(title=f"EchoTime similarity report - {args.input.stem} vs {args.reference.stem}")
        else:
            output = report.to_markdown()
        _write_or_print(output, args.output)
        return 0

    profile = profile_dataset(
        data,
        domain=args.domain,
        timestamps=timestamps,
        time_axis=args.time_axis,
        channel_axis=args.channel_axis,
        subject_axis=args.subject_axis,
        sampling_rate=args.sampling_rate,
        tr=args.tr,
        channel_names=_load_labels(args.channel_names),
        roi_names=_load_labels(args.roi_names),
        network_labels=_load_labels(args.network_labels),
        bootstrap=args.bootstrap,
        random_state=args.random_state,
    )

    if args.format == "tool-json":
        output = json.dumps(ts_profile(data, domain=args.domain, budget=args.agent_budget, audience=args.audience, timestamps_ref=timestamps, time_axis=args.time_axis, channel_axis=args.channel_axis, subject_axis=args.subject_axis, sampling_rate=args.sampling_rate, tr=args.tr, channel_names=_load_labels(args.channel_names), roi_names=_load_labels(args.roi_names), network_labels=_load_labels(args.network_labels), bootstrap=args.bootstrap, random_state=args.random_state), indent=2)
    elif args.format == "json":
        output = profile.to_json()
    elif args.format == "markdown":
        output = profile.to_markdown()
    elif args.format == "card-json":
        output = profile.to_card_json()
    elif args.format == "card-markdown":
        output = profile.to_card_markdown()
    elif args.format == "summary-card":
        output = profile.to_summary_card_markdown(audience=args.audience)
    elif args.format == "summary-card-json":
        output = profile.to_summary_card_json(audience=args.audience)
    elif args.format == "narrative":
        output = profile.to_narrative_report(audience=args.audience)
    elif args.format == "html-report":
        output = profile.to_html_report(audience=args.audience)
    else:
        output = profile.to_text()

    _write_or_print(output, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
