from __future__ import annotations

from echotime import (
    extracted_similarity_methods,
    native_similarity_methods,
    project_docs_pages,
    project_similarity_methods_html,
    similarity_method_atlas_dict,
    similarity_method_atlas_guide,
)


def test_similarity_method_atlas_extracts_expected_inventory() -> None:
    payload = similarity_method_atlas_dict()
    extracted = extracted_similarity_methods()
    native = native_similarity_methods()

    assert payload["summary"]["extracted_method_count"] == 127
    assert payload["summary"]["native_method_count"] >= 10
    assert payload["summary"]["source_package"] == "ts_similarity_package_v2_pkg"
    assert any(entry["name"] == "twed" and entry["echotime_status"] == "Implemented in EchoTime" for entry in payload["recommended_additions"])
    assert any(entry["name"] == "max_normalized_cross_correlation" and entry["echotime_status"] == "Implemented in EchoTime" for entry in payload["recommended_additions"])
    assert any(entry["name"] == "independent_sbd" and entry["echotime_status"] == "Implemented in EchoTime" for entry in extracted)
    assert any(entry["name"] == "periodogram_distance" and entry["echotime_status"] == "Implemented in EchoTime" for entry in payload["recommended_additions"])
    assert any(entry["name"] == "ordinal_pattern_js_distance" and entry["echotime_api"] == "ordinal_pattern_js_distance" for entry in extracted)
    assert any(entry["name"] == "shape_similarity" for entry in native)


def test_similarity_method_atlas_markdown_contains_formulas() -> None:
    text = similarity_method_atlas_guide()

    assert "# EchoTime similarity method atlas" in text
    assert "ts_similarity_package_v2_pkg" in text
    assert "Implemented and high-fit additions from ts_similarity_package_v2_pkg" in text
    assert "twed" in text
    assert "max_normalized_cross_correlation" in text
    assert "soft_dtw" in text
    assert "identity_embedding_similarity" in text
    assert "shape_similarity" in text


def test_methods_page_is_in_docs_bundle() -> None:
    html = project_similarity_methods_html()
    pages = project_docs_pages()

    assert "Similarity Methods Atlas" in html
    assert "guide/methods.html" in pages
    assert "What EchoTime now exposes" in pages["guide/methods.html"]
    assert "Implemented and high-fit additions from ts_similarity_package_v2_pkg" in pages["guide/methods.html"]
    assert "EchoTime API" in pages["guide/methods.html"]
    assert "Complexity" in pages["guide/methods.html"]
    assert "sbd" in pages["guide/methods.html"]
