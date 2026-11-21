"""Tests for the admin commands."""

import random
import re
from pathlib import Path

import pytest

from tests.fakes import FakeRepository
from xmas_wichtel.admin import (
    AdminError,
    Participant,
    add_users,
    generate_password,
    get_status,
    load_participants,
    reset_password,
    run_matching,
)


@pytest.fixture
def repository() -> FakeRepository:
    """Provide an empty in-memory repository."""
    return FakeRepository()


def write_participants(tmp_path: Path, content: str) -> Path:
    """Write a participants file and return its path."""
    path = tmp_path / "participants.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_participants_reads_all_entries(tmp_path: Path) -> None:
    """Valid entries are returned in file order with surrounding whitespace removed."""
    path = write_participants(
        tmp_path,
        "participants:\n  - username: anna\n    display_name: ' Anna '\n  - username: oma-inge\n    display_name: Oma Inge\n",
    )

    assert load_participants(path) == [Participant("anna", "Anna"), Participant("oma-inge", "Oma Inge")]


def test_example_participants_file_is_valid() -> None:
    """The committed example can be copied and used as is."""
    example = Path(__file__).parents[1] / "participants.example.yaml"

    assert len(load_participants(example)) >= 2


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("", "non-empty 'participants' list"),
        ("participants: []\n", "non-empty 'participants' list"),
        ("participants:\n  - anna\n", "must have a username"),
        ("participants:\n  - username: Anna\n    display_name: Anna\n", "username 'Anna'"),
        ("participants:\n  - username: anna\n", "display_name must be"),
        (
            "participants:\n  - {username: anna, display_name: A}\n  - {username: anna, display_name: B}\n",
            "Duplicate usernames.*anna",
        ),
    ],
)
def test_load_participants_rejects_invalid_files(tmp_path: Path, content: str, message: str) -> None:
    """Invalid files produce a helpful error."""
    path = write_participants(tmp_path, content)

    with pytest.raises(AdminError, match=message):
        load_participants(path)


def test_load_participants_reports_missing_file(tmp_path: Path) -> None:
    """A missing file points to the example."""
    with pytest.raises(AdminError, match="participants.example.yaml"):
        load_participants(tmp_path / "participants.yaml")


def test_generated_passwords_are_readable_and_unique() -> None:
    """Passwords have three groups of four unambiguous characters and do not repeat."""
    passwords = {generate_password() for _ in range(100)}

    assert len(passwords) == 100
    assert all(re.fullmatch(r"[a-hjkmnp-z2-9]{4}-[a-hjkmnp-z2-9]{4}-[a-hjkmnp-z2-9]{4}", p) for p in passwords)


def test_add_users_creates_missing_accounts_and_skips_existing(repository: FakeRepository) -> None:
    """Only new participants get an account, each with its own password."""
    repository.add_participant("anna")

    credentials, skipped = add_users(repository, [Participant("anna", "Anna"), Participant("ben", "Ben")])

    assert skipped == ["anna"]
    assert [(c.username, c.display_name) for c in credentials] == [("ben", "Ben")]
    assert repository.passwords["id-ben"] == credentials[0].password
    assert [profile.username for profile in repository.list_profiles()] == ["anna", "ben"]


def test_status_counts_wishes_per_participant(repository: FakeRepository) -> None:
    """Status shows the number of wishes per participant and whether the draw happened."""
    repository.add_participant("anna", item_count=2)
    repository.add_participant("ben")

    status = get_status(repository)

    assert [(p.username, p.item_count) for p in status.participants] == [("anna", 2), ("ben", 0)]
    assert not status.matched


def test_matching_stores_a_valid_draw(repository: FakeRepository) -> None:
    """Everyone is assigned exactly one other participant."""
    ids = [repository.add_participant(name, item_count=1).id for name in ["anna", "ben", "carl"]]

    count = run_matching(repository, rng=random.Random(1))

    assert count == 3
    assert sorted(repository.assignments) == sorted(ids)
    assert sorted(repository.assignments.values()) == sorted(ids)
    assert all(giver != receiver for giver, receiver in repository.assignments.items())
    assert get_status(repository).matched


def test_matching_needs_two_participants(repository: FakeRepository) -> None:
    """A single participant cannot be matched."""
    repository.add_participant("anna", item_count=1)

    with pytest.raises(AdminError, match="At least two"):
        run_matching(repository)


def test_matching_waits_for_empty_wishlists(repository: FakeRepository) -> None:
    """The draw refuses to run while someone has no wishes, unless explicitly allowed."""
    repository.add_participant("anna", item_count=1)
    repository.add_participant("ben")

    with pytest.raises(AdminError, match="Still waiting for wishes from: Ben"):
        run_matching(repository)
    assert repository.assignments == {}

    assert run_matching(repository, allow_empty=True) == 2


def test_matching_does_not_silently_replace_a_draw(repository: FakeRepository) -> None:
    """An existing draw is only replaced with --redraw."""
    for name in ["anna", "ben", "carl", "dora"]:
        repository.add_participant(name, item_count=1)
    run_matching(repository, rng=random.Random(1))
    first_draw = dict(repository.assignments)

    with pytest.raises(AdminError, match="already happened"):
        run_matching(repository)
    assert repository.assignments == first_draw

    run_matching(repository, redraw=True, rng=random.Random(2))
    assert repository.assignments != first_draw


def test_reset_password_sets_a_new_password(repository: FakeRepository) -> None:
    """The new password is stored and returned."""
    repository.add_participant("anna")

    password = reset_password(repository, "anna")

    assert repository.passwords["id-anna"] == password


def test_reset_password_rejects_unknown_users(repository: FakeRepository) -> None:
    """Unknown usernames produce an error."""
    with pytest.raises(AdminError, match="No participant"):
        reset_password(repository, "nobody")
