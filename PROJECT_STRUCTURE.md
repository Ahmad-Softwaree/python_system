# Project Structure Explained

This document explains **every folder and file** in the Postal System project: what it is for, and how it fits into the big picture. Use it when presenting to your teacher.

**Current stack:** Flask · Flask-SQLAlchemy (ORM) · MySQL · Matplotlib/Seaborn · custom i18n (EN/AR/CKB) · Tailwind CSS (CDN) · Lucide icons

**Default local URL:** http://localhost:3000  
**Default DB name (from `.env`):** `python_postal`

---

## Big picture (how a request flows)

```
Browser
   │
   ▼
app.py  (routes: dashboard, settings, tables, CRUD, deleted, stock history, report APIs)
   │
   ├── i18n/           → t(), localized(), lang/theme cookies, translations
   ├── table_meta.py   → columns, search, form fields, label_key → t()
   ├── services.py     → search, pagination, forms, IQD, joins, stock logic
   ├── models.py       → ORM (trilang text columns + Rating + Feedback)
   ├── extensions.py   → shared `db`
   ├── config.py       → .env → MySQL URI (utf8mb4)
   ├── charts/
   │     ├── reports.py   → filtered business reports (dashboard)
   │     └── generate.py  → lecture-style charts (optional / catalog)
   └── templates/ + static/js
```

**Soft delete:** rows are not removed from MySQL.  
- Delete → `deleted_at = now`  
- Active pages → `deleted_at IS NULL`  
- Deleted pages → `deleted_at IS NOT NULL`  
- Restore → `deleted_at = NULL`

**Money:** prices/revenue are Iraqi Dinar, shown as e.g. `450,000 IQD`.

**Languages:** UI via `t('key')`; DB text via `name_en` / `name_ar` / `name_ckb` (+ similar for description, title, body, comment, …) and `localized(obj)`.

**Theme:** light / dark via cookie `postal_theme` + Tailwind `class` dark mode.

---

## Root files

| File | Role |
|------|------|
| **`app.py`** | Flask factory + routes: dashboard, settings (lang/theme), table CRUD, soft-delete/restore, order status, stock history, `/api/report/<key>`, `/api/options/<source>`. Port **3000**. |
| **`config.py`** | Loads `.env`; builds `SQLALCHEMY_DATABASE_URI` with `charset=utf8mb4`; `PER_PAGE`, `SECRET_KEY`. |
| **`extensions.py`** | Shared `SQLAlchemy()` instance (`db`). |
| **`models.py`** | ORM models + `SoftDeleteMixin`, `OrderItem`, `StockHistory`, `Rating`, `Feedback`, `ORDER_STATUSES`. Text fields are trilang where users see names/titles. |
| **`table_meta.py`** | UI registry: `view_columns` / `fields` with `label_key`, trilang form fields, `OPTION_SOURCES`, `translate_columns` / `translate_fields`, `nav_tables()`. |
| **`services.py`** | Form parsing, search, pagination, `format_iqd()`, `enrich_row()` (uses `localized()` for joined names), order multi-item + stock. |
| **`seed.py`** | Hard-resets tables, inserts `data/*` expanded to trilang via `i18n.db_names.expand_row`, generates 500+ orders, ratings, feedbacks, stock history. |
| **`requirements.txt`** | Flask, Flask-SQLAlchemy, PyMySQL, dotenv, matplotlib, seaborn, pandas, numpy, cryptography, … |
| **`.env`** | Local secrets (gitignored). |
| **`.env.example`** | Template (`MYSQL_DATABASE=python_postal`, …). |
| **`.gitignore`** | `__pycache__/`, `.env`, virtualenvs, … |
| **`README.md`** | Install & run guide. |
| **`PROJECT_STRUCTURE.md`** | This file. |

---

## `i18n/` — multilingual support (like React i18n, for Flask)

| File | Role |
|------|------|
| **`__init__.py`** | `t(key)`, `localized(obj, base)`, `get_locale()` / `get_theme()`, cookie names, `init_i18n(app)` (before_request + context processor). |
| **`translations.py`** | UI catalogs for `en`, `ar`, `ckb` (nav, tables, columns, reports, forms, …). |
| **`db_names.py`** | EN→AR/CKB maps for seed strings + `expand_row()` / `trilang()` helpers. |

**Compared to React i18next:**

