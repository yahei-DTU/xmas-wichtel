# Xmas Wichtel

A small website where family members log in, write a Christmas wishlist, and — after the admin runs the draw — see
who they give a gift to and that person's wishlist.

## How it works

| Part | Runs on | Job |
|---|---|---|
| Website (`web/`) | GitHub Pages | Login, edit your own wishlist, see your giftee and their list |
| Supabase | Supabase free tier | User accounts, Postgres database, access rules |
| Admin CLI (`src/xmas_wichtel/`) | Your machine | Create accounts, check progress, run the draw |

The website talks to Supabase directly with the public *publishable key*. What each user may read or change is
enforced by row level security policies in the database (`supabase/migrations/`), not by the website:

| Table | A logged-in user can… |
|---|---|
| `profiles` | read their own name and their giftee's name |
| `wishlist_items` | read, add, change and delete their own wishes; read their giftee's wishes |
| `assignments` | read only who they give a gift to |

Visitors who are not logged in cannot read anything. The admin CLI uses the *secret key*, which bypasses these rules,
so it only ever runs on the admin's machine.

## The draw

Everyone is shuffled into one circle and gives a gift to the next person. Nobody draws themselves, everyone gives and
receives exactly one gift, and (with three or more people) no two people draw each other. The CLI never prints the
result, so the admin can take part too.

## Next steps

- [Setup](setup.md): create the Supabase project and publish the website.
- [Admin guide](admin.md): create accounts, follow progress and run the draw.
