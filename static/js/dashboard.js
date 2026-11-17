/**
 * Dashboard: show ONE chart at a time.
 * Clicking a button fetches /api/chart/<id> and swaps the preview panel.
 */
(function () {
  const buttons = document.querySelectorAll("[data-chart-id]");
  const titleEl = document.getElementById("chart-title");
  const lectureEl = document.getElementById("chart-lecture");
  const imageEl = document.getElementById("chart-image");
  const loadingEl = document.getElementById("chart-loading");
  const emptyEl = document.getElementById("chart-empty");
  if (!buttons.length || !imageEl) return;

  const cache = {};

  function setActiveButton(id) {
    buttons.forEach((btn) => {
      const active = Number(btn.dataset.chartId) === id;
      btn.classList.toggle("bg-brand", active);
      btn.classList.toggle("text-white", active);
      btn.classList.toggle("bg-white", !active);
      btn.classList.toggle("text-brand-dark", !active);
    });
  }

  function showLoading(on) {
    loadingEl.classList.toggle("hidden", !on);
    if (on) {
      imageEl.classList.add("hidden");
      emptyEl.classList.add("hidden");
    }
  }

  async function loadChart(id) {
    setActiveButton(id);
    showLoading(true);

    try {
      let chart = cache[id];
      if (!chart) {
        const res = await fetch("/api/chart/" + id);
        if (!res.ok) throw new Error("Failed to load chart");
        chart = await res.json();
        cache[id] = chart;
      }

      titleEl.textContent = chart.title;
      lectureEl.textContent = chart.lecture;
      imageEl.src = "data:image/png;base64," + chart.image;
      imageEl.alt = chart.title;
      imageEl.classList.remove("hidden");
      emptyEl.classList.add("hidden");
    } catch (err) {
      titleEl.textContent = "Could not load chart";
      lectureEl.textContent = String(err.message || err);
      imageEl.classList.add("hidden");
      emptyEl.classList.remove("hidden");
    } finally {
      showLoading(false);
    }
  }

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => loadChart(Number(btn.dataset.chartId)));
  });

  // Auto-load the first chart so the panel is not empty on open.
  loadChart(Number(buttons[0].dataset.chartId));
})();
