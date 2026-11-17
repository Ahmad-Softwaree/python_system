# Project Structure Explained

This document explains **every folder and file** in the Postal System project: what it is for, and how it fits into the big picture. Use it when presenting to your teacher.

---

## Big picture (how a request flows)

```
Browser
   │
   ▼
app.py  (routes: dashboard, tables, deleted, create/update/delete/restore)
   │
   ├── table_meta.py   → which columns / search fields / form fields per table
   ├── services.py     → search, pagination, form parsing helpers
   ├── models.py       → SQLAlchemy ORM classes (map to MySQL tables)
   ├── extensions.py   → shared `db` object
   ├── config.py       → reads .env → builds MySQL connection string
   ├── charts/         → builds Matplotlib/Seaborn PNGs for the dashboard
   └── templates/      → HTML pages (Jinja2 + Tailwind)
            └── static/js → sidebar collapse + create/edit modal
```

**Soft delete idea:** rows are not removed from MySQL. We set `deleted_at` to a timestamp. Active pages filter `deleted_at IS NULL`. Deleted pages filter `deleted_at IS NOT NULL`. Restore sets `deleted_at` back to `NULL`.

---

## Root files

| File | Role |
|------|------|
| **`app.py`** | Main Flask application. Creates the app, registers all HTTP routes (dashboard, table CRUD, deleted hub/restore), starts the server on port 3000. |
| **`config.py`** | Loads `.env` with `python-dotenv` and builds `SQLALCHEMY_DATABASE_URI` for MySQL. Also holds `PER_PAGE` for pagination. |
| **`extensions.py`** | Creates one shared `SQLAlchemy()` instance (`db`). Kept in a tiny file so `models.py` and `app.py` can both import it without circular imports. |
| **`models.py`** | ORM models: one Python class per MySQL table. Includes `SoftDeleteMixin` (`deleted_at`, `soft_delete()`, `restore()`). Each model has `to_dict()` for templates/charts. |
| **`table_meta.py`** | Registry of all tables for the UI: title, model class, visible columns, searchable fields, and modal form field definitions. Lets one generic table page work for every entity. |
| **`services.py`** | Helper functions used by routes: convert form values to Python types, apply form data onto a model, build SQLAlchemy search filters, paginate queries, build prev/next URLs, count deleted rows. |
| **`seed.py`** | One-time / reset script. Creates tables, clears them, inserts sample rows from `data/*.py` into MySQL using the ORM (`bulk_insert_mappings`). |
| **`requirements.txt`** | List of pip packages friends must install. |
| **`.env`** | Local secrets (MySQL password, etc.). **Not committed** to Git (see `.gitignore`). Each developer creates their own from `.env.example`. |
| **`.env.example`** | Safe template for `.env` that *is* committed so others know which variables to set. |
| **`.gitignore`** | Tells Git to ignore `__pycache__/`, `.env`, virtualenvs, etc. |
| **`README.md`** | Public install & run guide for GitHub. |
| **`PROJECT_STRUCTURE.md`** | This file — architecture notes for presentation. |

---

## `data/` — seed arrays only

These files are **not** used as the live database. They are Python lists of dictionaries used by `seed.py` to fill MySQL the first time (or when resetting).

| File | Contains |
|------|----------|
| `__init__.py` | Marks the folder as a Python package (so `from data.provinces import …` works). |
| `provinces.py` | Sample provinces (Erbil, Sulaymaniyah, …) |
| `cities.py` | Sample cities linked by `province_id` |
| `streets.py` | Streets + postal codes linked by `city_id` |
| `posts.py` | Post offices (capacity, staff) |
| `drivers.py` | Drivers (vehicle, deliveries, rating) |
| `merchants.py` | Merchants (category, revenue) |
| `admins.py` | Admin users |
| `item_types.py` | Categories (Electronics, Food, …) |
| `items.py` | Products linked to type + merchant |
| `orders.py` | Orders linking merchants, drivers, posts, cities, items |

