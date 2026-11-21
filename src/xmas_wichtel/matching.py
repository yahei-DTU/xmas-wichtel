"""Random secret santa draw."""

import random
from collections.abc import Sequence


def draw_assignments(participant_ids: Sequence[str], rng: random.Random | None = None) -> dict[str, str]:
    """Randomly decide who gives a gift to whom.

    Participants are shuffled into a single circle and everyone gives to the next person in it. This guarantees that
    nobody draws themselves, everyone gives and receives exactly one gift, and (with three or more participants) no
    two people draw each other.

    Args:
        participant_ids: Unique identifiers of all participants.
        rng: Random number generator to use. Defaults to a cryptographically secure one.

    Returns:
        Mapping from giver ID to receiver ID.

    Raises:
        ValueError: If there are fewer than two participants or the IDs are not unique.
    """
    if len(participant_ids) < 2:
        raise ValueError("At least two participants are needed for a draw.")
    if len(set(participant_ids)) != len(participant_ids):
        raise ValueError("Participant IDs must be unique.")

    circle = list(participant_ids)
    (rng or random.SystemRandom()).shuffle(circle)
    return {giver: circle[(index + 1) % len(circle)] for index, giver in enumerate(circle)}
