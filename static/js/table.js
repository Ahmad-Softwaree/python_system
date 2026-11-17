/**
 * Create / Edit modal + order multi-item lines.
 */
(function () {
  const modal = document.getElementById("record-modal");
  const form = document.getElementById("record-form");
  const title = document.getElementById("modal-title");
  const addBtn = document.getElementById("btn-add");
  if (!modal || !form) return;

  function openModal() {
    modal.classList.remove("hidden");
    if (window.lucide) lucide.createIcons();
  }

  function closeModal() {
    modal.classList.add("hidden");
  }

  function setFieldValue(field, value) {
    const input = document.getElementById("field-" + field.name);
    if (!input) return;
    if (field.type === "bool") {
      input.checked = Boolean(value);
    } else if (field.type === "relation") {
      const box = input.closest(".combobox");
      if (box && box.setValue) box.setValue(value);
      else input.value = value == null ? "" : value;
    } else {
      input.value = value == null ? "" : value;
    }
  }

  function clearOrderLines() {
    const wrap = document.getElementById("order-lines");
    if (wrap) wrap.innerHTML = "";
  }

  function addOrderLine(itemId, qty, label) {
    const wrap = document.getElementById("order-lines");
    if (!wrap) return;
    const row = document.createElement("div");
    row.className = "flex gap-2 items-start order-line";
    row.innerHTML = `
      <div class="combobox relative flex-1" data-source="items" data-name="item_id">
        <input type="hidden" name="item_id[]" ${itemId ? 'value="' + itemId + '"' : ""} required />
        <input type="text" class="combobox-input w-full px-3 py-2 rounded-lg border border-slate-300 text-sm"
               placeholder="Search item..." autocomplete="off" value="${label ? String(label).replace(/"/g, "&quot;") : ""}" />
        <div class="combobox-menu hidden absolute z-10 left-0 right-0 mt-1 max-h-40 overflow-auto bg-white border border-slate-200 rounded-lg shadow-lg"></div>
      </div>
      <input type="number" name="quantity[]" min="1" value="${qty || 1}" required
             class="w-24 px-3 py-2 rounded-lg border border-slate-300 text-sm" placeholder="Qty" />
      <button type="button" class="p-2 text-red-600 hover:bg-red-50 rounded-lg remove-line" title="Remove">
        <i data-lucide="trash-2" class="w-4 h-4"></i>
      </button>
    `;
    wrap.appendChild(row);
    const box = row.querySelector(".combobox");
    if (window.PostalCombobox) PostalCombobox.wireCombobox(box);
    row.querySelector(".remove-line").addEventListener("click", () => row.remove());
    if (window.lucide) lucide.createIcons({ nodes: [row] });
  }

  function resetForm() {
    form.reset();
    form.action = window.TABLE_CREATE_URL;
    title.textContent = "Add record";
    // Clear relation hidden values / labels
    form.querySelectorAll(".combobox").forEach((box) => {
      if (box.setValue) box.setValue("");
    });
    clearOrderLines();
    if (window.TABLE_SPECIAL === "orders") addOrderLine();
  }

  function fillForm(row) {
    (window.TABLE_FIELDS || []).forEach((field) => {
      setFieldValue(field, row[field.name]);
    });
    if (window.TABLE_SPECIAL === "orders") {
      clearOrderLines();
      const lines = row.order_items || [];
      if (!lines.length) addOrderLine();
      else {
        lines.forEach((line) => addOrderLine(line.item_id, line.quantity));
        // Resolve labels asynchronously
        lines.forEach((line, idx) => {
          const box = document.querySelectorAll("#order-lines .combobox")[idx];
          if (box && box.setValue) box.setValue(line.item_id);
        });
      }
    }
  }

  addBtn?.addEventListener("click", () => {
    resetForm();
    openModal();
  });

  document.getElementById("add-order-line")?.addEventListener("click", () => addOrderLine());

  document.querySelectorAll("[data-close-modal]").forEach((el) => {
    el.addEventListener("click", closeModal);
  });

  document.querySelectorAll(".btn-edit").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
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
