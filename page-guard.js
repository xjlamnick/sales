// page-guard.js — підключи до КОЖНОЇ захищеної сторінки
// Додай у <head> ПІСЛЯ auth.js:
//   <script src="auth.js"></script>
//   <script src="page-guard.js"></script>

(function() {
  if (!AUTH.guardPage()) {
    // guardPage() сам зробить редирект — просто зупиняємо завантаження
    document.documentElement.style.visibility = 'hidden';
  }
})();
