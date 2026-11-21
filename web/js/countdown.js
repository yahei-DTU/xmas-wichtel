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
 * Build the countdown shown next to the greeting.
 * @param {Date} [today]
 * @returns {string}
 */
export function christmasCountdown(today = new Date()) {
  if (today.getMonth() === DECEMBER && [25, 26].includes(today.getDate())) {
    return "Merry Christmas! 🎄";
  }
  const days = daysUntilChristmasEve(today);
  if (days === 0) {
    return "It's Christmas Eve! 🎁";
  }
  return `Only ${days} ${days === 1 ? "day" : "days"} left until Christmas Eve!`;
}
