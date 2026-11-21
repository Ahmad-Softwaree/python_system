/**
 * Sidebar collapse (desktop) + mobile drawer + theme localStorage sync.
 */
(function () {
  const sidebar = document.getElementById("sidebar");
  const toggle = document.getElementById("sidebar-toggle");
  const openMobile = document.getElementById("sidebar-open-mobile");
  const closeMobile = document.getElementById("sidebar-close-mobile");
  const backdrop = document.getElementById("sidebar-backdrop");
  if (!sidebar) return;

  const KEY = "postal-sidebar-collapsed";

  function isDesktop() {
    return window.matchMedia("(min-width: 768px)").matches;
  }

  function isCollapsed() {
    return sidebar.getAttribute("data-collapsed") === "1";
  }

  function setIcon(collapsed) {
    if (!toggle) return;
    toggle.innerHTML = "";
    const icon = document.createElement("i");
    icon.setAttribute("data-lucide", collapsed ? "panel-left-open" : "panel-left-close");
    icon.className = "w-4 h-4";
    toggle.appendChild(icon);
    if (window.lucide) lucide.createIcons({ nodes: [toggle] });
  }

  function applyDesktop(collapsed) {
    if (!isDesktop()) return;
    sidebar.setAttribute("data-collapsed", collapsed ? "1" : "0");
    sidebar.classList.toggle("w-60", !collapsed);
    sidebar.classList.toggle("w-16", collapsed);
    document.querySelectorAll(".sidebar-label").forEach((el) => {
      el.classList.toggle("hidden", collapsed);
    });
    const brand = sidebar.querySelector(".sidebar-brand");
    if (brand) brand.classList.toggle("hidden", collapsed);
    const prefs = sidebar.querySelector(".sidebar-prefs");
    if (prefs && collapsed) {
      // Keep compact icon-ish prefs readable: hide text labels only (already .sidebar-label)
    }
    setIcon(collapsed);
    if (toggle) toggle.title = collapsed ? "Expand sidebar" : "Collapse sidebar";
  }

  function openDrawer() {
    sidebar.classList.add("mobile-open");
    if (backdrop) backdrop.classList.add("show");
    document.body.style.overflow = "hidden";
  }

  function closeDrawer() {
    sidebar.classList.remove("mobile-open");
    if (backdrop) backdrop.classList.remove("show");
    document.body.style.overflow = "";
  }

  // Desktop collapse restore
  applyDesktop(localStorage.getItem(KEY) === "1");

  if (toggle) {
    toggle.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const next = !isCollapsed();
      localStorage.setItem(KEY, next ? "1" : "0");
      applyDesktop(next);
    });
  }

  if (openMobile) openMobile.addEventListener("click", openDrawer);
  if (closeMobile) closeMobile.addEventListener("click", closeDrawer);
  if (backdrop) backdrop.addEventListener("click", closeDrawer);

  window.addEventListener("resize", () => {
    if (isDesktop()) {
      closeDrawer();
      applyDesktop(localStorage.getItem(KEY) === "1");
    } else {
      sidebar.classList.add("w-60");
      sidebar.classList.remove("w-16");
      document.querySelectorAll(".sidebar-label").forEach((el) => el.classList.remove("hidden"));
      const brand = sidebar.querySelector(".sidebar-brand");
      if (brand) brand.classList.remove("hidden");
    }
  });

  // Sync theme cookie → localStorage for the early FOUC script
  try {
    const m = document.cookie.match(/(?:^|; )postal_theme=([^;]*)/);
    if (m) localStorage.setItem("postal-theme", decodeURIComponent(m[1]));
  } catch (e) {}
})();

/**
 * If any fetch gets 401 (expired/missing JWT), send the browser to /login.
 */
(function () {
  const originalFetch = window.fetch.bind(window);
  window.fetch = async function (input, init) {
    const res = await originalFetch(input, init);
    if (res.status === 401) {
      const path = window.location.pathname + window.location.search;
      if (!path.startsWith("/login")) {
        window.location.href = "/login?next=" + encodeURIComponent(path);
      }
    }
    return res;
  };
})();