**Presentation tip:** explain that separating seed data from the live DB is good practice — sample data stays versioned in Git; the real database lives in MySQL.

---

## `charts/` — dashboard visualizations

| File | Role |
|------|------|
| `__init__.py` | Re-exports `build_all_charts` so `app.py` can `from charts import build_all_charts`. |
| `generate.py` | Loads **active** (non-deleted) rows from MySQL, then draws every lecture chart type with Matplotlib/Seaborn. Each chart is saved to an in-memory PNG and returned as **base64** so the HTML can embed it with `<img src="data:image/png;base64,...">` without writing image files to disk. |

Chart types covered (matching the course PowerPoint): bar, grouped bar, horizontal bar, pie, donut, line, area, histogram, scatter, scatter+trend, bubble, box, violin, heatmap, count plot, KDE, radar.

---

## `templates/` — HTML pages (Jinja2)

| File | Role |
|------|------|
| `base.html` | Shared layout: collapsible sidebar, Tailwind CDN, Lucide icons, flash messages. Other pages `{% extends "base.html" %}`. |
| `dashboard.html` | Summary stat cards + grid of chart images. |
| `table.html` | Generic table UI used for **both** active and deleted modes: search box, pagination arrows, add/edit modal, delete or restore buttons. |
| `deleted_hub.html` | Grid of cards (one per table) showing how many soft-deleted rows exist; each card links to `/deleted/<name>`. |

---

## `static/` — front-end assets

| File | Role |
|------|------|
| `js/app.js` | Sidebar collapse/expand. Remembers state in `localStorage` so refresh keeps the same width. |
| `js/table.js` | Opens the Add/Edit modal, fills inputs from the row JSON, switches the form `action` URL between create and update. |

Styling is done with **Tailwind CSS via CDN** inside `base.html` (no separate CSS build step for this course project).

---

## Important design choices (good talking points for the teacher)

### 1. Soft delete (`deleted_at`)
We do **not** run SQL `DELETE` for normal “delete” in the UI.  
- Delete → set `deleted_at = now`  
- Restore → set `deleted_at = NULL`  
This keeps history and allows undo.

### 2. ORM instead of raw SQL
`Flask-SQLAlchemy` models describe tables in Python. Queries look like:

```python
Order.query.filter(Order.deleted_at.is_(None)).paginate(...)
```

Safer and clearer for a student project than string-building SQL.

### 3. One generic table page
`table_meta.py` describes every entity. Routes and `table.html` stay generic — adding a new table mostly means adding a model + a meta entry, not copying a whole page.

### 4. Factory pattern (`create_app`)
`create_app()` builds the Flask app. `seed.py` calls it to get an application context without starting the web server. `app = create_app()` at the bottom is what `python app.py` runs.

### 5. Charts as base64
Server renders charts with Matplotlib (`Agg` backend = no GUI window), encodes PNG to base64, embeds in HTML. Works well for a local dashboard without a separate image folder.

### 6. Pagination + search
Every list query supports `?q=` and `?page=`. Prev/Next links keep the current search term.

---

## Database tables (MySQL)

Created automatically from models when you run `seed.py` or `app.py`:

`provinces`, `cities`, `streets`, `posts`, `drivers`, `merchants`, `admins`, `item_types`, `items`, `orders`

All of them include:

- normal business columns  
- **`deleted_at`** (`NULL` = active, timestamp = soft-deleted)

Foreign keys follow the postal domain (city → province, order → driver/item/city, …).

---

## Suggested presentation order

1. Show the **dashboard** (charts from the lecture).  
2. Open a **table** → search → paginate → add/edit.  
3. Soft-delete a row → open **Deleted** hub → restore.  
4. Open **`models.py`** and explain `SoftDeleteMixin`.  
5. Open **`table_meta.py`** and explain the generic CRUD idea.  
6. Mention **`seed.py`** + **`data/`** as how sample data enters MySQL.  
7. Mention **`README.md`** so anyone can clone and run it.
