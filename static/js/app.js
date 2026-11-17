/**
 * Collapsible sidebar.
 * Stores open/closed state in localStorage so a page refresh keeps the choice.
 */
(function () {
  const sidebar = document.getElementById("sidebar");
  const toggle = document.getElementById("sidebar-toggle");
  if (!sidebar || !toggle) return;

  const KEY = "postal-sidebar-collapsed";

  function apply(collapsed) {
    // Tailwind width classes: full label sidebar vs icon-only rail.
    sidebar.classList.toggle("w-60", !collapsed);
    sidebar.classList.toggle("w-16", collapsed);
    document.querySelectorAll(".sidebar-label").forEach((el) => {
      el.classList.toggle("hidden", collapsed);
    });
    const openIcon = toggle.querySelector(".sidebar-open-icon");
    const closedIcon = toggle.querySelector(".sidebar-closed-icon");
    if (openIcon && closedIcon) {
      openIcon.classList.toggle("hidden", collapsed);
      closedIcon.classList.toggle("hidden", !collapsed);
    }
  }

  apply(localStorage.getItem(KEY) === "1");

  toggle.addEventListener("click", () => {
    const next = !sidebar.classList.contains("w-16");
    localStorage.setItem(KEY, next ? "1" : "0");
    apply(next);
  });
})();
