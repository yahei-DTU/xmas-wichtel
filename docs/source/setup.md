# Setup

Setup is done once and takes about 15 minutes. Menu names refer to the Supabase dashboard and may move slightly over
time.

## 1. Create the Supabase project

1. Sign up at [supabase.com](https://supabase.com) and create a new project on the free plan.
    - Pick a region close to your family, e.g. *Central EU (Frankfurt)*.
    - Save the database password somewhere safe. This app doesn't need it, but you can't view it again later.
    - Keep the Data API enabled (the default). The website uses it.
2. Open **SQL Editor**, paste the contents of `supabase/migrations/20261121000000_init.sql` and click **Run**.
   This creates the tables and access rules.
3. Open **Authentication → Sign In / Providers** and turn **off** *Allow new users to sign up*. Leave the *Email*
   provider enabled. Accounts are only created by the admin CLI, which still works with sign-ups disabled.

!!! note "Free tier pausing"
    Free Supabase projects are paused after about a week without any activity. The website then stops working until
    you click **Restore project** in the dashboard. No data is lost.

## 2. Configure the keys

Open **Project Settings → API Keys** in Supabase. The project URL is shown on the project's home page and under
**Project Settings → Data API**.

| Value | Goes into | Public? |
|---|---|---|
| Project URL | `web/js/config.js` (`SUPABASE_URL`) and `.env` (`SUPABASE_URL`) | yes |
| Publishable key (`sb_publishable_…`) | `web/js/config.js` (`SUPABASE_PUBLISHABLE_KEY`) | yes |
| Secret key (`sb_secret_…`) | `.env` (`SUPABASE_SECRET_KEY`) | **no, never commit it** |

```bash
cp .env.example .env   # then fill in SUPABASE_URL and SUPABASE_SECRET_KEY
```

If your project only shows the legacy keys, use the `anon` key as the publishable key and the `service_role` key as
the secret key.

The publishable key is safe to publish: it only lets visitors do what the access rules allow. The secret key bypasses
all rules, so it stays in `.env` on your machine. `.env` is listed in `.gitignore`.

## 3. Publish the website on GitHub Pages

1. On GitHub, open **Settings → Pages** and set **Source** to **GitHub Actions**.
2. Commit `web/js/config.js` with your project URL and publishable key and push to `main`.
3. The *Deploy website* workflow publishes `web/` to `https://<your-github-user>.github.io/<repository-name>/`.
   It runs again whenever something in `web/` changes, and can be started manually from the **Actions** tab.

Free GitHub accounts can only use Pages for public repositories. That is fine for the code, but `participants.yaml` and
`.env` must never be committed. Both are in `.gitignore`.

## 4. Try it locally (optional)

```bash
uv run invoke serve-web
```

This serves `web/` at <http://localhost:8000>, connected to your real Supabase project.
