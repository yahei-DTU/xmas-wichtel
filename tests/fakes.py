"""In-memory test doubles."""

from xmas_wichtel.repository import Profile


class FakeRepository:
    """Repository that keeps everything in memory."""

    def __init__(self) -> None:
        """Initialize an empty repository."""
        self.profiles: list[Profile] = []
        self.item_counts: dict[str, int] = {}
        self.assignments: dict[str, str] = {}
        self.passwords: dict[str, str] = {}

    def add_participant(self, username: str, item_count: int = 0) -> Profile:
        """Add a participant with an account and the given number of wishlist items.

        Args:
            username: Name used to log in. The display name is the capitalized username.
            item_count: Number of wishlist items.

        Returns:
            The new profile.
        """
        profile = self.create_user(username, username.capitalize(), "initial-password")
        self.item_counts[profile.id] = item_count
        return profile

    def list_profiles(self) -> list[Profile]:
        """Return all participants, sorted by display name."""
        return sorted(self.profiles, key=lambda profile: profile.display_name)

    def create_user(self, username: str, display_name: str, password: str) -> Profile:
        """Store a new participant."""
        profile = Profile(id=f"id-{username}", username=username, display_name=display_name)
        self.profiles.append(profile)
        self.passwords[profile.id] = password
        return profile

    def set_password(self, user_id: str, password: str) -> None:
        """Replace a participant's password."""
        self.passwords[user_id] = password

    def count_items_by_owner(self) -> dict[str, int]:
        """Return the number of wishlist items per participant ID."""
        return {owner: count for owner, count in self.item_counts.items() if count}

    def count_assignments(self) -> int:
        """Return how many assignments are stored."""
        return len(self.assignments)

    def replace_assignments(self, assignments: dict[str, str]) -> None:
        """Replace all stored assignments."""
        self.assignments = dict(assignments)
