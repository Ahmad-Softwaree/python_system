/**
 * Collapsible sidebar.
 *
 * Bug fix: previously we toggled two icon elements and inferred state from
 * the `w-16` class. Lucide replaces <i> with <svg>, and overflow:hidden could
 * clip the expand button — so collapse could not be undone.
 *
 * Now we:
 * - store state in data-collapsed + localStorage
 * - keep one toggle button always visible
 * - swap the Lucide icon name when expanding/collapsing
 */
(function () {
  const sidebar = document.getElementById("sidebar");
  const toggle = document.getElementById("sidebar-toggle");
  if (!sidebar || !toggle) return;

  const KEY = "postal-sidebar-collapsed";

  function isCollapsed() {
    return sidebar.getAttribute("data-collapsed") === "1";
  }

  function setIcon(collapsed) {
    // Remove any previous svg Lucide injected, then put a fresh <i> back.
    toggle.innerHTML = "";
    const icon = document.createElement("i");
    icon.setAttribute("data-lucide", collapsed ? "panel-left-open" : "panel-left-close");
    icon.className = "w-4 h-4";
    toggle.appendChild(icon);
    if (window.lucide) lucide.createIcons({ nodes: [toggle] });
  }

  function apply(collapsed) {
    sidebar.setAttribute("data-collapsed", collapsed ? "1" : "0");
    sidebar.classList.toggle("w-60", !collapsed);
    sidebar.classList.toggle("w-16", collapsed);

    document.querySelectorAll(".sidebar-label").forEach((el) => {
      el.classList.toggle("hidden", collapsed);
    });

    // When collapsed, hide the brand tile so the toggle button has room.
    const brand = sidebar.querySelector(".sidebar-brand");
    if (brand) brand.classList.toggle("hidden", collapsed);

    setIcon(collapsed);
    toggle.title = collapsed ? "Expand sidebar" : "Collapse sidebar";
  }

  apply(localStorage.getItem(KEY) === "1");

  toggle.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    const next = !isCollapsed();
    localStorage.setItem(KEY, next ? "1" : "0");
    apply(next);
  });
})();
