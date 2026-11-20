# Postal System — Data Analysis Dashboard

A Flask web app for a **postal / delivery system**. It stores provinces, cities, streets, post offices, drivers, merchants, admins, item types, items, orders, **ratings**, and **feedback** in **MySQL**, shows them in searchable paginated tables, and builds **filtered business reports** (with charts) on the dashboard.

Also includes **3 languages** (English / Arabic / Kurdish Sorani), **light/dark theme**, and a mobile-friendly UI.

Built for a university Python course on **Data Analysis and Visualization**.

---

## What you get

- Dashboard with **report tabs** (Orders, Revenue, Delivery, Inventory, Ratings, Heatmap) + shared filters
- Charts via Matplotlib + Seaborn (bar, pie, donut, line, area, histogram, heatmap, bubble, …)
- Table pages for every entity (search, pagination, add / edit / soft-delete)
- **Ratings** joined to items; **Feedback** (title + body)
- Deleted hub: soft-deleted rows with restore
- **i18n:** UI + DB text fields (`name_en` / `name_ar` / `name_ckb`, …)
- **Settings:** language + theme (also in the sidebar)
- MySQL via **SQLAlchemy ORM** (no raw SQL in the app layer)
- Tailwind CSS UI + collapsible / mobile sidebar

---

## Requirements

| Tool | Why |
|------|-----|
| **Python 3.10+** | Runs the Flask app |
| **pip** | Installs Python packages |
| **MySQL Server 8** | Stores the data |
| Modern browser | Opens `http://localhost:3000` |

Optional: MySQL Workbench (easy GUI to create the database).

---

## Step 1 — Install Python and pip

### Windows

