# Shared SQLAlchemy instance.
# Why a separate file? If we created `db` inside app.py, then models.py
# would need to import app.py, and app.py would import models.py → circular import.
# Keeping `db` here lets both sides import it safely.
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
