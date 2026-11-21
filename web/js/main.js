import * as api from "./api.js";
import { SUPABASE_URL } from "./config.js";
import { christmasCountdown } from "./countdown.js";

const $ = (id) => document.getElementById(id);

const loading = $("loading");
const setupHint = $("setup-hint");
const loginView = $("login-view");
const loginForm = $("login-form");
const loginError = $("login-error");
const appView = $("app-view");
const appError = $("app-error");
const displayName = $("display-name");
const countdown = $("countdown");
const logoutButton = $("logout-button");
const myWishes = $("my-wishes");
const myWishesEmpty = $("my-wishes-empty");
const wishForm = $("wish-form");
const wishFormTitle = $("wish-form-title");
const wishSubmit = $("wish-submit");
const wishCancel = $("wish-cancel");
const wishError = $("wish-error");
const gifteePending = $("giftee-pending");
const giftee = $("giftee");
const gifteeWishes = $("giftee-wishes");
const gifteeWishesEmpty = $("giftee-wishes-empty");

const state = { userId: null, editingId: null };

/**
 * Turn any thrown value into a readable message.
 * @param {unknown} error
 * @returns {string}
 */
function describe(error) {
  return error?.message ?? String(error);
}

/**
 * Enable or disable all buttons of a form while a request is running.
 * @param {HTMLFormElement} form
 * @param {boolean} busy
 */
function setBusy(form, busy) {
  for (const button of form.querySelectorAll("button")) {
    button.disabled = busy;
  }
}

/**
 * Check whether a value is an http(s) address that is safe to use as a link.
 * @param {string | null} value
 * @returns {boolean}
 */
function isWebLink(value) {
  try {
    return ["http:", "https:"].includes(new URL(value).protocol);
  } catch {
    return false;
  }
}

/**
 * Clean up a link typed by the user, adding https:// if it is missing.
 * @param {string} value
 * @returns {string | null} The link, or null if the field was empty.
 */
function normalizeLink(value) {
  const link = value.trim();
  if (!link) {
    return null;
  }
  const withScheme = /^[a-z][a-z0-9+.-]*:\/\//i.test(link) ? link : `https://${link}`;
  if (!isWebLink(withScheme)) {
    throw new Error("That link does not look like a web address.");
  }
  return withScheme;
}

/**
 * Create a small button that runs a function when clicked.
 * @param {string} label
 * @param {() => void} onClick
 * @returns {HTMLButtonElement}
 */
function actionButton(label, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "secondary";
  button.textContent = label;
  button.addEventListener("click", onClick);
  return button;
}

/**
 * Build the list entry of one wish. All user content is set as text, never as HTML.
 * @param {{id: string, title: string, link: string | null, note: string | null}} wish
 * @param {boolean} editable Whether to show edit and delete buttons.
 * @returns {HTMLLIElement}
 */
function renderWish(wish, editable) {
  const item = document.createElement("li");
  item.className = "wish";

  const body = document.createElement("div");
  body.className = "wish-body";
  const hasLink = isWebLink(wish.link);
  const title = document.createElement(hasLink ? "a" : "span");
  title.className = "wish-title";
  title.textContent = wish.title;
  if (hasLink) {
    title.href = wish.link;
    title.target = "_blank";
    title.rel = "noopener noreferrer";
  }
  body.append(title);
  if (wish.note) {
    const note = document.createElement("p");
    note.className = "wish-note";
    note.textContent = wish.note;
    body.append(note);
  }
  item.append(body);

  if (editable) {
    const actions = document.createElement("div");
    actions.className = "wish-actions";
    actions.append(
      actionButton("Edit", () => startEditing(wish)),
      actionButton("Delete", () => removeWish(wish)),
    );
    item.append(actions);
  }
  return item;
}

/** Reload and show the logged-in user's wishlist. */
async function refreshMyWishes() {
  const wishes = await api.listWishes(state.userId);
  myWishes.replaceChildren(...wishes.map((wish) => renderWish(wish, true)));
  myWishesEmpty.hidden = wishes.length > 0;
}

/** Show who the user gives a gift to and their wishlist, or a waiting message before the draw. */
async function refreshGiftee() {
  const gifteeId = await api.getGifteeId(state.userId);
  gifteePending.hidden = gifteeId !== null;
  giftee.hidden = gifteeId === null;
  if (gifteeId === null) {
    return;
  }
  const [name, wishes] = await Promise.all([api.getDisplayName(gifteeId), api.listWishes(gifteeId)]);
  for (const element of giftee.querySelectorAll(".giftee-name")) {
    element.textContent = name;
  }
  gifteeWishes.replaceChildren(...wishes.map((wish) => renderWish(wish, false)));
  gifteeWishesEmpty.hidden = wishes.length > 0;
}

