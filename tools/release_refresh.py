from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from echotime import (  # noqa: E402
    about,
    agent_schema_guide,
    agent_manifest,
    agent_driving_guide,
    api_reference,
    case_gallery,
    case_studies_guide,
    compatibility_guide,
    coverage_matrix,
    doctor_guide,
    docs_index,
    ecosystem_positioning,
    environment_matrix,
    github_readme,
    hot_case_gallery,
    installation_guide,
    integration_templates_guide,
    live_demo_guide,
    mcp_tool_descriptors,
    openai_function_schemas,
    pages_deploy_guide,
    project_demo_manifest,
    project_docs_pages,
    project_homepage_html,
    project_launchpad_html,
    project_playground_html,
    pypi_long_description,
    quickstart_guide,
    routing_contract_guide,
    scenario_guide,
    similarity_playbook,
    similarity_method_atlas_guide,
    starter_datasets_guide,
    start_here_guide,
    tool_schemas,
    trust_guide,
    utility_benchmark_guide,
    user_guide,
    workflow_recommendation,
    write_pages_bundle,
    zero_install_guide,
)
from echotime.demo_server import demo_server_html  # noqa: E402
from tools.generate_preview_assets import generate_preview_assets  # noqa: E402


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _write_json(path: Path, payload: object) -> None:
    _write(path, json.dumps(payload, indent=2))


def _copy(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _zip_dir(source_dir: Path, archive_path: Path) -> None:
    archive_path.unlink(missing_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(source_dir.rglob("*")):
            if file.is_file():
                zf.write(file, file.relative_to(source_dir))


def _release_draft() -> str:
    return """# EchoTime v0.17.0 Release Draft

## Headline

EchoTime v0.17.0 is the first fully branded release surface for the renamed package: official package name, Pages-ready title card, local demo entry points, compatibility presets, and PyPI release copy now all point to the same product story.

## Official package name

- Brand: EchoTime
- PyPI package: `echotime`
- Legacy compatibility shim: `tsontology`

## Release highlights

- compare-first README and homepage
- PyPI long description tailored for package index readers
- GitHub Pages-ready title card and refreshed visual language
- compatibility-aware onboarding for mixed scientific stacks
- root/docs release assets regenerated from one refresh script

## Entry points

```bash
pip install echotime
echotime-demo --open-browser
echotime --guide doctor
echotime --export-pages docs
```

## Compatibility note

The old `tsontology` package name remains callable in this release as a compatibility shim, but the official product name is now EchoTime.
"""


def main() -> None:
    generate_preview_assets(ROOT)

    _write(ROOT / "README.generated.md", github_readme())
    _write(ROOT / "README.md", github_readme())
    _write(ROOT / "PYPI_LONG_DESCRIPTION.md", pypi_long_description())
    _write(ROOT / "homepage.html", project_homepage_html())
    _write(ROOT / "playground.html", project_playground_html())
    _write(ROOT / "start-here.html", project_launchpad_html())
    _write(ROOT / "local_demo.html", demo_server_html())
    for rel, content in project_docs_pages().items():
        _write(ROOT / rel, content)

    _write(ROOT / "START_HERE.md", start_here_guide())
    _write(ROOT / "INTRODUCTION.md", about())
    _write(ROOT / "API_REFERENCE.md", api_reference())
    _write(ROOT / "DOCS_INDEX.md", docs_index())
    _write(ROOT / "ENVIRONMENT_MATRIX.md", environment_matrix())
    _write(ROOT / "SCENARIO_GUIDE.md", scenario_guide())
    _write(ROOT / "WORKFLOW_GUIDE.md", workflow_recommendation())
    _write(ROOT / "USER_GUIDE.md", user_guide())
    _write(ROOT / "AGENT_DRIVING.md", agent_driving_guide())
    _write(ROOT / "CASE_GALLERY.md", case_gallery())
    _write(ROOT / "HOT_CASES.md", hot_case_gallery())
    _write(ROOT / "SIMILARITY_GUIDE.md", similarity_playbook())
    _write(ROOT / "ECOSYSTEM_POSITIONING.md", ecosystem_positioning())
    _write(ROOT / "COVERAGE_MATRIX.md", coverage_matrix())
    _write(ROOT / "COMPATIBILITY.md", compatibility_guide())
    _write(ROOT / "AGENT_MANIFEST.md", agent_manifest(format="markdown"))
    _write(ROOT / "DOCTOR.md", doctor_guide())
    _write(ROOT / "INSTALLATION.md", installation_guide() + "\n\n" + doctor_guide())
    _write(ROOT / "ZERO_INSTALL.md", zero_install_guide())
    _write(ROOT / "LIVE_DEMO.md", live_demo_guide())
    _write(ROOT / "PAGES_DEPLOYMENT.md", pages_deploy_guide())
    _write(ROOT / "INTEGRATIONS.md", integration_templates_guide())
    _write(ROOT / "CASE_STUDIES.md", case_studies_guide())
    _write(ROOT / "TRUST.md", trust_guide())
    _write(ROOT / "STARTER_DATASETS.md", starter_datasets_guide())
    _write(ROOT / "AGENT_SCHEMAS.md", agent_schema_guide())
    _write(ROOT / "ROUTING_CONTRACTS.md", routing_contract_guide())
    _write(ROOT / "SIMILARITY_METHOD_ATLAS.md", similarity_method_atlas_guide())
    _write(ROOT / "UTILITY_BENCHMARK.md", utility_benchmark_guide())
    _write(ROOT / "PROJECT_HOMEPAGE.md", "# EchoTime homepage\n\nUse `homepage.html` or `docs/index.html` as the official GitHub Pages front door.\n")
    _write(ROOT / "RELEASE_DRAFT_v0.17.0.md", _release_draft())

    _write_json(ROOT / "AGENT_TOOL_SCHEMAS.json", tool_schemas(format="dict"))
    _write_json(ROOT / "OPENAI_FUNCTION_SCHEMAS.json", openai_function_schemas(format="dict"))
    _write_json(ROOT / "MCP_TOOL_DESCRIPTORS.json", mcp_tool_descriptors(format="dict"))
    _write_json(ROOT / "DEMO_MANIFEST.json", project_demo_manifest())
    _write_json(ROOT / "AGENT_MANIFEST.json", agent_manifest(format="json"))

    docs_dir = ROOT / "docs"
    audit_dir = ROOT / "audit_pages_out"
    write_pages_bundle(docs_dir)
    write_pages_bundle(audit_dir)

    _copy(ROOT / "assets" / "echotime_title_card.svg", ROOT / "social" / "echotime_title_card.svg")
    _copy(ROOT / "assets" / "echotime_mark.svg", ROOT / "social" / "echotime_mark.svg")
    _copy(ROOT / "assets" / "bham_affiliation_badge.svg", ROOT / "social" / "bham_affiliation_badge.svg")
    _copy(ROOT / "assets" / "echotime_title_card.svg", docs_dir / "social" / "echotime_title_card.svg")
    _copy(ROOT / "assets" / "echotime_mark.svg", docs_dir / "social" / "echotime_mark.svg")
    _copy(ROOT / "assets" / "bham_affiliation_badge.svg", docs_dir / "social" / "bham_affiliation_badge.svg")
    _copy(ROOT / "assets" / "echotime_title_card.png", ROOT / "social" / "echotime_title_card.png")
    _copy(ROOT / "assets" / "echotime_title_card.png", docs_dir / "social" / "echotime_title_card.png")

    _zip_dir(docs_dir, ROOT / "echotime_v0.17_pages_bundle.zip")
    print("release surface refreshed")


if __name__ == "__main__":
    main()
