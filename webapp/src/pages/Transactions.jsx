import { useState, useEffect } from "react";
import { api } from "../api/client";
import { formatAmount, formatDate, formatShortDate } from "../api/utils";

const PERIODS = [
  { key: "today", label: "Bugun" },
  { key: "week", label: "Hafta" },
  { key: "month", label: "Oy" },
  { key: "all", label: "Barchasi" },
];

const TYPES = [
  { key: null, label: "Barchasi" },
  { key: "expense", label: "Chiqim" },
  { key: "income", label: "Kirim" },
];

export default function Transactions() {
  const [period, setPeriod] = useState("month");
  const [typeFilter, setTypeFilter] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [currency, setCurrency] = useState("UZS");
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  useEffect(() => {
    setPage(1);
    loadTransactions(1);
  }, [period, typeFilter]);

  async function loadTransactions(p) {
    setLoading(true);
    try {
      const params = { period, page: p, limit: 20 };
      if (typeFilter) params.type = typeFilter;

      const res = await api.getTransactions(params);
      setTransactions(p === 1 ? res.transactions : [...transactions, ...res.transactions]);
      setCurrency(res.currency || "UZS");
    } catch (err) {
      console.error("Tranzaksiyalar yuklash xatoligi:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id) {
    if (!confirm("Bu tranzaksiyani o'chirmoqchimisiz?")) return;
    try {
      await api.deleteTransaction(id);
      setTransactions(transactions.filter((tx) => tx.id !== id));
    } catch (err) {
      console.error("O'chirish xatoligi:", err);
    }
  }

  function loadMore() {
    const next = page + 1;
    setPage(next);
    loadTransactions(next);
  }

  return (
    <div>
      <div className="section-header">
        <span className="section-title">Tranzaksiyalar</span>
      </div>

      {/* Davr filtri */}
      <div className="period-tabs">
        {PERIODS.map((p) => (
          <button
            key={p.key}
            className={`period-tab ${period === p.key ? "active" : ""}`}
            onClick={() => setPeriod(p.key)}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Tur filtri */}
      <div className="period-tabs">
        {TYPES.map((t) => (
          <button
            key={t.key || "all"}
            className={`period-tab ${typeFilter === t.key ? "active" : ""}`}
            onClick={() => setTypeFilter(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Ro'yxat */}
      <div className="tx-list">
        {loading && transactions.length === 0 ? (
          <div className="loading">
            <div className="spinner" />
            <p>Yuklanmoqda...</p>
          </div>
        ) : transactions.length === 0 ? (
          <div className="empty-state">
            <div className="emoji">📭</div>
            <p>Bu davrda tranzaksiyalar yo'q</p>
          </div>
        ) : (
          transactions.map((tx) => (
            <div key={tx.id} className="tx-item" onClick={() => handleDelete(tx.id)}>
              <div className="tx-icon">
                {tx.category?.icon || "📦"}
              </div>
              <div className="tx-info">
                <div className="tx-category">
                  {tx.category?.name || "Boshqa"}
                </div>
                <div className="tx-desc">
                  {tx.description || (tx.type === "income" ? "Kirim" : "Chiqim")}
                </div>
              </div>
              <div className="tx-right">
                <div className={`tx-amount ${tx.type}`}>
                  {tx.type === "income" ? "+" : "-"}
                  {formatAmount(tx.amount, currency)}
                </div>
                <div className="tx-time">{formatShortDate(tx.created_at)}</div>
              </div>
            </div>
          ))
        )}

        {transactions.length >= page * 20 && (
          <button
            className="period-tab"
            style={{ width: "100%", margin: "12px 0" }}
            onClick={loadMore}
          >
            Ko'proq yuklash
          </button>
        )}
      </div>
    </div>
  );
}
