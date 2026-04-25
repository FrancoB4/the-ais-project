import textwrap
from pathlib import Path

from tools.project_snapshot import (
    analyze_python_file,
    find_test_functions,
    scan_tools,
    scan_tests,
    count_contributions,
    generate_snapshot,
    ModuleInfo,
    TestInfo,
)


SAMPLE_MODULE = textwrap.dedent("""\
    \"\"\"A sample module for testing.\"\"\"

    from dataclasses import dataclass


    @dataclass
    class Foo:
        x: int


    def bar(x):
        pass


    def _private():
        pass
""")


SAMPLE_TEST = textwrap.dedent("""\
    def test_one():
        assert True


    def test_two():
        assert True


    def helper():
        pass
""")


def test_analyze_docstring(tmp_path):
    f = tmp_path / "mymodule.py"
    f.write_text(SAMPLE_MODULE)
    info = analyze_python_file(f)
    assert info.docstring == "A sample module for testing."


def test_analyze_public_functions_only(tmp_path):
    f = tmp_path / "mymodule.py"
    f.write_text(SAMPLE_MODULE)
    info = analyze_python_file(f)
    assert "bar" in info.functions
    assert "_private" not in info.functions


def test_analyze_classes(tmp_path):
    f = tmp_path / "mymodule.py"
    f.write_text(SAMPLE_MODULE)
    info = analyze_python_file(f)
    assert "Foo" in info.classes


def test_analyze_line_count(tmp_path):
    f = tmp_path / "mymodule.py"
    f.write_text(SAMPLE_MODULE)
    info = analyze_python_file(f)
    assert info.lines == len(SAMPLE_MODULE.splitlines())


def test_find_test_functions_includes_only_test_prefixed(tmp_path):
    f = tmp_path / "test_something.py"
    f.write_text(SAMPLE_TEST)
    info = find_test_functions(f)
    assert "test_one" in info.test_functions
    assert "test_two" in info.test_functions
    assert "helper" not in info.test_functions


def test_generate_snapshot_counts(tmp_path):
    modules = [
        ModuleInfo(
            path="tools/a.py",
            docstring="Does A.",
            functions=["run"],
            classes=[],
            lines=10,
        )
    ]
    tests = [
        TestInfo(path="tests/test_a.py", test_functions=["test_one", "test_two"])
    ]
    output = generate_snapshot(modules, tests, num_contributions=3, has_workflow=True)
    assert "**Total test functions:** 2" in output
    assert "**Contributions documented:** 3" in output
    assert "CI workflow:** present" in output


def test_generate_snapshot_absent_workflow():
    output = generate_snapshot([], [], num_contributions=0, has_workflow=False)
    assert "CI workflow:** absent" in output


def test_generate_snapshot_lists_test_functions():
    tests = [TestInfo(path="tests/test_x.py", test_functions=["test_alpha", "test_beta"])]
    output = generate_snapshot([], tests, num_contributions=0, has_workflow=False)
    assert "`test_alpha`" in output
    assert "`test_beta`" in output


def test_count_contributions(tmp_path):
    (tmp_path / "PR_DESCRIPTION_001.md").write_text("x")
    (tmp_path / "PR_DESCRIPTION_002.md").write_text("x")
    (tmp_path / "unrelated.md").write_text("x")
    assert count_contributions(tmp_path) == 2


def test_smoke_against_real_repo():
    """Run the full pipeline against the actual repository."""
    repo_root = Path(__file__).parent.parent
    modules = scan_tools(repo_root / "tools")
    tests = scan_tests(repo_root / "tests")
    n = count_contributions(repo_root / "contributions")
    output = generate_snapshot(modules, tests, num_contributions=n, has_workflow=True)
    assert "SNAPSHOT.md" in output
    assert len(modules) >= 1
    assert len(tests) >= 1
    assert n >= 3
