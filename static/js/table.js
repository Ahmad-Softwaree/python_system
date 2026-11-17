/**
 * Create / Edit modal for table pages.
 *
 * Odd detail — update URL:
 * The template injects TABLE_UPDATE_URL with row_id=0 as a placeholder
 * (e.g. /table/drivers/0/update). When editing, we replace "/0/" with the real id.
 * That avoids generating a separate update URL for every row in HTML.
 */
(function () {
  const modal = document.getElementById("record-modal");
  const form = document.getElementById("record-form");
  const title = document.getElementById("modal-title");
  const addBtn = document.getElementById("btn-add");
  if (!modal || !form) return;

  function openModal() {
    modal.classList.remove("hidden");
    // Re-draw Lucide icons that were inside the previously-hidden modal.
    if (window.lucide) lucide.createIcons();
  }

  function closeModal() {
    modal.classList.add("hidden");
  }

  function resetForm() {
    form.reset();
    form.action = window.TABLE_CREATE_URL;
    title.textContent = "Add record";
  }

  function fillForm(row) {
    (window.TABLE_FIELDS || []).forEach((field) => {
      const input = document.getElementById("field-" + field.name);
      if (!input) return;
      const value = row[field.name];
      if (field.type === "bool") {
        input.checked = Boolean(value);
      } else {
        input.value = value == null ? "" : value;
      }
    });
  }

  addBtn?.addEventListener("click", () => {
    resetForm();
    openModal();
  });

  document.querySelectorAll("[data-close-modal]").forEach((el) => {
    el.addEventListener("click", closeModal);
  });

  document.querySelectorAll(".btn-edit").forEach((btn) => {
    btn.addEventListener("click", () => {
      // Row data was embedded as JSON on the button (data-row="...").
      const row = JSON.parse(btn.getAttribute("data-row"));
      resetForm();
      title.textContent = "Edit record #" + row.id;
      form.action = window.TABLE_UPDATE_URL.replace("/0/", "/" + row.id + "/");
      fillForm(row);
      openModal();
    });
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });
})();
