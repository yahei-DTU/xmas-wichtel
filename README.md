# Xmas Wichtel

Family wishlists and a secret santa draw. Family members log in to a small website, write their Christmas wishlist,
and after the admin runs the draw they see who they give a gift to and that person's wishlist.

- **Website**: plain HTML/JS in `web/`, hosted for free on GitHub Pages.
- **Backend**: Supabase (free tier) for accounts and the database. Row level security makes sure everyone only sees
  their own wishlist and their giftee's.
- **Admin CLI**: Python, run locally to create accounts, follow progress and run the draw.

## Quickstart

1. Set up Supabase and GitHub Pages: [docs/source/setup.md](docs/source/setup.md).
2. Create accounts and run the draw: [docs/source/admin.md](docs/source/admin.md).

```bash
uv sync
cp participants.example.yaml participants.yaml   # list everyone taking part
cp .env.example .env                             # add your Supabase URL and secret key
uv run invoke add-users                          # prints the credentials to hand out
uv run invoke status                             # who has entered wishes?
uv run invoke match                              # the draw
```

## Project structure

```txt
├── .github/
│   ├── dependabot.yaml
│   └── workflows/
│       ├── deploy_pages.yaml     # Publishes web/ to GitHub Pages
│       ├── linting.yaml
│       ├── pre-commit-update.yaml
│       └── tests.yaml
├── docs/                         # mkdocs documentation (setup, admin guide, code reference)
├── src/xmas_wichtel/
│   ├── admin.py                  # Admin commands: add users, status, draw, reset password
│   ├── cli.py                    # `wichtel` command line interface
│   ├── matching.py               # The draw algorithm
│   └── repository.py             # Supabase access with the secret key
├── supabase/migrations/          # Tables and row level security policies
├── tests/                        # Unit tests, incl. access rules checked on a local Postgres
├── web/                          # The website (no build step)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                # Supabase calls
│       ├── config.js             # Project URL and publishable key
│       └── main.js               # UI logic
├── .env.example                  # Template for the local secret key (.env is gitignored)
├── participants.example.yaml     # Template for the participant list (participants.yaml is gitignored)
├── pyproject.toml
└── tasks.py                      # invoke tasks
```

## Development

```bash
uv run invoke test        # tests incl. row level security checks on an embedded Postgres
uv run ruff check .
uv run invoke serve-web   # website at http://localhost:8000
uv run invoke serve-docs  # documentation
```
