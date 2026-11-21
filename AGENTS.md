> Guidance for autonomous coding agents
> Read this before writing, editing, or executing anything in this repo.

# Relevant commands

* The project uses `uv` for management of virtual environments. This means:
  * To install packages, use `uv add <package-name>`.
  * To run Python scripts, use `uv run <script-name>.py`.
  * To run other commands related to Python, prefix them with `uv run `, e.g., `uv run <command>`.
* The project uses `pytest` for testing. To run tests, use `uv run pytest tests/`.
* The project uses `ruff` for linting and formatting:
    * To format code, use `uv run ruff format .`.
    * To lint code, use `uv run ruff check . --fix`.
* The project uses `invoke` for task management. To see available tasks, use `uv run invoke --list` or refer to the
    `tasks.py` file.
* The project uses `pre-commit` for managing pre-commit hooks. To run all hooks on all files, use
    `uv run pre-commit run --all-files`. For more information, refer to the `.pre-commit-config.yaml` file.
* The admin CLI is `uv run wichtel <command>` (`add-users`, `status`, `match`, `reset-password`), also available as
    invoke tasks. It talks to the real Supabase project configured in `.env`; never run it against production
    as part of testing.
* To serve the website locally, use `uv run invoke serve-web`. The website in `web/` is plain HTML/JS without a build
    step and is deployed to GitHub Pages by `.github/workflows/deploy_pages.yaml`.
* Database schema and row level security live in `supabase/migrations/`. `tests/test_policies.py` applies them to an
    embedded Postgres (`pgserver`); update those tests whenever the policies change.

# Code style

* Follow existing code style.
* Keep line length within 120 characters.
* Use f-strings for formatting.
* Use type hints
* Do not add inline comments unless absolutely necessary.

# Documentation

* If the project has a `docs/` folder, update documentation there as needed.
* In this case the project will be using `mkdocs` for documentation. To build the docs locally, use
    `uv run mkdocs serve`
* Use existing docstring style.
* Ensure all functions and classes have docstrings.
* Use Google style for docstrings.
* Update this `AGENTS.md` file if any new tools or commands are added to the project.