| React | This project |
|-------|----------------|
| `t('nav.dashboard')` | Same: `t('nav.dashboard')` in Jinja/Python |
| JSON locales | Dicts in `translations.py` |
| Language store | Cookie `postal_lang` + session |
| DB content often separate | Trilang columns + `localized()` |

---

## `data/` — seed arrays only

Python lists of dicts (English source strings). `seed.py` expands text fields to `*_en` / `*_ar` / `*_ckb` before insert.

| File | Contains |
|------|----------|
| `__init__.py` | Package marker |
| `roles.py` | Admin roles |
| `provinces.py` | Provinces |
| `cities.py` | Cities → `province_id` |
| `streets.py` | Streets + postal codes |
| `posts.py` | Post offices |
| `drivers.py` | Drivers (vehicle, deliveries, rating) |
| `merchants.py` | Merchants (city, phone, revenue IQD) |
| `admins.py` | Admins → `role_id` |
| `item_types.py` | Categories |
| `items.py` | Products (price IQD, stock) |
| `orders.py` / `order_items.py` | Optional static samples (live seed mostly generates orders) |
| `feedbacks.py` | Feedback title + body samples |

**Presentation tip:** seed data stays in Git; live data lives in MySQL.

---

## `charts/` — visualizations

| File | Role |
|------|------|
| `__init__.py` | Exports report + lecture chart helpers. |
| **`reports.py`** | **Main dashboard:** filtered reports (`orders`, `revenue`, `delivery`, `inventory`, `ratings`, `correlations`). Titles/lectures/summary use `t()`. Data labels use `localized()`. PNG → base64. |
| `generate.py` | Lecture chart catalog (bar, pie, scatter, box, violin, radar, …) from active MySQL rows — available if needed; dashboard UX is report-based. |

**Dashboard UX:** report buttons + shared filters → `GET /api/report/<key>?…` → several charts + summary cards.

---

## `templates/` — HTML (Jinja2 + Tailwind)

| File | Role |
|------|------|
| `base.html` | Layout: sidebar (nav + theme/lang), mobile drawer, dark mode, cards/animations, flash messages, Lucide. |
| `dashboard.html` | Stat cards, filters, report buttons, chart panels. |
| `settings.html` | Full settings page for theme + language. |
| `table.html` | Generic table: search, pagination, Add/Edit modal, comboboxes, confirm modal, order lines, status buttons. |
| `deleted_hub.html` | Soft-deleted counts per table. |
| `stock_history.html` | Read-only stock movements for one item. |

---

## `static/js/` — front-end behaviour

| File | Role |
|------|------|
| `app.js` | Desktop sidebar collapse + mobile drawer; sync theme to `localStorage`. |
| `search.js` | Live search with **1s debounce**; keeps focus; pagination keeps `q`. |
| `confirm.js` | Custom Delete / Restore modal. |
| `combobox.js` | Searchable FK select via `/api/options/<source>?q=`. |
| `table.js` | Add/Edit modal; multilang titles via `window.TABLE_I18N`; order multi-item lines. |
| `dashboard.js` | Report buttons + filters → `/api/report/<key>`; summary cards + chart grid. |

Styling: **Tailwind CSS via CDN** in `base.html` (no npm build). Dark mode: `darkMode: 'class'`.

---

## Main routes (quick map)

| URL | Purpose |
|-----|---------|
| `/` | Dashboard (stats + filters + reports) |
| `/settings` | Theme + language page |
| `/settings/lang/<en\|ar\|ckb>` | Set language cookie + redirect |
| `/settings/theme/<light\|dark>` | Set theme cookie + redirect |
| `/api/report/<key>` | JSON: report title, summary, chart images |
| `/api/options/<source>` | JSON: `{id, label}` (localized, search all trilang names) |
| `/table/<name>` | Active rows: search, paginate, CRUD |
| `/table/<name>/create` | POST create |
| `/table/<name>/<id>/update` | POST update |
| `/table/<name>/<id>/delete` | POST soft-delete |
| `/orders/<id>/status` | POST status switch |
| `/deleted` | Soft-deleted hub |
| `/deleted/<name>` | Soft-deleted rows + restore |
| `/deleted/<name>/<id>/restore` | POST restore |
| `/items/<id>/stock-history` | Stock log for that item |

`<name>` examples: `roles`, `provinces`, `cities`, `streets`, `posts`, `drivers`, `merchants`, `admins`, `item_types`, `items`, `orders`, `ratings`, `feedbacks`.

---

## Database tables (MySQL)

Created by `seed.py` / `db.create_all()`:

