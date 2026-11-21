"""Row level security tests.

The Supabase migration runs on a local Postgres server with a minimal stand-in for Supabase's roles, grants and
`auth.uid()`. Each test then queries the database as a specific logged-in user, like the website does.
"""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pgserver
import psycopg
import pytest
from psycopg import errors

MIGRATIONS_DIR = Path(__file__).parents[1] / "supabase" / "migrations"

ANNA = "00000000-0000-0000-0000-00000000000a"
BEN = "00000000-0000-0000-0000-00000000000b"
CARL = "00000000-0000-0000-0000-00000000000c"
DORA = "00000000-0000-0000-0000-00000000000d"
NAMES = {ANNA: "Anna", BEN: "Ben", CARL: "Carl", DORA: "Dora"}
DRAW = {ANNA: BEN, BEN: CARL, CARL: DORA, DORA: ANNA}

SUPABASE_STAND_IN = """
create role anon nologin noinherit;
create role authenticated nologin noinherit;
create role service_role nologin noinherit bypassrls;
create schema auth;
create table auth.users (id uuid primary key);
create function auth.uid() returns uuid language sql stable as $$
    select (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')::uuid
$$;
grant usage on schema auth to anon, authenticated, service_role;
grant usage on schema public to anon, authenticated, service_role;
alter default privileges in schema public grant all on tables to anon, authenticated, service_role;
"""

SEED = "".join(
    f"""
    insert into auth.users (id) values ('{user_id}');
    insert into public.profiles (id, username, display_name) values ('{user_id}', '{name.lower()}', '{name}');
    insert into public.wishlist_items (owner_id, title) values ('{user_id}', '{name} wish');
    """
    for user_id, name in NAMES.items()
)