/**
 * Fill the wish form with an existing wish so it can be changed.
 * @param {{id: string, title: string, link: string | null, note: string | null}} wish
 */
function startEditing(wish) {
  state.editingId = wish.id;
  wishForm.elements.title.value = wish.title;
  wishForm.elements.link.value = wish.link ?? "";
  wishForm.elements.note.value = wish.note ?? "";
  wishFormTitle.textContent = "Edit wish";
  wishSubmit.textContent = "Save";
  wishCancel.hidden = false;
  wishError.textContent = "";
  wishForm.scrollIntoView({ behavior: "smooth", block: "center" });
  wishForm.elements.title.focus({ preventScroll: true });
}

/** Reset the wish form to adding a new wish. */
function stopEditing() {
  state.editingId = null;
  wishForm.reset();
  wishFormTitle.textContent = "Add a wish";
  wishSubmit.textContent = "Add";
  wishCancel.hidden = true;
  wishError.textContent = "";
}

/**
 * Delete a wish after asking for confirmation.
 * @param {{id: string, title: string}} wish
 */
async function removeWish(wish) {
  if (!window.confirm(`Delete "${wish.title}"?`)) {
    return;
  }
  appError.textContent = "";
  try {
    await api.deleteWish(wish.id);
    if (state.editingId === wish.id) {
      stopEditing();
    }
    await refreshMyWishes();
  } catch (error) {
    appError.textContent = `Could not delete the wish: ${describe(error)}`;
  }
}

/** Show the login form. */
function showLogin() {
  state.userId = null;
  loading.hidden = true;
  appView.hidden = true;
  loginView.hidden = false;
  loginForm.elements.username.focus();
}

/**
 * Show the wishlist page of a logged-in user.
 * @param {string} userId
 */
async function showApp(userId) {
  state.userId = userId;
  stopEditing();
  appError.textContent = "";
  loginView.hidden = true;
  countdown.replaceChildren(
    ...christmasCountdown().map((part) =>
      typeof part === "string" ? part : Object.assign(document.createElement("strong"), { textContent: part.bold }),
    ),
  );
  try {
    const [name] = await Promise.all([api.getDisplayName(userId), refreshMyWishes(), refreshGiftee()]);
    displayName.textContent = name;
  } catch (error) {
    appError.textContent = `Could not load your data: ${describe(error)}`;
  } finally {
    loading.hidden = true;
    appView.hidden = false;
  }
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginError.textContent = "";
  setBusy(loginForm, true);
  const form = new FormData(loginForm);
  let userId;
  try {
    userId = await api.logIn(form.get("username"), form.get("password"));
  } catch (error) {
    loginError.textContent = error?.status === 400 ? "Wrong username or password." : describe(error);
    return;
  } finally {
    setBusy(loginForm, false);
  }
  loginForm.reset();
  await showApp(userId);
});

logoutButton.addEventListener("click", async () => {
  try {
    await api.logOut();
  } finally {
    showLogin();
  }
});

wishForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  wishError.textContent = "";
  const form = new FormData(wishForm);
  setBusy(wishForm, true);
  try {
    const wish = {
      title: form.get("title").trim(),
      link: normalizeLink(form.get("link")),
      note: form.get("note").trim() || null,
    };
    if (!wish.title) {
      throw new Error("Please describe your wish.");
    }
    if (state.editingId) {
      await api.updateWish(state.editingId, wish);
    } else {
      await api.addWish(wish);
    }
    stopEditing();
    await refreshMyWishes();
  } catch (error) {
    wishError.textContent = describe(error);
  } finally {
    setBusy(wishForm, false);
  }
});

wishCancel.addEventListener("click", stopEditing);

/** Show the setup hint, the wishlist page or the login form, depending on configuration and session. */
async function start() {
  if (SUPABASE_URL.includes("your-project-ref")) {
    loading.hidden = true;
    setupHint.hidden = false;
    return;
  }
  const userId = await api.getCurrentUserId();
  if (userId) {
    await showApp(userId);
  } else {
    showLogin();
  }
}

start();
