"""Bundle the small source assets required by installed-wheel imports and export.

Source files remain authoritative. Run this after changing tutorial data,
gallery examples, or the selected site images; ``--check`` detects stale
copies without modifying files. No network calls or third-party imports are
used. The payload deliberately excludes rendered reports and large previews.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "src" / "echotime" / "data" / "runtime"
RUNTIME_FILES = (
    "examples/data/real_example_sources.json",
    "examples/data/real_ai_attention_breakouts.csv",
    "examples/data/real_btc_oil_vix_2024.csv",
    "examples/data/real_heatwave_city_temps_2024.csv",
    "examples/data/real_python_javascript_pageviews_2024.csv",
    "examples/data/real_treasury_yields_2024.csv",
    "examples/data/real_usgs_earthquakes_ca_ak_2024.csv",
    "examples/gallery/plot_btc_gold_under_shocks.py",
    "examples/gallery/plot_github_breakout_analogs.py",
    "examples/gallery/plot_heatwave_grid_load.py",
    "examples/gallery/plot_irregular_patient_similarity.py",
    "examples/gallery/plot_two_curves_similarity.py",
    "examples/gallery/plot_weekly_traffic_similarity.py",
    "assets/bham_affiliation_badge.svg",
    "assets/echotime_mark.svg",
    "assets/echotime_title_card.svg",
    "assets/echotime_title_card.png",
    "assets/logo.png",
)


def expected_assets() -> dict[str, bytes]:
    files = {name: (ROOT / name).read_bytes() for name in RUNTIME_FILES}
    manifest = {
        "description": "Generated runtime resources; edit the original repository files.",
        "sources": {name: hashlib.sha256(content).hexdigest()
                    for name, content in files.items()},
    }
    files["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    return files


def sync_runtime_assets(*, check: bool = False) -> list[str]:
    files = expected_assets()
    if check:
        stale = [name for name, content in files.items()
                 if not (BUNDLE / name).is_file() or (BUNDLE / name).read_bytes() != content]
        extra = [path.relative_to(BUNDLE).as_posix() for path in BUNDLE.rglob("*")
                 if path.is_file() and path.relative_to(BUNDLE).as_posix() not in files
                 and "__pycache__" not in path.parts]
        if stale or extra:
            raise SystemExit("Stale runtime assets; run python tools/sync_runtime_assets.py: "
                             + ", ".join(stale + extra))
    else:
        # All entries in this directory are generated copies, never source files.
        if BUNDLE.exists():
            shutil.rmtree(BUNDLE)
        for name, content in files.items():
            target = BUNDLE / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
    return list(files)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if packaged copies are stale")
    args = parser.parse_args()
    names = sync_runtime_assets(check=args.check)
    print(f"Runtime assets {'verified' if args.check else 'synced'}: {len(names)} files")


if __name__ == "__main__":
    main()
