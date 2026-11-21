const DAY_IN_MS = 24 * 60 * 60 * 1000;
const DECEMBER = 11;

/**
 * Count the calendar days from a date until the next Christmas Eve (24 December), in the visitor's local time.
 * @param {Date} today
 * @returns {number} 0 on Christmas Eve itself.
 */
export function daysUntilChristmasEve(today) {
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  let christmasEve = new Date(today.getFullYear(), DECEMBER, 24);
  if (start > christmasEve) {
    christmasEve = new Date(today.getFullYear() + 1, DECEMBER, 24);
  }
  return Math.round((christmasEve - start) / DAY_IN_MS);
}

/**
 * Build the countdown shown next to the greeting, from Christmas Eve to Boxing Day a Christmas greeting instead.
 * @param {Date} [today]
 * @returns {Array<string | {bold: string}>} Text pieces in order; pieces given as `{bold}` are shown in bold.
 */
export function christmasCountdown(today = new Date()) {
  if (today.getMonth() === DECEMBER && [24, 25, 26].includes(today.getDate())) {
    return ["Merry Christmas! 🎄"];
  }
  const days = daysUntilChristmasEve(today);
  return ["Only ", { bold: String(days) }, ` ${days === 1 ? "day" : "days"} left until Christmas Eve!`];
}
