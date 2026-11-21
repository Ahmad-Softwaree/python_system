/**
 * Educational source peek — open a modal with Python/JS file path + code.
 * Buttons: .source-peek-btn[data-source-key="report.orders"]
 */
(function () {
  if (!window.SHOW_SOURCE) return;

  const modal = document.getElementById("source-peek-modal");
  const titleEl = document.getElementById("source-peek-title");
  const bodyEl = document.getElementById("source-peek-body");
  const i18n = window.SOURCE_I18N || {};

  if (!modal || !titleEl || !bodyEl) return;

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function linesLabel(start, end) {
    const tpl = i18n.lines || "Lines {start}–{end}";
    return tpl.replace("{start}", start).replace("{end}", end);
  }

  function openModal() {
    modal.hidden = false;
    modal.classList.add("open");
    document.body.style.overflow = "hidden";
    if (window.lucide) lucide.createIcons();
  }

  function closeModal() {
    modal.classList.remove("open");
    modal.hidden = true;
    document.body.style.overflow = "";
  }

  function renderParts(data) {
    titleEl.textContent = data.title || data.key || "Source";
    if (!data.parts || !data.parts.length) {
      bodyEl.innerHTML = `<p class="text-brand-muted dark:text-slate-400">${escapeHtml(i18n.error || "No source")}</p>`;
      return;
    }
    bodyEl.innerHTML = data.parts
      .map((part) => {
        const note = part.note ? `<p class="text-xs text-brand-muted dark:text-slate-400 mb-2">${escapeHtml(part.note)}</p>` : "";
        return `
        <section class="rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden">
          <div class="px-3 py-2 bg-slate-50 dark:bg-slate-950/60 border-b border-slate-200 dark:border-slate-700 flex flex-wrap items-center gap-2 justify-between">
            <code class="source-peek-path text-brand dark:text-teal-300 font-semibold">${escapeHtml(part.path)}</code>
            <span class="text-[11px] text-brand-muted dark:text-slate-400">${escapeHtml(linesLabel(part.start_line, part.end_line))}</span>
          </div>
          <div class="p-3">
            ${note}
            <pre class="source-peek-code"><code>${escapeHtml(part.code || "")}</code></pre>
          </div>
        </section>`;
      })
      .join("");
  }

  async function loadSource(key) {
    titleEl.textContent = key;
    bodyEl.innerHTML = `<p class="text-brand-muted dark:text-slate-400">${escapeHtml(i18n.loading || "Loading…")}</p>`;
    openModal();
    try {
      const res = await fetch("/api/source/" + encodeURIComponent(key));
      if (!res.ok) throw new Error("not found");
      const data = await res.json();
      renderParts(data);
    } catch (err) {
      bodyEl.innerHTML = `<p class="text-red-600 dark:text-red-300">${escapeHtml(i18n.error || "Error")}</p>`;
    }
  }

  /** Create a </> button element for a source key */
  function makeButton(key, extraClass) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "source-peek-btn" + (extraClass ? " " + extraClass : "");
    btn.dataset.sourceKey = key;
    btn.title = i18n.peek || "View source code";
    btn.setAttribute("aria-label", i18n.peek || "View source code");
    btn.innerHTML = '<span aria-hidden="true">&lt;/&gt;</span>';
    return btn;
  }

  // Delegate clicks from any peek button (static or JS-created)
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".source-peek-btn, [data-source-key]");
    if (btn && btn.classList.contains("source-peek-btn") && btn.dataset.sourceKey) {
      e.preventDefault();
      e.stopPropagation();
      loadSource(btn.dataset.sourceKey);
      return;
    }
    if (e.target.closest("[data-source-close]")) {
      closeModal();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal.classList.contains("open")) closeModal();
  });

  window.SourcePeek = {
    open: loadSource,
    makeButton,
    close: closeModal,
  };
})();
