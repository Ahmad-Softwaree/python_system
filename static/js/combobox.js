/**
 * Searchable relation combobox.
 * Type to filter /api/options/<source>?q=... then click a result to set the hidden id.
 */
(function () {
  function debounce(fn, ms) {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  }

  async function fetchOptions(source, q) {
    const url = "/api/options/" + source + "?q=" + encodeURIComponent(q || "");
    const res = await fetch(url);
    if (!res.ok) return [];
    return res.json();
  }

  function wireCombobox(root) {
    const source = root.dataset.source;
    const hidden = root.querySelector('input[type="hidden"]');
    const input = root.querySelector(".combobox-input");
    const menu = root.querySelector(".combobox-menu");
    if (!hidden || !input || !menu) return;

    function hideMenu() {
      menu.classList.add("hidden");
      menu.innerHTML = "";
    }

    function showOptions(rows) {
      menu.innerHTML = "";
      if (!rows.length) {
        menu.innerHTML = '<div class="px-3 py-2 text-xs text-slate-400">No matches</div>';
        menu.classList.remove("hidden");
        return;
      }
      rows.forEach((row) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "w-full text-left px-3 py-2 text-sm hover:bg-brand-soft";
        btn.textContent = row.label + " (#" + row.id + ")";
        btn.addEventListener("mousedown", (e) => {
          e.preventDefault();
          hidden.value = row.id;
          input.value = row.label;
          hideMenu();
        });
        menu.appendChild(btn);
      });
      menu.classList.remove("hidden");
    }

    const runSearch = debounce(async () => {
      // Typing clears the selected id until the user picks again.
      hidden.value = "";
      const rows = await fetchOptions(source, input.value.trim());
      showOptions(rows);
    }, 250);

    input.addEventListener("focus", async () => {
      const rows = await fetchOptions(source, input.value.trim());
      showOptions(rows);
    });
    input.addEventListener("input", runSearch);
    input.addEventListener("blur", () => setTimeout(hideMenu, 150));

    // Public helper used when editing a row: set id + label.
    root.setValue = async (id, labelHint) => {
      hidden.value = id || "";
      if (!id) {
        input.value = "";
        return;
      }
      if (labelHint) {
        input.value = labelHint;
        return;
      }
      const rows = await fetchOptions(source, "");
      const match = rows.find((r) => String(r.id) === String(id));
      input.value = match ? match.label : "#" + id;
    };
  }

  function initAll(scope) {
    (scope || document).querySelectorAll(".combobox").forEach(wireCombobox);
  }

  window.PostalCombobox = { initAll, wireCombobox };
  initAll();
})();
