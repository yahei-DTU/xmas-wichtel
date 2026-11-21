"""Data access for the admin CLI."""

import os
from collections import Counter
from dataclasses import dataclass
from typing import Protocol, Self

from dotenv import find_dotenv, load_dotenv
from supabase import Client, create_client

LOGIN_EMAIL_DOMAIN = "wichtel.local"


class ConfigurationError(Exception):
    """Raised when the connection settings are missing."""


@dataclass(frozen=True)
class Profile:
    """A participant with an account.

    Attributes:
        id: ID of the Supabase auth user.
        username: Name used to log in.
        display_name: Name shown to other participants.
    """

    id: str
    username: str
    display_name: str


def username_to_email(username: str) -> str:
    """Build the login email Supabase Auth uses for a username.

    Supabase Auth needs an email address, so every username is mapped to an address in a domain that is never mailed.
    The website does the same mapping when someone logs in.

    Args:
        username: Name used to log in.

    Returns:
        Email address of the Supabase auth user.
    """
    return f"{username}@{LOGIN_EMAIL_DOMAIN}"


class Repository(Protocol):
    """Storage operations the admin commands need."""

    def list_profiles(self) -> list[Profile]:
        """Return all participants."""
        ...

    def create_user(self, username: str, display_name: str, password: str) -> Profile:
        """Create a login and a profile for a new participant."""
        ...

    def set_password(self, user_id: str, password: str) -> None:
        """Replace a participant's password."""
        ...

    def count_items_by_owner(self) -> dict[str, int]:
        """Return the number of wishlist items per participant ID, without reading their contents."""
        ...

    def count_assignments(self) -> int:
        """Return how many assignments are stored."""
        ...

    def replace_assignments(self, assignments: dict[str, str]) -> None:
        """Delete all stored assignments and store the given giver to receiver mapping instead."""
        ...


class SupabaseRepository:
    """Repository backed by Supabase, authenticated with the secret key.

    The secret key bypasses row level security, so this class must only ever run on the admin's machine.
    """

    def __init__(self, client: Client) -> None:
        """Initialize the repository.

        Args:
            client: Supabase client created with the secret key.
        """
        self._client = client

    @classmethod
    def from_env(cls) -> Self:
        """Create a repository from the `SUPABASE_URL` and `SUPABASE_SECRET_KEY` environment variables.

        Values from a `.env` file in the current directory (or a parent of it) are loaded first.

        Returns:
            Repository connected to the configured Supabase project.

        Raises:
            ConfigurationError: If one of the variables is missing.
        """
        load_dotenv(find_dotenv(usecwd=True))
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SECRET_KEY")
        if not url or not key:
            raise ConfigurationError("Set SUPABASE_URL and SUPABASE_SECRET_KEY in .env (see .env.example).")
        return cls(create_client(url, key))

    def list_profiles(self) -> list[Profile]:
        """Return all participants, sorted by display name."""
        rows = self._client.table("profiles").select("id, username, display_name").order("display_name").execute()
        return [Profile(**row) for row in rows.data]

    def create_user(self, username: str, display_name: str, password: str) -> Profile:
        """Create a confirmed auth user and the matching profile.

        If the profile cannot be stored, the auth user is deleted again so the command can be rerun.
        """
        response = self._client.auth.admin.create_user(
            {"email": username_to_email(username), "password": password, "email_confirm": True}
        )
        user_id = response.user.id
        try:
            self._client.table("profiles").insert(
                {"id": user_id, "username": username, "display_name": display_name}
            ).execute()
        except Exception:
            self._client.auth.admin.delete_user(user_id)
            raise
        return Profile(id=user_id, username=username, display_name=display_name)

    def set_password(self, user_id: str, password: str) -> None:
        """Replace a participant's password."""
        self._client.auth.admin.update_user_by_id(user_id, {"password": password})

    def count_items_by_owner(self) -> dict[str, int]:
        """Return the number of wishlist items per participant ID, without reading their contents."""
        rows = self._client.table("wishlist_items").select("owner_id").execute()
        return dict(Counter(row["owner_id"] for row in rows.data))

    def count_assignments(self) -> int:
        """Return how many assignments are stored."""
        return len(self._client.table("assignments").select("giver_id").execute().data)

    def replace_assignments(self, assignments: dict[str, str]) -> None:
        """Delete all stored assignments and store the given giver to receiver mapping instead."""
        self._client.table("assignments").delete().not_.is_("giver_id", "null").execute()
        rows = [{"giver_id": giver, "receiver_id": receiver} for giver, receiver in assignments.items()]
        self._client.table("assignments").insert(rows).execute()
