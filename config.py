import os
from dotenv import load_dotenv

# Load key=value pairs from the local .env file into environment variables.
# .env is gitignored so each classmate can use their own MySQL password.
load_dotenv()


class Config:
    """Flask / SQLAlchemy settings. Values come from .env when present."""

    SECRET_KEY = os.getenv("SECRET_KEY", "postal-dev-secret")
    # How many rows each table page shows (Prev / Next pagination).
    PER_PAGE = int(os.getenv("PER_PAGE", "8"))

    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "mysql")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "python_postal")

    # SQLAlchemy connection URL.
    # "mysql+pymysql://" means: MySQL database, using the PyMySQL driver.
    # charset=utf8mb4 supports Kurdish / Arabic / emoji characters if needed.
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    )
    # Recommended Flask-SQLAlchemy default (avoids extra overhead).
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # pool_pre_ping: if MySQL closed a stale connection, reconnect instead of crashing.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
