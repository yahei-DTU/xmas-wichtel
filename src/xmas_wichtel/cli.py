"""Command line interface for the admin, available as `uv run wichtel`."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from xmas_wichtel.admin import AdminError, add_users, get_status, load_participants, reset_password, run_matching
from xmas_wichtel.repository import ConfigurationError, Repository, SupabaseRepository


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser with one subcommand per admin task.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(prog="wichtel", description="Admin tool for the Wichtel secret santa app.")
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add-users", help="Create accounts for everyone in the participants file.")
    add.add_argument("--file", type=Path, default=Path("participants.yaml"), help="Participants file.")

    commands.add_parser("status", help="Show how many wishes everyone has entered.")

    match = commands.add_parser("match", help="Draw who gives a gift to whom.")
    match.add_argument("--allow-empty", action="store_true", help="Draw even if some wishlists are empty.")
    match.add_argument("--redraw", action="store_true", help="Replace an existing draw.")

    reset = commands.add_parser("reset-password", help="Give a participant a new password.")
    reset.add_argument("username")
    return parser


def _print_add_users(repository: Repository, file: Path) -> None:
    """Create missing accounts and print their credentials.

    Args:
        repository: Storage to create the accounts in.
        file: Participants file.
    """
    credentials, skipped = add_users(repository, load_participants(file))
    for username in skipped:
        print(f"Skipped {username}: account already exists.")
    if not credentials:
        print("No new accounts created.")
        return
    print(f"Created {len(credentials)} account(s). Hand out these credentials, they are not shown again:\n")
    name_width = max(len(credential.display_name) for credential in credentials)
    user_width = max(len(credential.username) for credential in credentials)
    for credential in credentials:
        print(
            f"  {credential.display_name:<{name_width}}  username: {credential.username:<{user_width}}"
            f"  password: {credential.password}"
        )


def _print_status(repository: Repository) -> None:
    """Print everyone's number of wishes and whether the draw has happened.

    Args:
        repository: Storage to read from.
    """
    status = get_status(repository)
    if not status.participants:
        print("No participants yet. Run add-users first.")
        return
    name_width = max(len(f"{p.display_name} ({p.username})") for p in status.participants)
    for participant in status.participants:
        label = f"{participant.display_name} ({participant.username})"
        hint = "" if participant.item_count else "  <- no wishes yet"
        print(f"  {label:<{name_width}}  {participant.item_count:>3} wish(es){hint}")
    print(f"\nDraw: {'done' if status.matched else 'not done yet'}")


def main(argv: Sequence[str] | None = None, repository: Repository | None = None) -> int:
    """Run an admin command.

    Args:
        argv: Command line arguments. Defaults to `sys.argv[1:]`.
        repository: Storage to use. Defaults to Supabase, configured from the environment.

    Returns:
        Exit code: 0 on success, 1 on a handled error.
    """
    args = build_parser().parse_args(argv)
    try:
        repository = repository or SupabaseRepository.from_env()
        if args.command == "add-users":
            _print_add_users(repository, args.file)
        elif args.command == "status":
            _print_status(repository)
        elif args.command == "match":
            count = run_matching(repository, allow_empty=args.allow_empty, redraw=args.redraw)
            print(f"Draw done for {count} participants. Everyone can now log in to see who they give a gift to.")
        elif args.command == "reset-password":
            password = reset_password(repository, args.username)
            print(f"New password for {args.username}: {password}")
    except (AdminError, ConfigurationError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
