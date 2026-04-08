import { useState, useEffect } from "react";
import { api } from "../api/client";
import { formatAmount } from "../api/utils";

export default function Debts() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all"); // all, lent, borrowed

  useEffect(() => {
    loadDebts();
  }, []);

  async function loadDebts() {
    setLoading(true);
    try {
      const res = await api.getDebts();
      setData(res);
    } catch (err) {
      console.error("Qarzlar yuklash xatoligi:", err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <p>Yuklanmoqda...</p>
      </div>
    );
  }

  if (!data || data.debts.length === 0) {
    return (
      <div>
        <div className="section-header">
          <span className="section-title">Qarzlar</span>
        </div>
        <div className="empty-state">
          <div className="emoji">📭</div>
          <p>Hozircha qarzlar yo'q</p>
        </div>
      </div>
    );
  }

  const currency = data.currency || "UZS";
  const { summary } = data;

  const filteredDebts = data.debts.filter((d) => {
    if (filter === "lent") return d.type === "lent";
    if (filter === "borrowed") return d.type === "borrowed";
    return true;
  });

  return (
    <div>
      <div className="section-header">
        <span className="section-title">Qarzlar</span>
      </div>

      {/* Umumiy xulosa */}
      <div className="balance-card">
        <div className="sub-row" style={{ borderTop: "none", marginTop: 0, paddingTop: 0 }}>
          <div className="sub-item">
            <div className="sub-label">Berganlarim</div>
            <div className="sub-amount income">
              {formatAmount(summary.total_lent, currency)}
            </div>
            <div className="sub-label">{summary.lent_count} ta</div>
          </div>
          <div className="sub-item">
            <div className="sub-label">Olganlarim</div>
            <div className="sub-amount expense">
              {formatAmount(summary.total_borrowed, currency)}
            </div>
            <div className="sub-label">{summary.borrowed_count} ta</div>
          </div>
        </div>
      </div>

      {/* Filter */}
      <div className="period-tabs">
        {[
          { key: "all", label: "Barchasi" },
          { key: "lent", label: "Berganlarim" },
          { key: "borrowed", label: "Olganlarim" },
        ].map((f) => (
          <button
            key={f.key}
            className={`period-tab ${filter === f.key ? "active" : ""}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Qarzlar ro'yxati */}
      <div style={{ padding: "0 12px" }}>
        {filteredDebts.map((debt) => (
          <div key={debt.id} className="debt-item">
            <div className="debt-header">
              <div>
                <span className="debt-person">{debt.person_name}</span>
                <span
                  className={`debt-type-badge ${debt.type}`}
                  style={{ marginLeft: 8 }}
                >
                  {debt.type === "lent" ? "Berdim" : "Oldim"}
                </span>
              </div>
              <div className="debt-amount">
                {formatAmount(debt.remaining, currency)}
              </div>
            </div>

            <div className="debt-meta">
              {debt.remaining < debt.amount && (
                <span>
                  Jami: {formatAmount(debt.amount, currency)} ·
                  To'langan: {formatAmount(debt.paid_amount, currency)}
                </span>
              )}
              {debt.due_date && (
                <span>
                  {" · "}
                  Muddat: {new Date(debt.due_date).toLocaleDateString("uz")}
                </span>
              )}
              {debt.is_overdue && (
                <span className="debt-overdue"> · Muddati o'tdi!</span>
              )}
            </div>

            {debt.description && (
              <div className="debt-meta">{debt.description}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