| Table | Notes |
|-------|--------|
| `roles` | Trilang name + description |
| `provinces` | Trilang name; soft-deletable |
| `cities` | → province; trilang name |
| `streets` | → city; trilang name |
| `posts` | → city, street; trilang name |
| `drivers` | Trilang name + vehicle_type |
| `merchants` | Trilang name; revenue IQD |
| `admins` | → role; trilang name |
| `item_types` | Trilang name + description |
| `items` | → type + merchant; trilang name; price IQD; stock |
| `orders` | Header only |
| `order_items` | Many items per order |
| `stock_history` | Read-only movements |
| **`ratings`** | → `item_id`; score 1–5; trilang comment |
| **`feedbacks`** | Trilang title + body (not tied to an item) |

Most business tables have **`deleted_at`**.

### Domain rules worth mentioning

1. **One order → many items** via `order_items`.  
2. **Creating / updating an order** subtracts stock and writes `stock_history`.  
3. **Status → Cancelled** (or soft-delete order) restores stock.  
4. **Tables show localized joined names**, not raw FK ids.  
5. **FK fields** use searchable comboboxes.  
6. **Click an item row** → stock history.  
7. **Ratings** feed the Ratings + Heatmap reports.  
8. **UI + DB multilingual** with cookie language and trilang columns.

---

## Important design choices (teacher talking points)

### 1. Soft delete (`deleted_at`)
UI “Delete” does not run SQL `DELETE`. Undo via Deleted hub → Restore.

### 2. ORM instead of raw SQL
Flask-SQLAlchemy models + queries such as:

```python
Order.query.filter(Order.deleted_at.is_(None)).paginate(...)
```

### 3. One generic table page
`table_meta.py` drives columns/forms (`label_key` → `t()`). Special cases: `orders` (multi-item + status), `items` (row → stock history).

### 4. Application factory (`create_app`)
`seed.py` and tests create an app context without calling `app.run()`.

### 5. Report-based dashboard
Filters apply to whichever report is selected; `/api/report/<key>` returns multiple charts.

### 6. i18n without React
Custom `t()` + cookie locale for chrome; trilang DB columns for content (similar idea to React i18n + multilingual CMS fields).

### 7. Search + pagination together
Debounced search sets `?q=` and resets `page=1`. Prev/Next keep `q`.

### 8. Stock history
Every stock change is logged (`change_qty`, before/after, reason, optional `order_id`).

---

## Suggested presentation order

1. **Dashboard** — IQD stats, filters, report tabs (Orders → Heatmap).  
2. **Settings / sidebar** — switch EN ↔ AR ↔ CKB and light ↔ dark (RTL).  
3. **Table** — localized headers; Add form with `name_en` / `name_ar` / `name_ckb`.  
4. **Orders** — multi-item form, status buttons, stock side-effect.  
5. **Ratings & Feedback** — CRUD + Ratings report.  
6. **Items** — click row → stock history.  
7. **Soft delete** → Deleted hub → restore.  
8. **`models.py` + `i18n/`** — SoftDeleteMixin, Rating/Feedback, trilang fields, `t` / `localized`.  
9. **`charts/reports.py`** — how filtered reports are built.  
10. **`seed.py` + `data/`** — how sample multilang data enters MySQL.  
11. **`README.md`** — clone and run.

---

## Folder tree (source only)

```
Data Analysis/
├── app.py
├── config.py
├── extensions.py
├── models.py
├── table_meta.py
├── services.py
├── seed.py
├── requirements.txt
├── README.md
├── PROJECT_STRUCTURE.md
├── .env.example
├── .gitignore
├── i18n/
│   ├── __init__.py
│   ├── translations.py
│   └── db_names.py
├── charts/
│   ├── __init__.py
│   ├── reports.py
│   └── generate.py
├── data/
│   ├── __init__.py
│   ├── roles.py
│   ├── provinces.py
│   ├── cities.py
│   ├── streets.py
│   ├── posts.py
│   ├── drivers.py
│   ├── merchants.py
│   ├── admins.py
│   ├── item_types.py
│   ├── items.py
│   ├── orders.py
│   ├── order_items.py
│   └── feedbacks.py
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── settings.html
│   ├── table.html
│   ├── deleted_hub.html
│   └── stock_history.html
└── static/
    └── js/
        ├── app.js
        ├── search.js
        ├── confirm.js
        ├── combobox.js
        ├── table.js
        └── dashboard.js
```
