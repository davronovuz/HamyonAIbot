/**
 * Summani chiroyli formatda chiqarish.
 * formatAmount(1250000, "UZS") → "1 250 000 so'm"
 */
const CURRENCY_MAP = {
  UZS: "so'm",
  USD: "$",
  RUB: "₽",
  EUR: "€",
};

export function formatAmount(amount, currency = "UZS") {
  const symbol = CURRENCY_MAP[currency] || "so'm";

  if (currency === "UZS") {
    const formatted = Math.round(amount)
      .toString()
      .replace(/\B(?=(\d{3})+(?!\d))/g, " ");
    return `${formatted} ${symbol}`;
  }

  const formatted = amount
    .toFixed(2)
    .replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return `${formatted} ${symbol}`;
}

/**
 * Sanani formatlash.
 * formatDate("2026-04-08T14:30:00") → "8-aprel, 14:30"
 */
const MONTHS = [
  "", "yanvar", "fevral", "mart", "aprel", "may", "iyun",
  "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr",
];

export function formatDate(isoString) {
  const d = new Date(isoString);
  const day = d.getDate();
  const month = MONTHS[d.getMonth() + 1];
  const hours = d.getHours().toString().padStart(2, "0");
  const mins = d.getMinutes().toString().padStart(2, "0");
  return `${day}-${month}, ${hours}:${mins}`;
}

export function formatShortDate(isoString) {
  const d = new Date(isoString);
  return `${d.getDate().toString().padStart(2, "0")}.${(d.getMonth() + 1)
    .toString()
    .padStart(2, "0")} ${d.getHours().toString().padStart(2, "0")}:${d
    .getMinutes()
    .toString()
    .padStart(2, "0")}`;
}
