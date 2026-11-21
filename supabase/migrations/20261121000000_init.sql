-- Wichtel schema: participants, their wishlist items and the secret santa assignments.
-- Logged-in users may only see their own data plus the profile and wishlist of the person they give a gift to.
-- The admin CLI uses the secret key, which bypasses row level security.

create table public.profiles (
    id uuid primary key references auth.users (id) on delete cascade,
    username text not null unique check (username ~ '^[a-z0-9_-]{1,32}$'),
    display_name text not null check (char_length(display_name) between 1 and 100)
);

create table public.wishlist_items (
    id uuid primary key default gen_random_uuid(),
    owner_id uuid not null default auth.uid() references public.profiles (id) on delete cascade,
    title text not null check (char_length(title) between 1 and 200),
    link text check (link ~* '^https?://' and char_length(link) <= 2000),
    note text check (char_length(note) <= 1000),
    created_at timestamptz not null default now()
);

create index wishlist_items_owner_id_idx on public.wishlist_items (owner_id);

create table public.assignments (
    giver_id uuid primary key references public.profiles (id) on delete cascade,
    receiver_id uuid not null unique references public.profiles (id) on delete cascade,
    check (giver_id <> receiver_id)
);

alter table public.profiles enable row level security;
alter table public.wishlist_items enable row level security;
alter table public.assignments enable row level security;

revoke all on public.profiles, public.wishlist_items, public.assignments from anon, authenticated;
grant select on public.profiles, public.assignments to authenticated;
grant select, delete on public.wishlist_items to authenticated;
grant insert (title, link, note), update (title, link, note) on public.wishlist_items to authenticated;
grant all on public.profiles, public.wishlist_items, public.assignments to service_role;

create policy "Read own assignment" on public.assignments
    for select to authenticated
    using (giver_id = (select auth.uid()));

create policy "Read own and giftee's profile" on public.profiles
    for select to authenticated
    using (
        id = (select auth.uid())
        or id = (select receiver_id from public.assignments where giver_id = (select auth.uid()))
    );

create policy "Read own and giftee's items" on public.wishlist_items
    for select to authenticated
    using (
        owner_id = (select auth.uid())
        or owner_id = (select receiver_id from public.assignments where giver_id = (select auth.uid()))
    );

create policy "Add own items" on public.wishlist_items
    for insert to authenticated
    with check (owner_id = (select auth.uid()));

create policy "Edit own items" on public.wishlist_items
    for update to authenticated
    using (owner_id = (select auth.uid()))
    with check (owner_id = (select auth.uid()));

create policy "Delete own items" on public.wishlist_items
    for delete to authenticated
    using (owner_id = (select auth.uid()));
