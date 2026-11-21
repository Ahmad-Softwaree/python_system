"""
Flask i18n — similar idea to react-i18next, without a React build.

How it works (vs React i18n):
  React:  i18n.t('key') + JSON locales + language detector
  Here:   t('key') in Jinja/Python + dict locales + cookie `postal_lang`

UI chrome (buttons, nav, labels) → translation keys in `translations.py`.
DB text (names, titles) → columns name_en / name_ar / name_ckb (etc.),
picked at read time with `localized(obj, 'name')`.
"""

from __future__ import annotations

from flask import g, request, session

from i18n.translations import TRANSLATIONS

LANGS = ("en", "ar", "ckb")
LANG_META = {
    "en": {"label": "English", "native": "English", "dir": "ltr"},
    "ar": {"label": "Arabic", "native": "العربية", "dir": "rtl"},
    "ckb": {"label": "Kurdish", "native": "کوردی", "dir": "rtl"},
}
COOKIE_LANG = "postal_lang"
COOKIE_THEME = "postal_theme"
THEMES = ("light", "dark")


def get_locale() -> str:
    lang = getattr(g, "locale", None)
    if lang in LANGS:
        return lang
    return "en"


def get_theme() -> str:
    theme = getattr(g, "theme", None)
    if theme in THEMES:
        return theme
    return "light"


def is_rtl() -> bool:
    return LANG_META[get_locale()]["dir"] == "rtl"


def t(key: str, **kwargs) -> str:
    """Translate a UI key for the active language (fallback → English → key)."""
    lang = get_locale()
    text = TRANSLATIONS.get(lang, {}).get(key)
    if text is None:
        text = TRANSLATIONS.get("en", {}).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def localized(obj, base: str = "name", lang: str | None = None) -> str:
    """
    Read multilang DB fields: name_en / name_ar / name_ckb.
    Falls back: active lang → en → ar → ckb → first non-empty.
    """
    lang = lang or get_locale()
    for code in (lang, "en", "ar", "ckb"):
        val = getattr(obj, f"{base}_{code}", None)
        if val not in (None, ""):
            return str(val)
    # Legacy single column if still present
    legacy = getattr(obj, base, None)
    return str(legacy) if legacy not in (None, "") else "—"


def resolve_prefs():
    """Load lang/theme from cookie (preferred) or session into flask.g."""
    lang = request.cookies.get(COOKIE_LANG) or session.get("lang") or "en"
    theme = request.cookies.get(COOKIE_THEME) or session.get("theme") or "light"
    if lang not in LANGS:
        lang = "en"
    if theme not in THEMES:
        theme = "light"
    g.locale = lang
    g.theme = theme
    # Source-peek buttons (student teaching aid) — default on
    from source_peek import resolve_show_source

    resolve_show_source()


def init_i18n(app):
    @app.before_request
    def _load_prefs():
        resolve_prefs()

    @app.context_processor
    def _inject_i18n():
        from source_peek import show_source_enabled

        return {
            "t": t,
            "locale": get_locale(),
            "theme": get_theme(),
            "is_rtl": is_rtl(),
            "langs": LANG_META,
            "lang_codes": LANGS,
            "localized": localized,
            "show_source": show_source_enabled(),
        }
