"""Admin commands: create accounts, check progress and run the draw."""

import random
import re
import secrets
from dataclasses import dataclass
from pathlib import Path

import yaml

from xmas_wichtel.matching import draw_assignments
from xmas_wichtel.repository import Repository

USERNAME_PATTERN = re.compile(r"^[a-z0-9_-]{1,32}$")
PASSWORD_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"


class AdminError(Exception):
    """Raised when an admin command cannot be carried out."""


@dataclass(frozen=True)
class Participant:
    """An entry of the participants file.

    Attributes:
        username: Name used to log in.
        display_name: Name shown to other participants.
    """

    username: str
    display_name: str


@dataclass(frozen=True)
class Credential:
    """Login details of a newly created account.

    Attributes:
        username: Name used to log in.
        display_name: Name shown to other participants.
        password: Generated password.
    """

    username: str
    display_name: str
    password: str


@dataclass(frozen=True)
class ParticipantStatus:
    """How far a participant is with their wishlist.

    Attributes:
        username: Name used to log in.
        display_name: Name shown to other participants.
        item_count: Number of items on their wishlist.
    """

    username: str
    display_name: str
    item_count: int


@dataclass(frozen=True)
class Status:
    """Overall progress.

    Attributes:
        participants: Progress of every participant.
        matched: Whether the draw has happened.
    """

    participants: list[ParticipantStatus]
    matched: bool


def load_participants(path: Path) -> list[Participant]:
    """Read and validate the participants file.

    Args:
        path: YAML file with a `participants` list of `username` and `display_name` entries.

    Returns:
        Participants in file order.

    Raises:
        AdminError: If the file is missing or invalid.
    """
    if not path.is_file():
        raise AdminError(f"{path} not found. Copy participants.example.yaml to {path} and fill it in.")
    content = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = content.get("participants") if isinstance(content, dict) else None
    if not isinstance(entries, list) or not entries:
        raise AdminError(f"{path} must contain a non-empty 'participants' list.")

    participants = []
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise AdminError(f"Participant {index} in {path} must have a username and a display_name.")
        username = str(entry.get("username", "")).strip()
        display_name = str(entry.get("display_name", "")).strip()
        if not USERNAME_PATTERN.fullmatch(username):
            raise AdminError(
                f"Participant {index} in {path}: username {username!r} must be 1-32 characters of a-z, 0-9, _ or -."
            )
        if not 1 <= len(display_name) <= 100:
            raise AdminError(f"Participant {index} in {path}: display_name must be 1-100 characters.")
        participants.append(Participant(username=username, display_name=display_name))

    usernames = [participant.username for participant in participants]
    duplicates = sorted({username for username in usernames if usernames.count(username) > 1})
    if duplicates:
        raise AdminError(f"Duplicate usernames in {path}: {', '.join(duplicates)}")
    return participants


def generate_password() -> str:
    """Generate a random password that is easy to read and type, e.g. `k7hd-9wxe-m3pa`.

    Returns:
        Password of three dash-separated groups of four characters without look-alikes such as 0/o or 1/l.
    """
    return "-".join("".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(4)) for _ in range(3))


def add_users(repository: Repository, participants: list[Participant]) -> tuple[list[Credential], list[str]]:
    """Create accounts for all participants that do not have one yet.

    Args:
        repository: Storage to create the accounts in.
        participants: Everyone who should have an account.

    Returns:
        Credentials of the new accounts, and usernames that already existed and were skipped.
    """
    existing = {profile.username for profile in repository.list_profiles()}
    credentials = []
    skipped = []
    for participant in participants:
        if participant.username in existing:
            skipped.append(participant.username)
            continue
        password = generate_password()
        repository.create_user(participant.username, participant.display_name, password)
        credentials.append(Credential(participant.username, participant.display_name, password))
    return credentials, skipped


def get_status(repository: Repository) -> Status:
    """Collect how many wishlist items everyone has entered and whether the draw has happened.

    Args:
        repository: Storage to read from.

    Returns:
        Progress of all participants. Wishlist contents and assignments are never read.
    """
    counts = repository.count_items_by_owner()
    participants = [
        ParticipantStatus(profile.username, profile.display_name, counts.get(profile.id, 0))
        for profile in repository.list_profiles()
    ]
    return Status(participants=participants, matched=repository.count_assignments() > 0)


def run_matching(
    repository: Repository, allow_empty: bool = False, redraw: bool = False, rng: random.Random | None = None
) -> int:
    """Draw who gives a gift to whom and store the result.

    Args:
        repository: Storage to read participants from and write assignments to.
        allow_empty: Run the draw even if some participants have an empty wishlist.
        redraw: Replace an existing draw.
        rng: Random number generator, for tests.

    Returns:
        Number of participants in the draw.

    Raises:
        AdminError: If there are too few participants, someone's wishlist is empty, or a draw already exists.
    """
    profiles = repository.list_profiles()
    if len(profiles) < 2:
        raise AdminError("At least two participants are needed for a draw. Run add-users first.")

    if not redraw and repository.count_assignments() > 0:
        raise AdminError("The draw has already happened. Pass --redraw to replace it (everyone gets a new person).")

    if not allow_empty:
        counts = repository.count_items_by_owner()
        empty = [profile.display_name for profile in profiles if counts.get(profile.id, 0) == 0]
        if empty:
            raise AdminError(f"Still waiting for wishes from: {', '.join(empty)}. Pass --allow-empty to draw anyway.")

    assignments = draw_assignments([profile.id for profile in profiles], rng=rng)
    repository.replace_assignments(assignments)
    return len(assignments)


def reset_password(repository: Repository, username: str) -> str:
    """Give a participant a new random password.

    Args:
        repository: Storage containing the participant.
        username: Name the participant logs in with.

    Returns:
        The new password.

    Raises:
        AdminError: If no participant has this username.
    """
    profile = next((profile for profile in repository.list_profiles() if profile.username == username), None)
    if profile is None:
        raise AdminError(f"No participant with username {username!r}.")
    password = generate_password()
    repository.set_password(profile.id, password)
    return password
