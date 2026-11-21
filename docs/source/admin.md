# Admin guide

All commands run on your machine and need a filled-in `.env` (see [Setup](setup.md)). Each `invoke` task is a
shortcut for the equivalent `uv run wichtel …` command.

## Create accounts

```bash
cp participants.example.yaml participants.yaml   # then list everyone taking part, including yourself
uv run invoke add-users
```

```yaml
participants:
  - username: anna          # what they type to log in: lowercase letters, digits, _ or -
    display_name: Anna      # what the others see
```

The command prints a generated password for every new account. Send each person their username, password and the
website link. Passwords are not shown again. If someone loses theirs, give them a new one:

```bash
uv run invoke reset-password --username anna
```

Running `add-users` again only creates accounts for new entries, so you can add late participants before the draw.

## Follow progress

```bash
uv run invoke status
```

This shows how many wishes everyone has entered. It never shows the wishes themselves or the draw.

## Run the draw

```bash
uv run invoke match
```

The draw refuses to run while someone's wishlist is still empty. Use `--allow-empty` to draw anyway. Everyone can
keep editing their wishlist after the draw, and the person giving them a gift sees the changes.

After the draw, the website shows each person who they give a gift to. The result is never printed, so you can take
part too. Just don't open the `assignments` table in the Supabase dashboard.

A finished draw is only replaced with `--redraw`. Everyone then gets a new person, so only do that if necessary,
e.g. when someone joins or leaves late:

```bash
uv run invoke match --redraw
```

## Remove a participant

Delete the user in the Supabase dashboard under **Authentication → Users**. Their profile, wishes and draw entries are
deleted with them. If the draw has already happened, run `match --redraw` afterwards.

## Next year

To start over with the same accounts, run this in the Supabase **SQL Editor**:

```sql
delete from public.assignments;
delete from public.wishlist_items;
```
