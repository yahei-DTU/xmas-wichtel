import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.119.0/+esm";
import { LOGIN_EMAIL_DOMAIN, SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL } from "./config.js";

const supabase = createClient(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);

/**
 * Return the data of a Supabase response, or throw its error.
 * @param {{data: any, error: Error | null}} response
 * @returns {any}
 */
function unwrap({ data, error }) {
  if (error) {
    throw error;
  }
  return data;
}

/**
 * Return the ID of the logged-in user, or null if nobody is logged in.
 * @returns {Promise<string | null>}
 */
export async function getCurrentUserId() {
  const { data } = await supabase.auth.getSession();
  return data.session?.user.id ?? null;
}

/**
 * Log in with the username and password handed out by the admin.
 * @param {string} username
 * @param {string} password
 * @returns {Promise<string>} ID of the logged-in user.
 */
export async function logIn(username, password) {
  const email = `${username.trim().toLowerCase()}@${LOGIN_EMAIL_DOMAIN}`;
  const data = unwrap(await supabase.auth.signInWithPassword({ email, password }));
  return data.user.id;
}

/** Log out the current user. */
export async function logOut() {
  unwrap(await supabase.auth.signOut());
}

/**
 * Return the display name of a participant (yourself or the person you give a gift to).
 * @param {string} userId
 * @returns {Promise<string>}
 */
export async function getDisplayName(userId) {
  const profile = unwrap(await supabase.from("profiles").select("display_name").eq("id", userId).single());
  return profile.display_name;
}

/**
 * Return the ID of the person the user gives a gift to, or null before the draw.
 * @param {string} userId
 * @returns {Promise<string | null>}
 */
export async function getGifteeId(userId) {
  const assignment = unwrap(
    await supabase.from("assignments").select("receiver_id").eq("giver_id", userId).maybeSingle(),
  );
  return assignment?.receiver_id ?? null;
}

/**
 * Return the wishes of a participant, oldest first.
 * @param {string} ownerId
 * @returns {Promise<Array<{id: string, title: string, link: string | null, note: string | null}>>}
 */
export async function listWishes(ownerId) {
  return unwrap(
    await supabase.from("wishlist_items").select("id, title, link, note").eq("owner_id", ownerId).order("created_at"),
  );
}

/**
 * Add a wish to the logged-in user's wishlist.
 * @param {{title: string, link: string | null, note: string | null}} wish
 */
export async function addWish(wish) {
  unwrap(await supabase.from("wishlist_items").insert(wish));
}

/**
 * Change one of the logged-in user's wishes.
 * @param {string} id
 * @param {{title: string, link: string | null, note: string | null}} wish
 */
export async function updateWish(id, wish) {
  unwrap(await supabase.from("wishlist_items").update(wish).eq("id", id));
}

/**
 * Delete one of the logged-in user's wishes.
 * @param {string} id
 */
export async function deleteWish(id) {
  unwrap(await supabase.from("wishlist_items").delete().eq("id", id));
}
