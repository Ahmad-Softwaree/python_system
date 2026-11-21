"""
Admin authentication — bcrypt-style password hashes (werkzeug) + JWT tokens.

Token is stored in the httpOnly cookie `postal_jwt`. APIs return 401 when missing/invalid;
HTML pages redirect to /login.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, jsonify, redirect, request, url_for
from werkzeug.security import check_password_hash, generate_password_hash

COOKIE_JWT = "postal_jwt"
# Public: auth pages + preference toggles usable on the login screen
PUBLIC_ENDPOINTS = {
    "login",
    "logout",
    "api_login",
    "settings_lang",
    "settings_theme",
    "static",
}


def hash_password(plain: str) -> str:
    """Hash a plaintext password for DB storage (never store plain text)."""
    return generate_password_hash(plain)


def verify_password(password_hash: str | None, plain: str) -> bool:
    if not password_hash or not plain:
        return False
    return check_password_hash(password_hash, plain)


def create_access_token(admin_id: int, email: str) -> str:
    hours = int(current_app.config.get("JWT_EXPIRE_HOURS", 24))
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(admin_id),  # JWT "sub" must be a string (RFC 7519)
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=hours)).timestamp()),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def _extract_token() -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return request.cookies.get(COOKIE_JWT) or None


def get_current_admin():
    """Resolve Admin from JWT (cookie or Bearer). Returns None if invalid."""
    from models import Admin

    token = _extract_token()
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    admin_id = payload.get("sub")
    if not admin_id:
        return None
    admin = Admin.query.filter(
        Admin.id == int(admin_id),
        Admin.deleted_at.is_(None),
        Admin.active == True,  # noqa: E712
    ).first()
    return admin


def set_jwt_cookie(response, token: str):
    hours = int(current_app.config.get("JWT_EXPIRE_HOURS", 24))
    response.set_cookie(
        COOKIE_JWT,
        token,
        max_age=hours * 3600,
        httponly=True,
        samesite="Lax",
        path="/",
    )
    return response


def clear_jwt_cookie(response):
    response.set_cookie(COOKIE_JWT, "", max_age=0, httponly=True, samesite="Lax", path="/")
    return response


def wants_json() -> bool:
    if request.path.startswith("/api/"):
        return True
    accept = (request.accept_mimetypes.best or "") if request.accept_mimetypes else ""
    return "application/json" in accept and "text/html" not in (request.accept_mimetypes[0][0] if request.accept_mimetypes else "")


def unauthorized_response():
    if wants_json() or request.path.startswith("/api/"):
        return jsonify({"error": "unauthorized", "message": "Login required"}), 401
    nxt = request.full_path if request.query_string else request.path
    if nxt.endswith("?"):
        nxt = nxt[:-1]
    return redirect(url_for("login", next=nxt))


def init_auth(app):
    @app.before_request
    def _require_login():
        endpoint = request.endpoint or ""
        if endpoint in PUBLIC_ENDPOINTS or endpoint.startswith("static"):
            return None
        admin = get_current_admin()
        if admin:
            g.current_admin = admin
            return None
        g.current_admin = None
        return unauthorized_response()

    @app.context_processor
    def _inject_auth():
        return {"current_admin": getattr(g, "current_admin", None)}


def login_required(view):
    """Optional extra guard for a single view (before_request already covers most)."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if getattr(g, "current_admin", None) is None:
            return unauthorized_response()
        return view(*args, **kwargs)

    return wrapped