@pytest.fixture(scope="module")
def database_uri(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Start a Postgres server with the Supabase stand-in, all migrations and seed data."""
    server = pgserver.get_server(tmp_path_factory.mktemp("pgdata"), cleanup_mode="stop")
    uri = server.get_uri()
    with psycopg.connect(uri, autocommit=True) as connection:
        connection.execute(SUPABASE_STAND_IN)
        for migration in sorted(MIGRATIONS_DIR.glob("*.sql")):
            connection.execute(migration.read_text(encoding="utf-8"))
        connection.execute(SEED)
    yield uri
    server.cleanup()


@pytest.fixture
def connection(database_uri: str) -> Iterator[psycopg.Connection]:
    """Provide a superuser connection whose changes are rolled back after the test."""
    with psycopg.connect(database_uri) as connection:
        with connection.transaction(force_rollback=True):
            yield connection


@pytest.fixture
def drawn(connection: psycopg.Connection) -> None:
    """Store the draw Anna -> Ben -> Carl -> Dora -> Anna."""
    for giver, receiver in DRAW.items():
        connection.execute("insert into public.assignments values (%s, %s)", (giver, receiver))


@contextmanager
def acting_as(connection: psycopg.Connection, user_id: str | None) -> Iterator[psycopg.Connection]:
    """Run queries as a logged-in user, or as an anonymous visitor if `user_id` is None."""
    with connection.transaction():
        if user_id is None:
            connection.execute("set local role anon")
        else:
            claims = json.dumps({"sub": user_id, "role": "authenticated"})
            connection.execute("select set_config('request.jwt.claims', %s, true)", (claims,))
            connection.execute("set local role authenticated")
        yield connection
        connection.execute("reset role")
        connection.execute("select set_config('request.jwt.claims', '', true)")


def visible(connection: psycopg.Connection, user_id: str, query: str) -> set[tuple]:
    """Return the rows a user gets for a query."""
    with acting_as(connection, user_id):
        return set(connection.execute(query).fetchall())


def item_titles(connection: psycopg.Connection, user_id: str) -> set[str]:
    """Return the titles of all wishlist items a user can see."""
    return {title for (title,) in visible(connection, user_id, "select title from public.wishlist_items")}


@pytest.mark.parametrize("table", ["profiles", "wishlist_items", "assignments"])
def test_anonymous_visitors_cannot_read_anything(connection: psycopg.Connection, table: str) -> None:
    """Without logging in, every table is off limits."""
    with pytest.raises(errors.InsufficientPrivilege), acting_as(connection, None):
        connection.execute(f"select * from public.{table}")


def test_before_the_draw_users_only_see_themselves(connection: psycopg.Connection) -> None:
    """Before the draw, a user sees their own profile and wishes and nothing else."""
    assert item_titles(connection, ANNA) == {"Anna wish"}
    assert visible(connection, ANNA, "select display_name from public.profiles") == {("Anna",)}
    assert visible(connection, ANNA, "select * from public.assignments") == set()


@pytest.mark.usefixtures("drawn")
@pytest.mark.parametrize("giver", list(DRAW))
def test_after_the_draw_users_see_only_their_giftee(connection: psycopg.Connection, giver: str) -> None:
    """After the draw, a user additionally sees the profile and wishes of the person they give to."""
    receiver = DRAW[giver]

    assert item_titles(connection, giver) == {f"{NAMES[giver]} wish", f"{NAMES[receiver]} wish"}
    assert visible(connection, giver, "select display_name from public.profiles") == {
        (NAMES[giver],),
        (NAMES[receiver],),
    }
    assert visible(connection, giver, "select giver_id::text, receiver_id::text from public.assignments") == {
        (giver, receiver)
    }


@pytest.mark.usefixtures("drawn")
def test_giftees_see_updates_to_wishes(connection: psycopg.Connection) -> None:
    """Wishes added after the draw show up for the person giving the gift."""
    with acting_as(connection, BEN):
        connection.execute("insert into public.wishlist_items (title) values ('Late wish')")

    assert item_titles(connection, ANNA) == {"Anna wish", "Ben wish", "Late wish"}


def test_users_can_add_edit_and_delete_their_own_wishes(connection: psycopg.Connection) -> None:
    """Users manage their own wishlist; new wishes belong to the logged-in user automatically."""
    with acting_as(connection, ANNA):
        connection.execute(
            "insert into public.wishlist_items (title, link, note) values (%s, %s, %s)",
            ("Book", "https://example.org/book", "Hardcover"),
        )
        connection.execute("update public.wishlist_items set title = 'Socks' where title = 'Anna wish'")
        connection.execute("delete from public.wishlist_items where title = 'Book'")

    rows = connection.execute("select title, owner_id::text from public.wishlist_items where owner_id = %s", (ANNA,))
    assert set(rows.fetchall()) == {("Socks", ANNA)}


def test_users_cannot_add_wishes_for_someone_else(connection: psycopg.Connection) -> None:
    """The owner of a new wish cannot be chosen."""
    with pytest.raises(errors.InsufficientPrivilege), acting_as(connection, ANNA):
        connection.execute("insert into public.wishlist_items (owner_id, title) values (%s, 'Fake')", (BEN,))


@pytest.mark.usefixtures("drawn")
def test_users_cannot_change_or_delete_their_giftees_wishes(connection: psycopg.Connection) -> None:
    """Seeing the giftee's wishes does not allow changing them."""
    with acting_as(connection, ANNA):
        updated = connection.execute("update public.wishlist_items set title = 'Changed' where owner_id = %s", (BEN,))
        assert updated.rowcount == 0
        deleted = connection.execute("delete from public.wishlist_items where owner_id = %s", (BEN,))
        assert deleted.rowcount == 0

    assert connection.execute("select count(*) from public.wishlist_items").fetchone() == (4,)
    assert connection.execute("select title from public.wishlist_items where owner_id = %s", (BEN,)).fetchone() == (
        "Ben wish",
    )


def test_users_cannot_give_their_wishes_to_someone_else(connection: psycopg.Connection) -> None:
    """The owner of an existing wish cannot be changed."""
    with pytest.raises(errors.InsufficientPrivilege), acting_as(connection, ANNA):
        connection.execute("update public.wishlist_items set owner_id = %s", (BEN,))


@pytest.mark.parametrize(
    "statement",
    [
        f"insert into public.assignments values ('{ANNA}', '{CARL}')",
        "delete from public.assignments",
        "update public.profiles set display_name = 'Hacker'",
        f"insert into public.profiles values ('{ANNA}', 'x', 'x')",
    ],
)
def test_users_cannot_change_the_draw_or_profiles(connection: psycopg.Connection, statement: str) -> None:
    """Only the admin can write profiles and assignments."""
    with pytest.raises(errors.InsufficientPrivilege), acting_as(connection, ANNA):
        connection.execute(statement)


@pytest.mark.parametrize("link", ["javascript:alert(1)", "ftp://example.org", "example.org"])
def test_links_must_be_web_addresses(connection: psycopg.Connection, link: str) -> None:
    """Only http(s) links can be stored, so a link can never run code in someone else's browser."""
    with pytest.raises(errors.CheckViolation), acting_as(connection, ANNA):
        connection.execute("insert into public.wishlist_items (title, link) values ('Wish', %s)", (link,))
