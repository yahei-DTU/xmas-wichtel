"""Tests for the secret santa draw."""

import random

import pytest

from xmas_wichtel.matching import draw_assignments


@pytest.mark.parametrize("size", [2, 3, 4, 7, 15])
@pytest.mark.parametrize("seed", range(20))
def test_everyone_gives_and_receives_exactly_once_and_never_to_themselves(size: int, seed: int) -> None:
    """Every draw is a valid secret santa assignment."""
    participants = [f"person-{index}" for index in range(size)]

    assignments = draw_assignments(participants, rng=random.Random(seed))

    assert sorted(assignments) == sorted(participants)
    assert sorted(assignments.values()) == sorted(participants)
    assert all(giver != receiver for giver, receiver in assignments.items())


@pytest.mark.parametrize("seed", range(20))
def test_assignments_form_a_single_circle(seed: int) -> None:
    """Following the chain from anyone visits everybody, so nobody draws the person who drew them."""
    participants = [f"person-{index}" for index in range(6)]

    assignments = draw_assignments(participants, rng=random.Random(seed))

    visited = [participants[0]]
    while (receiver := assignments[visited[-1]]) != participants[0]:
        visited.append(receiver)
    assert sorted(visited) == sorted(participants)


def test_draw_is_random() -> None:
    """Different seeds lead to different draws."""
    participants = [f"person-{index}" for index in range(6)]

    draws = {tuple(sorted(draw_assignments(participants, rng=random.Random(seed)).items())) for seed in range(20)}

    assert len(draws) > 1


def test_draw_works_without_explicit_rng() -> None:
    """The default random number generator produces a valid draw."""
    assignments = draw_assignments(["anna", "ben", "carl"])

    assert sorted(assignments.values()) == ["anna", "ben", "carl"]


@pytest.mark.parametrize("participants", [[], ["anna"]])
def test_too_few_participants_are_rejected(participants: list[str]) -> None:
    """A draw needs at least two people."""
    with pytest.raises(ValueError, match="At least two"):
        draw_assignments(participants)


def test_duplicate_participants_are_rejected() -> None:
    """Each participant can only be in the draw once."""
    with pytest.raises(ValueError, match="unique"):
        draw_assignments(["anna", "ben", "anna"])
