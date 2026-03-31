// ============================================================
//  auth.js  —  GORODOK Dashboard · Role-based auth
//  Ролі: admin (повний доступ) | viewer (без захищених сторінок)
//  Захищені сторінки: dynamics.html, competitor-delta.html, daily-delta.html
// ============================================================

const AUTH = {
  // --- Паролі (змінюй тут) ---
  passwords: {
    admin:  "gteam-admin",   // пароль для адміна
    viewer: "gteam"          // пароль для viewer (старий пароль — тепер viewer)
  },

  // --- Захищені сторінки (тільки admin) ---
  adminOnly: [
    "dynamics.html",
    "competitor-delta.html",
    "daily-delta.html"
  ],

  EXPIRY_DAYS: 30,

  // --- Зберегти сесію ---
  save(role) {
    localStorage.setItem("auth_role",    role);
    localStorage.setItem("auth_date",    Date.now());
    localStorage.setItem("isAuthorized", "true");
  },

  // --- Очистити сесію ---
  clear() {
    localStorage.removeItem("auth_role");
    localStorage.removeItem("auth_date");
    localStorage.removeItem("isAuthorized");
  },

  // --- Перевірити чи сесія ще діє ---
  isValid() {
    const saved = localStorage.getItem("isAuthorized");
    const date  = parseInt(localStorage.getItem("auth_date") || "0");
    if (saved !== "true") return false;
    const expired = (Date.now() - date) > this.EXPIRY_DAYS * 864e5;
    if (expired) { this.clear(); return false; }
    return true;
  },

  // --- Поточна роль ---
  getRole() {
    return localStorage.getItem("auth_role") || null;
  },

  // --- Перевірити пароль і повернути роль (або null) ---
  checkPassword(input) {
    if (input === this.passwords.admin)  return "admin";
    if (input === this.passwords.viewer) return "viewer";
    return null;
  },

  // --- Чи має поточний юзер доступ до сторінки ---
  canAccess(filename) {
    if (!this.isValid()) return false;
    if (this.adminOnly.includes(filename) && this.getRole() !== "admin") return false;
    return true;
  },

  // --- Ім'я поточної html-сторінки ---
  currentPage() {
    return window.location.pathname.split("/").pop() || "index.html";
  },

  // --- Викликати на захищених сторінках ---
  guardPage() {
    if (!this.isValid()) {
      window.location.href = "index.html";
      return false;
    }
    const page = this.currentPage();
    if (this.adminOnly.includes(page) && this.getRole() !== "admin") {
      window.location.href = "index.html?access=denied";
      return false;
    }
    return true;
  }
};
