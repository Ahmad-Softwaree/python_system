# Postal System — Data Analysis Dashboard

A Flask web app for a **postal / delivery system**. It stores provinces, cities, streets, post offices, drivers, merchants, admins, item types, items, and orders in **MySQL**, shows them in searchable paginated tables, and draws **data-analysis charts** (bar, pie, scatter, box, violin, heatmap, radar, …) on a one-page dashboard.

Built for a university Python course on **Data Analysis and Visualization**.

---

## What you get

- Dashboard with lecture-style charts (Matplotlib + Seaborn)
- Table pages for every entity (search, pagination, add / edit / soft-delete)
- Deleted hub: soft-deleted rows with restore
- MySQL database via **SQLAlchemy ORM** (no raw SQL in the app)
- Tailwind CSS UI + collapsible sidebar

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
4. Open a new terminal (PowerShell, CMD, or Git Bash) and check:

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
# If Homebrew is installed:
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

> On Mac/Linux you may need `python3` / `pip3` instead of `python` / `pip`. The rest of this README uses `python` and `pip`; swap names if needed.

---

## Step 2 — Install MySQL

1. Install [MySQL Community Server](https://dev.mysql.com/downloads/mysql/)
2. During setup, remember the **root password** you choose
3. Make sure the MySQL service is running

Create an empty database (Workbench SQL tab or terminal):

```sql
CREATE DATABASE postal_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Or from terminal:

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS postal_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

---

## Step 3 — Download the project

```bash
git clone <this-repo-url>
cd "Data Analysis"
```

Or download the ZIP from GitHub → Extract → open that folder in a terminal.

---

## Step 4 — Create a virtual environment (recommended)

Keeps project packages separate from the rest of your PC.

```bash
python -m venv .venv
```

Activate it:

```bash
# Windows (Git Bash)
source .venv/Scripts/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

You should see `(.venv)` in the prompt.

---

## Step 5 — Install Python packages

```bash
pip install -r requirements.txt
```

This installs Flask, Flask-SQLAlchemy, PyMySQL, Matplotlib, Seaborn, pandas, numpy, python-dotenv, etc.

---

## Step 6 — Configure the database (`.env`)

1. Copy the example env file:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

2. Open `.env` in a text editor and set your MySQL password:

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=postal_system
SECRET_KEY=any-random-string
PER_PAGE=8
```

| Variable | Meaning |
|----------|---------|
| `MYSQL_HOST` | Usually `127.0.0.1` on your own PC |
| `MYSQL_PORT` | Default MySQL port is `3306` |
| `MYSQL_USER` | Often `root` for local study projects |
| `MYSQL_PASSWORD` | The password you set when installing MySQL |
| `MYSQL_DATABASE` | Must match the database you created |
| `PER_PAGE` | How many rows per table page |

---

## Step 7 — Create tables and load sample data

```bash
python seed.py
```

What this does:

1. Connects to MySQL using `.env`
2. Creates all tables (ORM models)
3. Clears old rows (if any)
4. Inserts the sample arrays from the `data/` folder

You should see: `Seed complete.`

To reset everything back to the sample data later, run `python seed.py` again.

---

## Step 8 — Run the app

```bash
python app.py
```

Open your browser:

**http://localhost:3000**

Stop the server with `Ctrl + C` in the terminal.

---

## Quick map of the website

| URL | What it is |
|-----|------------|
| `/` | Dashboard + charts |
| `/table/provinces` (and other names) | Live table: search, add, edit, soft-delete, pagination |
| `/deleted` | Hub of soft-deleted tables |
| `/deleted/orders` (etc.) | Deleted rows + restore |

Sidebar table links: Provinces, Cities, Streets, Posts, Drivers, Merchants, Admins, Item Types, Items, Orders.

---

## Common problems

### `Access denied for user 'root'@'localhost'`

Wrong password in `.env`. Fix `MYSQL_PASSWORD` and try again.

### `Unknown database 'postal_system'`

You forgot to create the database — see Step 2.

### `ModuleNotFoundError: No module named 'flask'`

Packages are not installed, or the virtualenv is not activated. Repeat Steps 4–5.

### `pip` is not recognized

Use `python -m pip install -r requirements.txt` instead.

### Port 3000 already in use

Change the port at the bottom of `app.py`, or close the other program using 3000.

### Charts page is slow the first time

Normal — Matplotlib builds many images. Later loads are usually faster.

### Windows: weird console encoding errors

Avoid special Unicode characters in `print()` if your terminal uses an old code page. The project already uses plain ASCII in startup messages.

---

## Project docs

- **`README.md`** (this file) — how to install and run
- **`PROJECT_STRUCTURE.md`** — what every folder and file does

---

## Tech stack (short)

- **Backend:** Flask
- **ORM:** Flask-SQLAlchemy + PyMySQL
- **DB:** MySQL
- **Charts:** Matplotlib, Seaborn, pandas, NumPy
- **Frontend:** Jinja2 templates, Tailwind CSS (CDN), Lucide icons

---

## License / course use

University coursework project — feel free to fork and adapt for learning.
