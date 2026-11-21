/**
 * Dashboard reports:
 * - Few report buttons (Orders / Revenue / Delivery / Inventory)
 * - Shared filters (province, city, merchant, driver, post, status, dates, presets)
 * - Loads multiple charts per report from /api/report/<key>
 */
(function () {
  const reportButtons = document.querySelectorAll(".report-btn");
  const presetButtons = document.querySelectorAll(".preset-btn");
  const titleEl = document.getElementById("report-title");
  const descEl = document.getElementById("report-description");
  const summaryEl = document.getElementById("report-summary");
  const chartsEl = document.getElementById("report-charts");
  const loadingEl = document.getElementById("report-loading");
  const emptyEl = document.getElementById("report-empty");
  const applyBtn = document.getElementById("filter-apply");
  const resetBtn = document.getElementById("filter-reset");

  const provinceSel = document.getElementById("filter-province");
  const citySel = document.getElementById("filter-city");
  const merchantSel = document.getElementById("filter-merchant");
  const driverSel = document.getElementById("filter-driver");
  const postSel = document.getElementById("filter-post");
  const statusSel = document.getElementById("filter-status");
  const dateFrom = document.getElementById("filter-date-from");
  const dateTo = document.getElementById("filter-date-to");

  if (!reportButtons.length || !chartsEl) return;

  let activeReport = "orders";
  let activePreset = "";

  function setActiveReport(key) {
    activeReport = key;
    reportButtons.forEach((btn) => {
      const on = btn.dataset.report === key;
      btn.classList.toggle("bg-brand", on);
      btn.classList.toggle("text-white", on);
      btn.classList.toggle("shadow-md", on);
    });
  }

  function setActivePreset(preset) {
    activePreset = preset || "";
    presetButtons.forEach((btn) => {
      const on = btn.dataset.preset === activePreset;
      btn.classList.toggle("bg-brand", on);
      btn.classList.toggle("text-white", on);
      btn.classList.toggle("shadow-sm", on);
    });
    // Preset overrides custom date inputs visually
    if (activePreset) {
      dateFrom.value = "";
      dateTo.value = "";
    }
  }

  function filterCitiesByProvince() {
    const provinceId = provinceSel.value;
    const currentCity = citySel.value;
    const cities = window.DASHBOARD_CITIES || [];
    citySel.innerHTML = '<option value="">All cities</option>';
    cities
      .filter((c) => !provinceId || String(c.province_id) === String(provinceId))
      .forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.textContent = c.name;
        opt.dataset.province = c.province_id;
        citySel.appendChild(opt);
      });
    // Keep selection if still valid
    if ([...citySel.options].some((o) => o.value === currentCity)) {
      citySel.value = currentCity;
    }
  }

  function collectFilters() {
    const params = new URLSearchParams();
    if (provinceSel.value) params.set("province_id", provinceSel.value);
    if (citySel.value) params.set("city_id", citySel.value);
    if (merchantSel.value) params.set("merchant_id", merchantSel.value);
    if (driverSel.value) params.set("driver_id", driverSel.value);
    if (postSel.value) params.set("post_id", postSel.value);
    if (statusSel.value) params.set("status", statusSel.value);
    if (activePreset) params.set("preset", activePreset);
    if (!activePreset && dateFrom.value) params.set("date_from", dateFrom.value);
    if (!activePreset && dateTo.value) params.set("date_to", dateTo.value);
    return params;
  }

  function renderSummary(summary) {
    if (!summary) {
      summaryEl.classList.add("hidden");
      summaryEl.innerHTML = "";
      return;
    }
    // Prefer explicit cards (e.g. Ratings report); else classic order KPIs.
    const cards = Array.isArray(summary.cards)
      ? summary.cards.map((c) => [c.label, c.value])
      : [
          ["Orders", summary.orders],
          ["Delivered", summary.delivered],
          ["Cancelled", summary.cancelled],
          ["Revenue", summary.revenue],
          ["Avg days", summary.avg_delivery_days],
        ];
    const tones = ["teal", "amber", "sky", "orange", "emerald", "cyan"];
    summaryEl.innerHTML = cards
      .map(([label, value], i) => {
        const tone = tones[i % tones.length];
        return `
      <div class="summary-chip tone-${tone}" style="animation-delay:${i * 40}ms">
        <div class="relative text-lg font-bold">${value}</div>
        <div class="relative text-[11px] mt-0.5 opacity-75">${label}</div>
      </div>`;
      })
      .join("");
    summaryEl.classList.remove("hidden");
  }

  function renderCharts(charts) {
    chartsEl.innerHTML = "";
    if (!charts || !charts.length) {
      emptyEl.classList.remove("hidden");
      return;
    }
    emptyEl.classList.add("hidden");
    charts.forEach((chart, i) => {
      const card = document.createElement("article");
      card.className = "chart-card";
      card.style.animationDelay = `${i * 50}ms`;
      const sourceKey = chart.source_key || "";
      const peekBtn =
        window.SHOW_SOURCE && sourceKey && window.SourcePeek
          ? window.SourcePeek.makeButton(sourceKey).outerHTML
          : window.SHOW_SOURCE && sourceKey
            ? `<button type="button" class="source-peek-btn" data-source-key="${sourceKey}" title="View source">&lt;/&gt;</button>`
            : "";
      card.innerHTML = `
        <div class="relative flex items-start justify-between gap-2 mb-1">
          <h4 class="font-semibold text-brand-dark dark:text-slate-100">${chart.title}</h4>
          <div class="shrink-0 flex items-center gap-1.5">
            ${peekBtn}
            <span class="w-8 h-8 rounded-full bg-teal-50 dark:bg-teal-950 text-brand dark:text-teal-300 grid place-items-center text-xs font-bold">${i + 1}</span>
          </div>
        </div>
        <p class="relative text-xs text-brand-muted dark:text-slate-400 mb-3">${chart.lecture || ""}</p>
        <img src="data:image/png;base64,${chart.image}" alt="${chart.title}" class="relative w-full rounded-xl bg-white dark:bg-slate-950 border border-slate-100 dark:border-slate-800" />
      `;
      chartsEl.appendChild(card);
    });
  }

  async function loadReport(key) {
    setActiveReport(key);
    loadingEl.classList.remove("hidden");
    emptyEl.classList.add("hidden");
    chartsEl.innerHTML = "";
    summaryEl.classList.add("hidden");

    try {
      const params = collectFilters();
      const res = await fetch("/api/report/" + key + "?" + params.toString());
      if (!res.ok) throw new Error("Failed to load report");
      const report = await res.json();
      titleEl.textContent = report.title;
      descEl.textContent = report.description || "";
      // Optional </> next to report title (active report builder)
      if (window.SHOW_SOURCE && report.source_key) {
        let wrap = document.getElementById("report-title-peek");
        if (!wrap) {
          wrap = document.createElement("span");
          wrap.id = "report-title-peek";
          wrap.className = "inline-flex ms-2 align-middle";
          titleEl.appendChild(wrap);
        }
        wrap.innerHTML = "";
        const btn =
          window.SourcePeek && window.SourcePeek.makeButton
            ? window.SourcePeek.makeButton(report.source_key)
            : null;
        if (btn) wrap.appendChild(btn);
        else {
          wrap.innerHTML = `<button type="button" class="source-peek-btn" data-source-key="${report.source_key}">&lt;/&gt;</button>`;
        }
      }
      renderSummary(report.summary);
      renderCharts(report.charts || []);
    } catch (err) {
      titleEl.textContent = "Could not load report";
      descEl.textContent = String(err.message || err);
      emptyEl.classList.remove("hidden");
    } finally {
      loadingEl.classList.add("hidden");
    }
  }

  reportButtons.forEach((btn) => {
    btn.addEventListener("click", () => loadReport(btn.dataset.report));
  });

  presetButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const next = btn.dataset.preset === activePreset ? "" : btn.dataset.preset;
      setActivePreset(next);
      loadReport(activeReport);
    });
  });

  provinceSel?.addEventListener("change", filterCitiesByProvince);
  applyBtn?.addEventListener("click", () => {
    // Manual dates clear preset
    if (dateFrom.value || dateTo.value) setActivePreset("");
    loadReport(activeReport);
  });
  resetBtn?.addEventListener("click", () => {
    provinceSel.value = "";
    filterCitiesByProvince();
    citySel.value = "";
    merchantSel.value = "";
    driverSel.value = "";
    postSel.value = "";
    statusSel.value = "";
    dateFrom.value = "";
    dateTo.value = "";
    setActivePreset("");
    loadReport(activeReport);
  });

  // Changing a date manually drops the preset highlight
  [dateFrom, dateTo].forEach((el) => {
    el?.addEventListener("change", () => setActivePreset(""));
  });

  filterCitiesByProvince();
  loadReport("orders");
})();
