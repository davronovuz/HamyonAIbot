/**
 * API client — Telegram Mini App initData bilan autentifikatsiya.
 */

const BASE_URL = "/api";

function getInitData() {
  if (window.Telegram?.WebApp?.initData) {
    return window.Telegram.WebApp.initData;
  }
  return "";
}

async function request(path, options = {}) {
  const initData = getInitData();

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `tma ${initData}`,
      ...options.headers,
    },
  });

  if (!res.ok) {
    throw new Error(`API xatolik: ${res.status}`);
  }

  return res.json();
}

export const api = {
  // Transactions
  getTransactions: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/transactions?${query}`);
  },
  createTransaction: (data) =>
    request("/transactions", { method: "POST", body: JSON.stringify(data) }),
  deleteTransaction: (id) =>
    request(`/transactions/${id}`, { method: "DELETE" }),

  // Summary
  getSummary: (period = "month") => request(`/transactions/summary?period=${period}`),
  getCategoryBreakdown: (period = "month", type = "expense") =>
    request(`/transactions/categories?period=${period}&type=${type}`),
  getDailyChart: (year, month) =>
    request(`/transactions/daily-chart?year=${year}&month=${month}`),

  // Categories
  getCategories: (type) => {
    const query = type ? `?type=${type}` : "";
    return request(`/categories${query}`);
  },

  // Debts
  getDebts: () => request("/debts"),
};
