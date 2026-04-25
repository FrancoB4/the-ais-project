#!/usr/bin/env python3
"""
Generates COVERAGE_MAP.md — a static map of tests to tool modules.

This complements the existing observability artifacts:
- EVOLUTION.md: what happened (history)
- SNAPSHOT.md: what exists (structure)
- THREADS.md: what remains (open work)
- COVERAGE_MAP.md: what is exercised (test-to-module map)

The mapping is inferred by parsing test imports and symbol usage with `ast`.
No test execution is required.

Usage: python tools/coverage_map.py
Writes COVERAGE_MAP.md to the repo root.
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple


@dataclass
class TestCoverage:
    test_file: str
    test_name: str
    modules: List[str]


def _attribute_chain(node: ast.AST) -> List[str]:
    """Return attribute name chain for expressions like a.b.c -> ["a", "b", "c"]."""
    chain: List[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        chain.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        chain.append(current.id)
        return list(reversed(chain))
    return []


def parse_tool_imports(tree: ast.AST) -> Tuple[Dict[str, str], Dict[Tuple[str, str], str]]:
    """Return symbol and package maps for imports that reference `tools.*` modules."""
    symbol_map: Dict[str, str] = {}
    package_map: Dict[Tuple[str, str], str] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not alias.name.startswith("tools"):
                    continue

                parts = alias.name.split(".")
                if len(parts) >= 2:
                    module = parts[1]
                    package_map[(parts[0], parts[1])] = module
                    if alias.asname:
                        symbol_map[alias.asname] = module
                elif alias.name == "tools" and alias.asname:
                    # `import tools as t` can still support t.module attribute usage.
                    symbol_map[alias.asname] = "tools"

        if isinstance(node, ast.ImportFrom):
            if not node.module or not node.module.startswith("tools"):
                continue

            parts = node.module.split(".")
            if len(parts) >= 2:
                module = parts[1]
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    bound_name = alias.asname or alias.name
                    symbol_map[bound_name] = module
            else:
                # from tools import project_snapshot as ps
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    module = alias.name
                    bound_name = alias.asname or alias.name
                    symbol_map[bound_name] = module
                    package_map[("tools", alias.name)] = module

    return symbol_map, package_map


def infer_modules_for_test(
    test_node: ast.FunctionDef,
    symbol_map: Dict[str, str],
    package_map: Dict[Tuple[str, str], str],
) -> List[str]:
    """Infer which tool modules a single test function exercises."""
    modules: Set[str] = set()

    for node in ast.walk(test_node):
        if isinstance(node, ast.Name):
            module = symbol_map.get(node.id)
            if module and module != "tools":
                modules.add(module)

        if isinstance(node, ast.Attribute):
            chain = _attribute_chain(node)
            if not chain:
                continue

            root_module = symbol_map.get(chain[0])
            if root_module and root_module != "tools":
                modules.add(root_module)
                continue

            if len(chain) >= 2:
                module = package_map.get((chain[0], chain[1]))
                if module:
                    modules.add(module)

    return sorted(modules)


def collect_test_coverage(tests_dir: Path) -> List[TestCoverage]:
    coverage: List[TestCoverage] = []

    for test_file in sorted(tests_dir.glob("test_*.py")):
        source = test_file.read_text(encoding="utf-8")
        tree = ast.parse(source)
        symbol_map, package_map = parse_tool_imports(tree)

        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                modules = infer_modules_for_test(node, symbol_map, package_map)
                coverage.append(
                    TestCoverage(
                        test_file=f"tests/{test_file.name}",
                        test_name=node.name,
                        modules=modules,
                    )
                )

    return coverage


def list_tool_modules(tools_dir: Path) -> List[str]:
    modules = [p.stem for p in sorted(tools_dir.glob("*.py")) if p.name != "__init__.py"]
    return sorted(modules)


def aggregate_by_module(coverage: List[TestCoverage]) -> Dict[str, List[str]]:
    by_module: Dict[str, List[str]] = {}
    for t in coverage:
        test_id = f"{t.test_file}::{t.test_name}"
        for module in t.modules:
            by_module.setdefault(module, []).append(test_id)

    for module in by_module:
        by_module[module].sort()

    return by_module


def generate_coverage_map(coverage: List[TestCoverage], tool_modules: List[str]) -> str:
    by_module = aggregate_by_module(coverage)
    total_tests = len(coverage)
    mapped_tests = sum(1 for t in coverage if t.modules)
    unmapped_tests = total_tests - mapped_tests

    lines = [
        "# COVERAGE_MAP.md",
        "",
        "> Auto-generated by `tools/coverage_map.py`. Do not edit by hand.",
        "> Run the script from the repo root to regenerate after test or tool changes.",
        "",
        "A static map of which test functions appear to exercise which `tools/` modules.",
        "For history and structure, see [EVOLUTION.md](EVOLUTION.md) and [SNAPSHOT.md](SNAPSHOT.md).",
        "",
        "---",
        "",
        f"- **Total test functions:** {total_tests}",
        f"- **Mapped test functions:** {mapped_tests}",
        f"- **Unmapped test functions:** {unmapped_tests}",
        "",
        "## By module",
        "",
    ]

    for module in tool_modules:
        tests = by_module.get(module, [])
        lines.append(f"### `tools/{module}.py`")
        lines.append("")
        lines.append(f"- **Mapped tests:** {len(tests)}")
        if tests:
            for test_id in tests:
                lines.append(f"- `{test_id}`")
        else:
            lines.append("- *(no mapped tests)*")
        lines.append("")

    if unmapped_tests:
        lines.append("## Unmapped tests")
        lines.append("")
        for t in coverage:
            if not t.modules:
                lines.append(f"- `{t.test_file}::{t.test_name}`")
        lines.append("")

    lines += [
        "---",
        "",
        "> Mapping is heuristic and import-usage based; it does not execute tests or measure runtime coverage.",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    repo_root = Path(__file__).parent.parent
    coverage = collect_test_coverage(repo_root / "tests")
    tool_modules = list_tool_modules(repo_root / "tools")
    output = generate_coverage_map(coverage, tool_modules)

    output_path = repo_root / "COVERAGE_MAP.md"
    output_path.write_text(output, encoding="utf-8")
    print(f"Generated {output_path} ({len(coverage)} test function(s)).")
