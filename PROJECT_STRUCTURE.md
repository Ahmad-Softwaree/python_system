# Project Structure Explained

This document explains **every folder and file** in the Postal System project: what it is for, and how it fits into the big picture. Use it when presenting to your teacher.

**Current stack:** Flask · Flask-SQLAlchemy (ORM) · MySQL · Matplotlib/Seaborn · Tailwind CSS (CDN) · Lucide icons

**Default local URL:** http://localhost:3000  
**Default DB name (from `.env`):** `python_postal`

---

## Big picture (how a request flows)

```
Browser
   │
   ▼
app.py  (routes: dashboard, tables, CRUD, deleted, orders status, stock history, APIs)
   │
   ├── table_meta.py   → columns, search, form fields, relation combobox sources
   ├── services.py     → search, pagination, forms, IQD format, joins, stock logic
   ├── models.py       → SQLAlchemy ORM classes (MySQL tables)
   ├── extensions.py   → shared `db` object
   ├── config.py       → reads .env → MySQL connection string
   ├── charts/         → one chart at a time via /api/chart/<id>
   └── templates/      → Jinja2 + Tailwind
            └── static/js → sidebar, search debounce, combobox, confirm, dashboard, table modal
```

**Soft delete:** rows are not removed from MySQL.  
- Delete → `deleted_at = now`  
- Active pages → `deleted_at IS NULL`  
- Deleted pages → `deleted_at IS NOT NULL`  
- Restore → `deleted_at = NULL`

**Money:** all prices/revenue are Iraqi Dinar, shown as e.g. `450,000 IQD`.

---

## Root files

| File | Role |
|------|------|
| **`app.py`** | Flask app factory + all routes: dashboard, generic table CRUD, soft-delete/restore, order status buttons, stock history page, `/api/chart/<id>`, `/api/options/<source>`. Runs on port **3000**. |
| **`config.py`** | Loads `.env` (`python-dotenv`) and builds `SQLALCHEMY_DATABASE_URI` (`mysql+pymysql://…`). Also `PER_PAGE` for pagination. |
| **`extensions.py`** | Shared `SQLAlchemy()` instance (`db`). Separate file avoids circular imports between `app.py` and `models.py`. |
| **`models.py`** | ORM models for every table + `SoftDeleteMixin`, `OrderItem`, `StockHistory`, `ORDER_STATUSES`. Each model has `to_dict()`. |
| **`table_meta.py`** | UI registry: `view_columns` (joined display names), `search`, `fields` (including `relation` comboboxes), `OPTION_SOURCES` for `/api/options/…`. |
| **`services.py`** | Helpers: form parsing, search filter, pagination URLs, `format_iqd()`, `enrich_row()` (joins → names), order multi-item apply, stock adjust / cancel restore / status changes. |
| **`seed.py`** | Hard-resets MySQL tables (FK checks off on same connection), `create_all()`, inserts seed arrays, writes initial stock-history rows. Run: `python seed.py`. |
| **`requirements.txt`** | pip packages: Flask, Flask-SQLAlchemy, PyMySQL, dotenv, matplotlib, seaborn, pandas, numpy, … |
| **`.env`** | Local secrets (DB password, DB name). **Gitignored** — each developer copies from `.env.example`. |
| **`.env.example`** | Committed template for `.env` (`MYSQL_DATABASE=python_postal`, etc.). |
| **`.gitignore`** | Ignores `__pycache__/`, `.env`, virtualenvs, logs. |
| **`README.md`** | Public install & run guide for GitHub / classmates. |
| **`PROJECT_STRUCTURE.md`** | This file — architecture notes for presentation. |

---

## `data/` — seed arrays only

These Python lists of dicts are **not** the live database. `seed.py` loads them into MySQL.

| File | Contains |
|------|----------|
| `__init__.py` | Makes `data` a package (`from data.roles import roles`). |
| `roles.py` | Admin roles (Super Admin, Post Manager, …) |
| `provinces.py` | Provinces (Erbil, Sulaymaniyah, …) |
| `cities.py` | Cities → `province_id` |
| `streets.py` | Streets + postal codes → `city_id` |
| `posts.py` | Post offices (capacity, staff) |
| `drivers.py` | Drivers (no post_id — vehicle, deliveries, rating) |
| `merchants.py` | Merchants (no category — city, phone, revenue in IQD) |
| `admins.py` | Admins → `role_id` (no post_id) |
| `item_types.py` | Item categories (name + description only) |
| `items.py` | Products → type + merchant; **price in IQD**; stock |
| `orders.py` | Order headers (merchant, driver, post, city, street, total, status, …) |
| `order_items.py` | Line items: many rows per order (`order_id`, `item_id`, qty, unit price, line total) |

**Presentation tip:** seed data stays in Git; live data lives in MySQL.

---

## `charts/` — dashboard visualizations

| File | Role |
|------|------|
| `__init__.py` | Exports `get_chart_catalog`, `build_chart_by_id`, `build_all_charts`. |
| `generate.py` | Builds lecture charts with Matplotlib/Seaborn from **active** MySQL rows. Dashboard loads **one chart at a time** via API (not all at once). PNG → base64 for `<img src="data:image/png;base64,…">`. Uses `Agg` backend (no GUI window). |

**Chart types:** bar, grouped bar, horizontal bar, pie, donut, line, area, histogram, scatter, scatter+trend, bubble, box, violin, heatmap, count plot, KDE, radar.

