"""Tests for the admin command line interface."""

import re
from pathlib import Path

import pytest

from tests.fakes import FakeRepository
from xmas_wichtel.cli import main
from xmas_wichtel.repository import LOGIN_EMAIL_DOMAIN, username_to_email

WEB_CONFIG = Path(__file__).parents[1] / "web" / "js" / "config.js"


def test_add_users_prints_credentials(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """New accounts are printed with their passwords so they can be handed out."""
    participants = tmp_path / "participants.yaml"
    participants.write_text("participants:\n  - {username: anna, display_name: Anna}\n", encoding="utf-8")
    repository = FakeRepository()

    exit_code = main(["add-users", "--file", str(participants)], repository=repository)

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "username: anna" in output
    assert repository.passwords["id-anna"] in output


def test_status_lists_participants(capsys: pytest.CaptureFixture[str]) -> None:
    """Status shows who still needs to enter wishes."""
    repository = FakeRepository()
    repository.add_participant("anna", item_count=3)
    repository.add_participant("ben")

    assert main(["status"], repository=repository) == 0

    output = capsys.readouterr().out
    assert re.search(r"Anna \(anna\)\s+3 wish", output)
    assert re.search(r"Ben \(ben\)\s+0 wish.*no wishes yet", output)
    assert "Draw: not done yet" in output


def test_match_does_not_reveal_assignments(capsys: pytest.CaptureFixture[str]) -> None:
    """The admin is a participant too, so the draw result is never printed."""
    repository = FakeRepository()
    for name in ["anna", "ben", "carl"]:
        repository.add_participant(name, item_count=1)

    assert main(["match"], repository=repository) == 0

    output = capsys.readouterr().out
    assert "Draw done for 3 participants" in output
    assert not any(name in output.lower() for name in ["anna", "ben", "carl"])


def test_errors_are_reported_without_traceback(capsys: pytest.CaptureFixture[str]) -> None:
    """Handled errors print a message and return exit code 1."""
    assert main(["reset-password", "nobody"], repository=FakeRepository()) == 1

    assert "Error: No participant with username 'nobody'" in capsys.readouterr().err


def test_missing_configuration_is_reported(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Without Supabase settings the CLI explains what to configure."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)

    assert main(["status"]) == 1


def test_website_uses_the_same_login_domain() -> None:
    """The website must map usernames to the same emails the CLI creates accounts with."""
    match = re.search(r'LOGIN_EMAIL_DOMAIN\s*=\s*"([^"]+)"', WEB_CONFIG.read_text(encoding="utf-8"))

    assert match is not None
    assert match.group(1) == LOGIN_EMAIL_DOMAIN
    assert username_to_email("anna") == f"anna@{LOGIN_EMAIL_DOMAIN}"
