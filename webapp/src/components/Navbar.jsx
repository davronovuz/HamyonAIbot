import { NavLink } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="navbar">
      <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`} end>
        <span className="nav-icon">📊</span>
        Dashboard
      </NavLink>
      <NavLink to="/transactions" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
        <span className="nav-icon">📋</span>
        Tarix
      </NavLink>
      <NavLink to="/debts" className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}>
        <span className="nav-icon">💳</span>
        Qarzlar
      </NavLink>
    </nav>
  );
}
