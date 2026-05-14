
"""EchoTime: explainable similarity for time series and time-series datasets."""

from .adapters import EEGInput, EventStreamInput, FMRIInput, IrregularSubjectInput, IrregularTimeSeriesInput
from .agent import AgentDriveResult, AgentDriver, agent_context, agent_drive, agent_driving_guide
from .profile import DatasetProfile, SeriesProfile, profile_dataset, profile_series
from .communication import narrative_report, summary_card
from .gallery import case_gallery
from .hotcases import hot_case_gallery, similarity_playbook
from .homepage import project_homepage_html
from .playground import project_playground_html
from .launchpad import project_launchpad_html
from .docs_site import (
    project_agents_html,
    project_api_reference_html,
    project_docs_home_html,
    project_docs_pages,
    project_ecosystem_html,
    project_getting_started_html,
    project_similarity_methods_html,
    project_scenarios_html,
    project_tutorials_html,
)
from .sitebundle import project_demo_manifest, project_pages_bundle, write_pages_bundle
from .visuals import axis_bar_svg, profile_html_report, profile_radar_svg, profile_social_card_svg, rolling_similarity_svg, series_overlay_svg, similarity_components_svg, similarity_html_report, similarity_radar_svg, similarity_social_card_svg
from .datasets import list_starter_datasets, starter_dataset, write_starter_dataset
from .product import explain_dataset, explain_similarity, report_dataset, report_similarity
from .agent_tools import TOOL_SCHEMA_VERSION, mcp_tool_descriptors, openai_function_schemas, tool_schemas, ts_compare, ts_profile, ts_route
from .repo_docs import agent_schema_guide, case_studies_guide, doctor_guide, github_readme, installation_guide, integration_templates_guide, live_demo_guide, pages_deploy_guide, pypi_long_description, quickstart_guide, routing_contract_guide, starter_datasets_guide, start_here_guide, trust_guide, utility_benchmark_guide, zero_install_guide
from .similarity import SimilarityReport, compare_profiles, compare_series, rolling_similarity
from .similarity_methods import acf_distance, best_shift, edr_distance, erp_distance, independent_max_ncc, independent_sbd, lcss_distance, lcss_similarity, linear_trend_model_distance, max_ncc, ncc_sequence, ordinal_pattern_js_distance, periodogram_distance, sbd, trend_distance, twed_distance
from .guide import about, api_reference, docs_index, environment_matrix, scenario_guide, user_guide, workflow_recommendation
from .positioning import agent_manifest, coverage_matrix, ecosystem_positioning, tooling_router
from .registry import clear_custom_extensions, get_registry, register_adaptor, register_plugin
from .schema import SCHEMA_VERSION, get_schema, schema_dict
from .doctor import environment_doctor
from .compat import compatibility_constraints, compatibility_guide, write_compatibility_constraints
from .consistency import asset_consistency_report
from .similarity_method_atlas import extracted_similarity_methods, native_similarity_methods, similarity_method_atlas_dict, similarity_method_atlas_guide

_LAZY_ATTRS = {
    'compare_from_text': ('demo_server', 'compare_from_text'),
    'demo_server_html': ('demo_server', 'demo_server_html'),
    'parse_numeric_text': ('demo_server', 'parse_numeric_text'),
    'profile_from_text': ('demo_server', 'profile_from_text'),
    'run_demo_server': ('demo_server', 'run_demo_server'),
}

__all__ = [
    'DatasetProfile', 'SeriesProfile',
    'EEGInput', 'EventStreamInput', 'FMRIInput', 'IrregularSubjectInput', 'IrregularTimeSeriesInput',
    'AgentDriver', 'AgentDriveResult', 'agent_drive', 'agent_context', 'agent_driving_guide',
    'profile_dataset', 'profile_series', 'summary_card', 'narrative_report', 'case_gallery', 'hot_case_gallery',
    'similarity_playbook', 'project_homepage_html', 'project_playground_html', 'project_launchpad_html',
    'project_docs_home_html', 'project_getting_started_html', 'project_tutorials_html', 'project_api_reference_html', 'project_similarity_methods_html', 'project_scenarios_html', 'project_ecosystem_html', 'project_agents_html', 'project_docs_pages',
    'project_demo_manifest', 'project_pages_bundle', 'write_pages_bundle',
    'profile_html_report', 'similarity_html_report', 'profile_radar_svg', 'profile_social_card_svg', 'axis_bar_svg',
    'series_overlay_svg', 'rolling_similarity_svg', 'similarity_components_svg', 'similarity_radar_svg', 'similarity_social_card_svg',
    'starter_dataset', 'list_starter_datasets', 'write_starter_dataset',
    'explain_dataset', 'report_dataset', 'explain_similarity', 'report_similarity',
    'ts_profile', 'ts_compare', 'ts_route', 'tool_schemas', 'openai_function_schemas', 'mcp_tool_descriptors', 'TOOL_SCHEMA_VERSION',
    'quickstart_guide', 'installation_guide', 'zero_install_guide', 'pages_deploy_guide', 'live_demo_guide', 'integration_templates_guide', 'pypi_long_description',
    'case_studies_guide', 'trust_guide', 'starter_datasets_guide', 'agent_schema_guide', 'routing_contract_guide', 'utility_benchmark_guide',
    'start_here_guide', 'doctor_guide', 'github_readme',
    'SimilarityReport', 'compare_series', 'compare_profiles', 'rolling_similarity',
    'ncc_sequence', 'max_ncc', 'best_shift', 'sbd', 'independent_max_ncc', 'independent_sbd', 'acf_distance', 'periodogram_distance', 'trend_distance', 'ordinal_pattern_js_distance', 'linear_trend_model_distance', 'lcss_similarity', 'lcss_distance', 'edr_distance', 'erp_distance', 'twed_distance',
    'about', 'api_reference', 'scenario_guide', 'environment_matrix', 'workflow_recommendation', 'ecosystem_positioning', 'coverage_matrix',
    'native_similarity_methods', 'extracted_similarity_methods', 'similarity_method_atlas_dict', 'similarity_method_atlas_guide',
    'agent_manifest', 'tooling_router', 'user_guide', 'docs_index',
    'get_registry', 'register_adaptor', 'register_plugin', 'clear_custom_extensions',
    'get_schema', 'schema_dict', 'SCHEMA_VERSION', 'environment_doctor', 'compatibility_constraints', 'compatibility_guide', 'write_compatibility_constraints', 'asset_consistency_report',
    'compare_from_text', 'demo_server_html', 'parse_numeric_text', 'profile_from_text', 'run_demo_server'
]

def __getattr__(name: str):
    if name in _LAZY_ATTRS:
        from importlib import import_module
        module_name, attr_name = _LAZY_ATTRS[name]
        module = import_module(f'.{module_name}', __name__)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(name)

def __dir__():
    return sorted(set(globals()) | set(__all__))

__version__ = '0.17.0'
