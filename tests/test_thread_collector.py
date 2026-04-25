import textwrap
from pathlib import Path

from tools.thread_collector import (
    parse_open_threads,
    collect_threads,
    generate_threads_md,
    Thread,
)


SAMPLE_WITH_THREADS = textwrap.dedent("""\
    # Contribution #005

    **Agent:** Test
    **Date:** 2026-04-25
    **PR:** test

    ---

    ## What I observed

    Some observation.

    ## Open threads

    - First open question that future agents might address.
    - Second open question, slightly longer.

    ## Why

    Reasoning.

    ---
""")


SAMPLE_WITHOUT_THREADS = textwrap.dedent("""\
    # Contribution #099

    **Agent:** Test

    ## What I observed

    Stuff.

    ## Why

    Because.

    ---
""")


SAMPLE_MULTI_LINE_BULLET = textwrap.dedent("""\
    ## Open threads

    - First thread
      with a continuation line that should remain attached.
    - Second thread is single-line.

    ## Next section

    Stuff.
""")


def test_parse_open_threads_present():
    threads = parse_open_threads(SAMPLE_WITH_THREADS)
    assert len(threads) == 2
    assert "First open question" in threads[0]
    assert "Second open question" in threads[1]


def test_parse_open_threads_absent():
    assert parse_open_threads(SAMPLE_WITHOUT_THREADS) == []


def test_parse_open_threads_handles_multi_line_bullet():
    threads = parse_open_threads(SAMPLE_MULTI_LINE_BULLET)
    assert len(threads) == 2
    assert "continuation line" in threads[0]
    assert "Second thread is single-line" in threads[1]


def test_parse_open_threads_stops_at_next_header():
    text = textwrap.dedent("""\
        ## Open threads

        - Only thread.

        ## Why

        - Not a thread, this is reasoning.
    """)
    threads = parse_open_threads(text)
    assert len(threads) == 1
    assert "Only thread" in threads[0]


def test_collect_threads_tags_with_contribution_number(tmp_path):
    (tmp_path / "PR_DESCRIPTION_001.md").write_text(SAMPLE_WITHOUT_THREADS)
    (tmp_path / "PR_DESCRIPTION_005.md").write_text(SAMPLE_WITH_THREADS)
    threads = collect_threads(tmp_path)
    assert len(threads) == 2
    assert all(t.contribution_number == 5 for t in threads)


def test_collect_threads_ignores_unrelated_files(tmp_path):
    (tmp_path / "PR_DESCRIPTION_007.md").write_text(SAMPLE_WITH_THREADS)
    (tmp_path / "README.md").write_text(SAMPLE_WITH_THREADS)
    (tmp_path / "notes.txt").write_text(SAMPLE_WITH_THREADS)
    threads = collect_threads(tmp_path)
    assert len(threads) == 2
    assert all(t.contribution_number == 7 for t in threads)


def test_generate_threads_md_includes_count_and_bodies():
    threads = [
        Thread(contribution_number=5, text="Thread A"),
        Thread(contribution_number=5, text="Thread B"),
    ]
    output = generate_threads_md(threads)
    assert "**Total open threads:** 2" in output
    assert "Thread A" in output
    assert "Thread B" in output
    assert "contribution #005" in output


def test_generate_threads_md_empty():
    output = generate_threads_md([])
    assert "**Total open threads:** 0" in output
    assert "No open threads recorded" in output


def test_smoke_against_real_repo():
    """End-to-end: thread_collector runs against the actual repository."""
    repo_root = Path(__file__).parent.parent
    threads = collect_threads(repo_root / "contributions")
    output = generate_threads_md(threads)
    assert "THREADS.md" in output
    assert len(threads) >= 1
