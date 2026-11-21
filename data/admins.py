# Demo password for every seeded admin (hashed in seed.py before DB insert).
# Login example: ahmed@postal.iq  /  Admin@123
DEFAULT_ADMIN_PASSWORD = "Admin@123"

admins = [
    {"id": 1, "name": "Ahmed Salih", "email": "ahmed@postal.iq", "password": DEFAULT_ADMIN_PASSWORD, "role_id": 1, "active": True},
    {"id": 2, "name": "Sara Kamal", "email": "sara@postal.iq", "password": DEFAULT_ADMIN_PASSWORD, "role_id": 2, "active": True},
    {"id": 3, "name": "Nizar Hadi", "email": "nizar@postal.iq", "password": DEFAULT_ADMIN_PASSWORD, "role_id": 2, "active": True},
    {"id": 4, "name": "Lara Othman", "email": "lara@postal.iq", "password": DEFAULT_ADMIN_PASSWORD, "role_id": 3, "active": True},
    {"id": 5, "name": "Bayan Rashid", "email": "bayan@postal.iq", "password": DEFAULT_ADMIN_PASSWORD, "role_id": 2, "active": True},
    {"id": 6, "name": "Dana Ali", "email": "dana@postal.iq", "password": DEFAULT_ADMIN_PASSWORD, "role_id": 3, "active": False},
    {"id": 7, "name": "Rojin Aziz", "email": "rojin@postal.iq", "password": DEFAULT_ADMIN_PASSWORD, "role_id": 2, "active": True},
    {"id": 8, "name": "Hiwa Karim", "email": "hiwa@postal.iq", "password": DEFAULT_ADMIN_PASSWORD, "role_id": 4, "active": True},
    {"id": 9, "name": "Media Faruq", "email": "media@postal.iq", "password": DEFAULT_ADMIN_PASSWORD, "role_id": 4, "active": True},
    {"id": 10, "name": "Peshawa Nuri", "email": "peshawa@postal.iq", "password": DEFAULT_ADMIN_PASSWORD, "role_id": 3, "active": True},
]
