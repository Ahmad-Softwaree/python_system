/**
 * Custom confirm modal for Delete / Restore (replaces window.alert / confirm).
 */
(function () {
  const modal = document.getElementById("confirm-modal");
  const form = document.getElementById("confirm-form");
  const title = document.getElementById("confirm-title");
  const message = document.getElementById("confirm-message");
  const submit = document.getElementById("confirm-submit");
  if (!modal || !form) return;

  function openConfirm(action, opts) {
    form.action = action;
    title.textContent = opts.title || "Confirm";
    message.textContent = opts.message || "Are you sure?";
    submit.textContent = opts.confirmLabel || "Confirm";
    modal.classList.remove("hidden");
    if (window.lucide) lucide.createIcons();
  }

  function closeConfirm() {
    modal.classList.add("hidden");
  }

  document.querySelectorAll(".btn-confirm").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      openConfirm(btn.dataset.action, {
        title: btn.dataset.title,
        message: btn.dataset.message,
        confirmLabel: btn.dataset.confirmLabel,
      });
    });
  });

  document.querySelectorAll("[data-close-confirm]").forEach((el) => {
    el.addEventListener("click", closeConfirm);
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeConfirm();
  });
})();
