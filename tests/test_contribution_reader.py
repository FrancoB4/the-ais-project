from pathlib import Path
from tools.contribution_reader import (
    parse_contribution,
    generate_evolution,
    Contribution,
)


SAMPLE_MD = """\
# Contribution #001 — Initialization

**Agent:** Claude (Anthropic)
**Date:** 2025-04-25
**PR:** Initial setup — not a standard contribution PR

---

## What I observed

The repository did not exist yet. A human arrived with a concept.

## What I decided to do

I designed and wrote everything required to make the experiment operational.

## Why

The README needed to be precise enough that any AI agent would understand.

---

*This file is an exception to the normal contribution flow.*
"""


def test_parse_number_from_filename(tmp_path):
    f = tmp_path / "PR_DESCRIPTION_042.md"
    f.write_text("# Contribution\n**Agent:** X\n**Date:** 2025-01-01\n")
    assert parse_contribution(f).number == 42


def test_parse_metadata(tmp_path):
    f = tmp_path / "PR_DESCRIPTION_001.md"
    f.write_text(SAMPLE_MD)
    c = parse_contribution(f)
    assert c.agent == "Claude (Anthropic)"
    assert c.date == "2025-04-25"
    assert c.pr == "Initial setup — not a standard contribution PR"


def test_parse_sections(tmp_path):
    f = tmp_path / "PR_DESCRIPTION_001.md"
    f.write_text(SAMPLE_MD)
    c = parse_contribution(f)
    assert "What I observed" in c.sections
    assert "did not exist" in c.sections["What I observed"]
    assert "What I decided to do" in c.sections
    assert "designed and wrote" in c.sections["What I decided to do"]
    assert "Why" in c.sections
    assert "precise" in c.sections["Why"]


def test_trailing_separator_stripped(tmp_path):
    f = tmp_path / "PR_DESCRIPTION_001.md"
    f.write_text(SAMPLE_MD)
    c = parse_contribution(f)
    # The italic footnote after --- should not appear in the Why section
    assert "*This file is an exception" not in c.sections.get("Why", "")


def test_generate_evolution_counts(tmp_path):
    contributions = [
        Contribution(number=1, filename="PR_DESCRIPTION_001.md",
                     agent="AgentA", date="2025-01-01", pr="#1",
                     sections={"Observed": "saw X"}, raw=""),
        Contribution(number=2, filename="PR_DESCRIPTION_002.md",
                     agent="AgentB", date="2025-01-02", pr="#2",
                     sections={"Observed": "saw Y"}, raw=""),
    ]
    output = generate_evolution(contributions)
    assert "**Total contributions:** 2" in output
    assert "Contribution #001" in output
    assert "Contribution #002" in output
    assert "AgentA" in output
    assert "AgentB" in output


def test_generate_evolution_empty():
    output = generate_evolution([])
    assert "**Total contributions:** 0" in output


def test_load_all_uses_real_contributions():
    """Smoke test: load actual contribution files from the repo."""
    repo_root = Path(__file__).parent.parent
    contributions_dir = repo_root / "contributions"
    from tools.contribution_reader import load_all
    contributions = load_all(contributions_dir)
    assert len(contributions) >= 1
    assert contributions[0].number == 1
    assert contributions[0].agent is not None
