import os

from invoke import Context, task

WINDOWS = os.name == "nt"
PROJECT_NAME = "xmas_wichtel"
PYTHON_VERSION = "3.12"


# Admin commands
@task
def add_users(ctx: Context, file: str = "participants.yaml") -> None:
    """Create accounts for everyone in the participants file and print their credentials."""
    ctx.run(f"uv run wichtel add-users --file {file}", echo=True, pty=not WINDOWS)


@task
def status(ctx: Context) -> None:
    """Show how many wishes everyone has entered and whether the draw has happened."""
    ctx.run("uv run wichtel status", echo=True, pty=not WINDOWS)


@task
def match(ctx: Context, allow_empty: bool = False, redraw: bool = False) -> None:
    """Draw who gives a gift to whom."""
    flags = f"{' --allow-empty' if allow_empty else ''}{' --redraw' if redraw else ''}"
    ctx.run(f"uv run wichtel match{flags}", echo=True, pty=not WINDOWS)


@task
def reset_password(ctx: Context, username: str) -> None:
    """Give a participant a new password."""
    ctx.run(f"uv run wichtel reset-password {username}", echo=True, pty=not WINDOWS)


@task
def serve_web(ctx: Context, port: int = 8000) -> None:
    """Serve the website locally at http://localhost:8000."""
    ctx.run(f"uv run python -m http.server {port} --directory web", echo=True, pty=not WINDOWS)


# Development commands
@task
def test(ctx: Context) -> None:
    """Run tests."""
    ctx.run("uv run coverage run -m pytest tests/", echo=True, pty=not WINDOWS)
    ctx.run("uv run coverage report -m -i", echo=True, pty=not WINDOWS)


# Documentation commands
@task
def build_docs(ctx: Context) -> None:
    """Build documentation."""
    ctx.run("uv run mkdocs build --config-file docs/mkdocs.yaml --site-dir build", echo=True, pty=not WINDOWS)


@task
def serve_docs(ctx: Context) -> None:
    """Serve documentation."""
    ctx.run("uv run mkdocs serve --config-file docs/mkdocs.yaml", echo=True, pty=not WINDOWS)