**Dashboard UX:** buttons on `/` → `GET /api/chart/<id>` → show that chart only (cached in the browser for the session).

---

## `templates/` — HTML (Jinja2 + Tailwind)

| File | Role |
|------|------|
| `base.html` | Layout: collapsible sidebar, Tailwind CDN, Lucide icons, flash messages. Child pages `{% extends "base.html" %}`. |
| `dashboard.html` | Stat cards (revenue as IQD) + chart button strip + single chart panel. |
| `table.html` | Generic table for active **and** deleted modes: live search, pagination, joined name columns, Add/Edit modal, relation comboboxes, custom delete/restore confirm modal, order multi-item lines, status switch buttons. |
| `deleted_hub.html` | Cards per table with soft-deleted counts → `/deleted/<name>`. |
| `stock_history.html` | Read-only stock movements for one item (`/items/<id>/stock-history`). |

---

## `static/js/` — front-end behaviour

| File | Role |
|------|------|
| `app.js` | Collapsible sidebar; state in `data-collapsed` + `localStorage`; toggle always clickable. |
| `search.js` | Live search: `oninput` → **1 second debounce** → reload `?q=&page=1`. Keeps focus after reload until the user blurs the input. Pagination keeps the same `q`. |
| `confirm.js` | Custom Delete / Restore confirm modal (no `window.alert` / `confirm`). |
| `combobox.js` | Searchable FK select: type → `/api/options/<source>?q=` → click to set hidden id. |
| `table.js` | Add/Edit modal; fills relation fields; for **orders**, dynamic multi-item lines (`item_id[]` + `quantity[]`). |
| `dashboard.js` | Chart buttons → fetch `/api/chart/<id>` → show one chart (with loading state + cache). |

Styling: **Tailwind CSS via CDN** in `base.html` (no npm build).

---

## Main routes (quick map)

| URL | Purpose |
|-----|---------|
| `/` | Dashboard + chart buttons |
| `/api/chart/<id>` | JSON: one rendered chart (base64 PNG) |
| `/api/options/<source>` | JSON: `{id, label}` list for comboboxes |
| `/table/<name>` | Active rows: search, paginate, CRUD |
| `/table/<name>/create` | POST create |
| `/table/<name>/<id>/update` | POST update |
| `/table/<name>/<id>/delete` | POST soft-delete |
| `/orders/<id>/status` | POST switch order status (Pending / In Transit / Delivered / Cancelled) |
| `/deleted` | Soft-deleted hub |
| `/deleted/<name>` | Soft-deleted rows + restore |
| `/deleted/<name>/<id>/restore` | POST restore |
| `/items/<id>/stock-history` | Read-only stock log for that item |

`<name>` examples: `roles`, `provinces`, `cities`, `streets`, `posts`, `drivers`, `merchants`, `admins`, `item_types`, `items`, `orders`.

---

## Database tables (MySQL)

Created by `seed.py` / `db.create_all()` from ORM models:

| Table | Notes |
|-------|--------|
| `roles` | Admin roles |
| `provinces` | Soft-deletable |
| `cities` | → province |
| `streets` | → city |
| `posts` | → city, street |
| `drivers` | No post_id |
| `merchants` | No category; revenue in IQD |
| `admins` | → `role_id` (not post_id) |
| `item_types` | No avg weight |
| `items` | → type + merchant; price IQD; stock; **no weight** |
| `orders` | Header only (no single item_id/qty) |
| `order_items` | Many items per order |
| `stock_history` | Read-only movements (sale / cancel / edit) |

Most business tables have **`deleted_at`**.  
`order_items` and `stock_history` are supporting tables (history is read-only in the UI).

### Domain rules worth mentioning

1. **One order → many items** via `order_items`.  
2. **Creating / updating an order** subtracts stock and writes `stock_history`.  
3. **Status → Cancelled** (or soft-delete order) restores stock.  
4. **Un-cancel** subtracts stock again.  
5. **Tables show joined names** (city name, role name, …), not raw FK ids.  
6. **FK form fields** use searchable comboboxes, not typed ids.  
7. **Click an item row** → stock history page.

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
`table_meta.py` drives columns/forms. Special cases: `orders` (multi-item + status buttons), `items` (row link to stock history).

### 4. Application factory (`create_app`)
`seed.py` creates an app context without calling `app.run()`.

### 5. Charts on demand
Catalog of titles on the dashboard; images rendered only when a button is clicked (`/api/chart/<id>`).

### 6. Search + pagination together
Debounced search sets `?q=` and resets `page=1`. Prev/Next keep `q`.

### 7. Stock history
Every stock change is logged (`change_qty`, before/after, reason, optional `order_id`).

---

## Suggested presentation order

1. **Dashboard** — stats in IQD, click chart buttons one-by-one.  
2. **Table** — live search (focus stays), pagination, combobox Add/Edit.  
3. **Orders** — multi-item form, status buttons, stock side-effect.  
4. **Items** — click row → stock history.  
5. **Soft delete** → Deleted hub → restore (custom modal).  
6. **`models.py`** — SoftDeleteMixin, Order + OrderItem, StockHistory, Role.  
7. **`table_meta.py` + `services.py`** — generic UI + enrich/joins + stock helpers.  
8. **`seed.py` + `data/`** — how sample data enters MySQL.  
9. **`README.md`** — anyone can clone and run.

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
├── charts/
│   ├── __init__.py
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
│   └── order_items.py
├── templates/
│   ├── base.html
│   ├── dashboard.html
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
