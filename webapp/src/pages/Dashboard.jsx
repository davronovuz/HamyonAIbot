import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { api } from "../api/client";
import { formatAmount } from "../api/utils";

const PERIODS = [
  { key: "today", label: "Bugun" },
  { key: "week", label: "Hafta" },
  { key: "month", label: "Oy" },
];

export default function Dashboard() {
  const [period, setPeriod] = useState("month");
  const [summary, setSummary] = useState(null);
  const [categories, setCategories] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [period]);

  async function loadData() {
    setLoading(true);
    try {
      const [sumRes, catRes] = await Promise.all([
        api.getSummary(period),
        api.getCategoryBreakdown(period, "expense"),
      ]);
      setSummary(sumRes);
      setCategories(catRes.categories || []);

      // Grafik faqat oylik ko'rinishda
      if (period === "month") {
        const now = new Date();
        const chartRes = await api.getDailyChart(now.getFullYear(), now.getMonth() + 1);
        setChartData(chartRes.days || []);
      } else {
        setChartData([]);
      }
    } catch (err) {
      console.error("Dashboard yuklash xatoligi:", err);
    } finally {
      setLoading(false);
    }
  }

  if (loading && !summary) {
    return (
      <div className="loading">
        <div className="spinner" />
        <p>Yuklanmoqda...</p>
      </div>
    );
  }

  const currency = summary?.currency || "UZS";

  return (
    <div>
      {/* Davr tanlash */}
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

      {/* Balans karta */}
      {summary && (
        <div className="balance-card">
          <div className="label">Balans</div>
          <div className="amount">
            {summary.balance >= 0 ? "+" : ""}
            {formatAmount(summary.balance, currency)}
          </div>
          <div className="sub-row">
            <div className="sub-item">
              <div className="sub-label">Kirim</div>
              <div className="sub-amount income">
                +{formatAmount(summary.total_income, currency)}
              </div>
            </div>
            <div className="sub-item">
              <div className="sub-label">Chiqim</div>
              <div className="sub-amount expense">
                -{formatAmount(summary.total_expense, currency)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Kunlik grafik */}
      {chartData.length > 0 && (
        <div className="card">
          <div className="card-title">Kunlik grafik</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={chartData} barGap={2}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis
                  dataKey="day"
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis hide />
                <Tooltip
                  formatter={(value) => formatAmount(value, currency)}
                  labelFormatter={(day) => `${day}-kun`}
                />
                <Bar dataKey="income" fill="#34c759" radius={[3, 3, 0, 0]} name="Kirim" />
                <Bar dataKey="expense" fill="#ff3b30" radius={[3, 3, 0, 0]} name="Chiqim" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Kategoriya taqsimoti */}
      {categories.length > 0 && (
        <div className="card">
          <div className="card-title">Xarajatlar taqsimoti</div>
          {categories.slice(0, 5).map((cat, i) => (
            <div key={i} className="cat-item">
              <span className="cat-icon">{cat.icon}</span>
              <div className="cat-info">
                <div className="cat-name">{cat.name}</div>
                <div className="cat-bar">
                  <div
                    className="cat-bar-fill"
                    style={{ width: `${cat.percent}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="cat-amount">{formatAmount(cat.total, currency)}</div>
                <div className="cat-percent">{cat.percent}%</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* So'nggi tranzaksiyalar ga havola */}
      <div className="section-header">
        <span className="section-title">So'nggi yozuvlar</span>
        <Link to="/transactions" className="section-link">
          Barchasi
        </Link>
      </div>
    </div>
  );
}
