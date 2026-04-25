import ast
import textwrap
from pathlib import Path

from tools.coverage_map import (
    parse_tool_imports,
    infer_modules_for_test,
    collect_test_coverage,
    list_tool_modules,
    aggregate_by_module,
    generate_coverage_map,
)


SAMPLE_IMPORTS = textwrap.dedent(
    """\
    from tools.project_snapshot import analyze_python_file as analyze
    import tools.thread_collector as tc
    from tools import contribution_reader as cr


    def test_uses_analyze():
        analyze(None)


    def test_uses_alias_module():
        tc.parse_open_threads("x")


    def test_uses_from_tools_import():
        cr.load_all(None)


    def test_unmapped():
        assert True
    """
)


def test_parse_tool_imports_supports_from_and_alias_imports():
    tree = ast.parse(SAMPLE_IMPORTS)
    symbol_map, package_map = parse_tool_imports(tree)

    assert symbol_map["analyze"] == "project_snapshot"
    assert symbol_map["tc"] == "thread_collector"
    assert symbol_map["cr"] == "contribution_reader"
    assert package_map[("tools", "thread_collector")] == "thread_collector"


def test_infer_modules_for_test_from_symbol_usage():
    tree = ast.parse(SAMPLE_IMPORTS)
    symbol_map, package_map = parse_tool_imports(tree)

    test_fn = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "test_uses_analyze"
    )

    assert infer_modules_for_test(test_fn, symbol_map, package_map) == ["project_snapshot"]


def test_infer_modules_for_test_from_attribute_usage():
    tree = ast.parse(SAMPLE_IMPORTS)
    symbol_map, package_map = parse_tool_imports(tree)

    test_fn = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "test_uses_alias_module"
    )

    assert infer_modules_for_test(test_fn, symbol_map, package_map) == ["thread_collector"]


def test_collect_test_coverage_returns_all_test_functions(tmp_path):
    test_file = tmp_path / "test_sample.py"
    test_file.write_text(SAMPLE_IMPORTS)

    coverage = collect_test_coverage(tmp_path)
    assert len(coverage) == 4

    by_name = {c.test_name: c.modules for c in coverage}
    assert by_name["test_uses_analyze"] == ["project_snapshot"]
    assert by_name["test_uses_alias_module"] == ["thread_collector"]
    assert by_name["test_uses_from_tools_import"] == ["contribution_reader"]
    assert by_name["test_unmapped"] == []


def test_list_tool_modules_ignores_init(tmp_path):
    (tmp_path / "__init__.py").write_text("")
    (tmp_path / "alpha.py").write_text("")
    (tmp_path / "beta.py").write_text("")

    assert list_tool_modules(tmp_path) == ["alpha", "beta"]


def test_aggregate_by_module_expands_test_ids():
    coverage = collect_test_coverage(Path(__file__).parent)
    by_module = aggregate_by_module(coverage)
    assert isinstance(by_module, dict)


def test_generate_coverage_map_includes_counts_and_unmapped_section(tmp_path):
    test_file = tmp_path / "test_sample.py"
    test_file.write_text(SAMPLE_IMPORTS)

    coverage = collect_test_coverage(tmp_path)
    output = generate_coverage_map(coverage, ["contribution_reader", "project_snapshot", "thread_collector"])

    assert "**Total test functions:** 4" in output
    assert "**Mapped test functions:** 3" in output
    assert "**Unmapped test functions:** 1" in output
    assert "tests/test_sample.py::test_unmapped" in output


def test_smoke_against_real_repo():
    repo_root = Path(__file__).parent.parent
    coverage = collect_test_coverage(repo_root / "tests")
    tool_modules = list_tool_modules(repo_root / "tools")
    output = generate_coverage_map(coverage, tool_modules)

    assert "COVERAGE_MAP.md" in output
    assert len(coverage) >= 1
    assert "contribution_reader" in output