1. Download Python from [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Run the installer
3. **Important:** tick **“Add python.exe to PATH”**
4. Open a new terminal and check:

```bash
python --version
pip --version
```

If `pip` is missing:

```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

### macOS

```bash
brew install python
python3 --version
pip3 --version
```

### Linux (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version
pip3 --version
```

> On Mac/Linux you may need `python3` / `pip3` instead of `python` / `pip`.

---

## Step 2 — Install MySQL

1. Install [MySQL Community Server](https://dev.mysql.com/downloads/mysql/)
2. Remember the **root password**
3. Make sure the MySQL service is running

Create an empty database (default name used by this project):

```sql
CREATE DATABASE python_postal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Or from terminal:

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS python_postal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

`utf8mb4` is required so Arabic / Kurdish text stores correctly.

---

## Step 3 — Download the project

```bash
git clone <this-repo-url>
cd "Data Analysis"
```

Or download the ZIP from GitHub → Extract → open that folder in a terminal.

---

## Step 4 — Create a virtual environment (recommended)

```bash
python -m venv .venv
```

Activate:

```bash
# Windows (Git Bash)
source .venv/Scripts/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate
```

---

## Step 5 — Install Python packages

```bash
pip install -r requirements.txt
```

Installs Flask, Flask-SQLAlchemy, PyMySQL, Matplotlib, Seaborn, pandas, numpy, python-dotenv, cryptography, …

---

## Step 6 — Configure the database (`.env`)

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env`:

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=python_postal
SECRET_KEY=any-random-string
PER_PAGE=8
```

| Variable | Meaning |
|----------|---------|
| `MYSQL_HOST` | Usually `127.0.0.1` |
| `MYSQL_PORT` | Default `3306` |
| `MYSQL_USER` | Often `root` locally |
| `MYSQL_PASSWORD` | Your MySQL password |
| `MYSQL_DATABASE` | Must match the DB you created (`python_postal`) |
| `SECRET_KEY` | Used for Flask session (language/theme cookies) |
| `PER_PAGE` | Rows per table page |

---

## Step 7 — Create tables and load sample data

```bash
python seed.py
```

What this does:

1. Connects to MySQL using `.env`
2. Drops & recreates tables (ORM models)
3. Inserts sample rows from `data/` (with EN/AR/CKB name fields)
4. Generates **500+ orders**, order lines, stock history, **~400 ratings**, and feedbacks

You should see a seed summary line (orders, lines, ratings, feedbacks).

To reset sample data later, run `python seed.py` again.

---

## Step 8 — Run the app

```bash
python app.py
```

Open: **http://localhost:3000**

Stop with `Ctrl + C`.

---

## Quick map of the website

| URL | What it is |
|-----|------------|
| `/` | Dashboard: stats + filters + report charts |
| `/settings` | Language (EN / AR / CKB) and theme (light / dark) |
| `/table/<name>` | Live table: search, add, edit, soft-delete, pagination |
| `/deleted` | Hub of soft-deleted tables |
| `/deleted/<name>` | Deleted rows + restore |
| `/items/<id>/stock-history` | Stock movement log for one item |
| `/api/report/<key>` | JSON report (charts as base64 PNGs) |
| `/api/options/<source>` | Combobox options (localized labels) |

Sidebar tables include: Roles, Provinces, Cities, Streets, Posts, Drivers, Merchants, Admins, Item Types, Items, Orders, **Ratings**, **Feedback**.

Language and theme can also be changed from the **sidebar** (and mobile top bar).

---

## Languages & theme (how it works)

### UI text (like React i18n `t('key')`)

- Strings live in `i18n/translations.py` for `en`, `ar`, `ckb`
- Templates / Python call `t('nav.dashboard')`
- Active language is stored in cookie `postal_lang` (+ session)
- Arabic & Kurdish use **RTL** layout (`dir="rtl"`)

### Database text (names, titles, …)

- Columns such as `name_en`, `name_ar`, `name_ckb` (same idea as `enName` / `arName` / `ckbName`)
- Also used for descriptions, feedback title/body, rating comments, vehicle type, …
- Display uses `localized(obj)` → picks the active language (fallback to English)
- Add/Edit forms show all three language fields

### Theme

- Cookie `postal_theme` = `light` or `dark`
- Tailwind `darkMode: 'class'` on `<html>`
- Early script avoids flash of wrong theme

---

## Dashboard reports

| Report key | What it shows |
|------------|----------------|
| `orders` | Orders by city / merchant / driver / status + trend |
| `revenue` | IQD revenue by province / city / merchant / month |
| `delivery` | Avg delivery days, status mix, days histogram |
| `inventory` | Top sold items, sales by type, low stock |
| `ratings` | Avg rating by item, score distribution |
| `correlations` | Heatmaps linking rating × price × qty × orders × revenue |

Shared filters: province, city, merchant, driver, post, status, date range / presets (today, week, month, year).

---

## Common problems

### `Access denied for user 'root'@'localhost'`

Wrong password in `.env`. Fix `MYSQL_PASSWORD`.

### `Unknown database 'python_postal'`

Create the database — see Step 2.

### `ModuleNotFoundError: No module named 'flask'`

Activate the virtualenv and run `pip install -r requirements.txt`.

### Port 3000 already in use

Close the other process, or change the port at the bottom of `app.py`.

### Charts look slow the first time

Normal — Matplotlib builds images on demand for each report.

### Arabic / Kurdish looks wrong in MySQL

Database and connection must use `utf8mb4` (already set in `config.py` URI).

---

## Project docs

- **`README.md`** (this file) — install & run
- **`PROJECT_STRUCTURE.md`** — folders, files, architecture for presentation

---

## Tech stack (short)

- **Backend:** Flask
- **ORM:** Flask-SQLAlchemy + PyMySQL
- **DB:** MySQL (`utf8mb4`)
- **Charts:** Matplotlib, Seaborn, pandas, NumPy
- **i18n:** custom `i18n/` module (cookie locale + trilang DB fields)
- **Frontend:** Jinja2, Tailwind CSS (CDN), Lucide icons

---

## License / course use

University coursework project — feel free to fork and adapt for learning.
