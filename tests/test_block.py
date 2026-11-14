"""The delegation block: inserted, replaced and removed without touching the user's text."""

import pytest

from block import END, START, BlockError, insert, remove

BLOCK = "## Delegation\n\n- rule\n"


def test_appends_after_one_blank_line_and_replaces_in_place():
    once = insert("# Mine\n", BLOCK)
    assert once == f"# Mine\n\n{START}\n## Delegation\n\n- rule\n{END}\n"

    again = insert(once.replace("- rule", "- old rule"), BLOCK)
    assert again == once


def test_remove_restores_a_block_in_the_middle():
    original = "A\n\nB\n"
    with_block = original.replace("A\n\n", f"A\n\n{START}\n## Delegation\n{END}\n\n")

    assert remove(with_block) == original


def test_remove_restores_a_block_at_the_end_and_empties_a_block_only_file():
    assert remove(insert("# Mine\n", BLOCK)) == "# Mine\n"
    assert remove(insert("", BLOCK)) == ""


def test_keeps_crlf_line_ends():
    text = "# Mine\r\n\r\nKeep.\r\n"

    added = insert(text, BLOCK)

    assert "\n" not in added.replace("\r\n", "")
    assert remove(added) == text


@pytest.mark.parametrize(
    "text",
    [
        f"# Mine\n{START}\nIMPORTANT USER TEXT\n",  # start only
        f"# Mine\n{END}\nIMPORTANT USER TEXT\n",  # end only
        f"{END}\nx\n{START}\n",  # reversed
        f"{START}\na\n{END}\n{START}\nb\n{END}\n",  # two blocks
    ],
)
def test_refuses_broken_markers(text: str):
    with pytest.raises(BlockError):
        insert(text, BLOCK)
    with pytest.raises(BlockError):
        remove(text)


def test_markers_mentioned_in_prose_or_code_are_not_markers():
    prose = f"Never edit text between `{START}` and `{END}`: RULE A\n"
    fenced = f"Example:\n\n```\n{START}\nx\n{END}\n```\n\nRULE B\n"

    for text in (prose, fenced):
        added = insert(text, BLOCK)
        assert added.startswith(text)
        assert remove(added) == text
