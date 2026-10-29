"""Source, wheel and legacy resource resolution must work independently of cwd."""

from pathlib import Path

from echotime import runtime_paths


def _resource(root: Path) -> Path:
    directory = root / "examples" / "data"
    directory.mkdir(parents=True)
    (directory / "sentinel.json").write_text("{}", encoding="utf-8")
    return directory


def test_installed_package_uses_bundled_assets_away_from_checkout(tmp_path, monkeypatch):
    package = tmp_path / "environment" / "lib" / "python3.12" / "site-packages" / "echotime"
    expected = _resource(package / "data" / "runtime")
    elsewhere = tmp_path / "unrelated_working_directory"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setattr(runtime_paths, "__file__", str(package / "runtime_paths.py"))

    assert runtime_paths.resolve_repo_subdir("examples", "data", sentinel="sentinel.json") == expected


def test_source_checkout_resources_take_precedence_over_packaged_copies(tmp_path, monkeypatch):
    repository = tmp_path / "checkout"
    package = repository / "src" / "echotime"
    expected = _resource(repository)
    _resource(package / "data" / "runtime")
    monkeypatch.setattr(runtime_paths, "__file__", str(package / "runtime_paths.py"))

    assert runtime_paths.resolve_repo_subdir("examples", "data", sentinel="sentinel.json") == expected


def test_legacy_working_directory_fallback_remains_available(tmp_path, monkeypatch):
    package = tmp_path / "environment" / "lib" / "python3.12" / "site-packages" / "echotime"
    working_directory = tmp_path / "legacy"
    expected = _resource(working_directory)
    monkeypatch.chdir(working_directory)
    monkeypatch.setattr(runtime_paths, "__file__", str(package / "runtime_paths.py"))

    assert runtime_paths.resolve_repo_subdir("examples", "data", sentinel="sentinel.json") == expected
