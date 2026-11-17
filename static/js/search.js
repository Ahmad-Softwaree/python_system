/**
 * Live search with 1s debounce.
 * Keeps focus on the search input after the page reloads with results
 * (sessionStorage flag), until the user leaves the field themselves.
 */
(function () {
  const input = document.getElementById("live-search");
  if (!input) return;

  const DELAY_MS = 1000;
  const FOCUS_KEY = "postal-search-keep-focus";
  const VALUE_KEY = "postal-search-value";
  let timer = null;
  let keepFocus = false;

  // Restore focus after reload triggered by search.
  if (sessionStorage.getItem(FOCUS_KEY) === "1") {
    keepFocus = true;
    const saved = sessionStorage.getItem(VALUE_KEY);
    if (saved != null && input.value === "") input.value = saved;
    // Defer focus until after layout / lucide icons.
    setTimeout(() => {
      input.focus();
      const len = input.value.length;
      try { input.setSelectionRange(len, len); } catch (_) {}
    }, 0);
  }

  // If the user blurs the field on purpose, stop auto-refocusing.
  input.addEventListener("blur", () => {
    keepFocus = false;
    sessionStorage.removeItem(FOCUS_KEY);
    sessionStorage.removeItem(VALUE_KEY);
  });

  // If we still want focus (e.g. something stole it), reclaim it.
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && keepFocus) input.focus();
  });

  function currentParams() {
    return new URLSearchParams(window.location.search);
  }

  function goSearch(value) {
    const params = currentParams();
    const q = value.trim();
    if (q) params.set("q", q);
    else params.delete("q");
    params.set("page", "1");

    sessionStorage.setItem(FOCUS_KEY, "1");
    sessionStorage.setItem(VALUE_KEY, value);

    const qs = params.toString();
    window.location.href = window.location.pathname + (qs ? "?" + qs : "");
  }

  input.addEventListener("input", () => {
    clearTimeout(timer);
    const value = input.value;
    timer = setTimeout(() => {
      const currentQ = (currentParams().get("q") || "").trim();
      if (value.trim() === currentQ) return;
      goSearch(value);
    }, DELAY_MS);
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      clearTimeout(timer);
      goSearch(input.value);
    }
  });
})();
