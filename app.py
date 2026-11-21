"""
Postal System — Flask dashboard with MySQL ORM CRUD.
Entry: python app.py  →  http://localhost:3000
"""

from flask import Flask, abort, flash, jsonify, make_response, redirect, render_template, request, session, url_for
from sqlalchemy import or_

from charts import build_report, get_report_catalog
from config import Config
from extensions import db
from i18n import COOKIE_LANG, COOKIE_THEME, LANGS, THEMES, init_i18n, localized, t
from source_peek import COOKIE_SHOW_SOURCE, get_source
from models import (
    ORDER_STATUSES,
    City,
    Driver,
    Item,
    Merchant,
    Order,
    OrderItem,
    Post,
    Province,
    StockHistory,
)
from services import (
    apply_form,
    apply_order_items,
    deleted_counts,
    enrich_row,
    format_iqd,
    paginate_query,
    pagination_urls,
    parse_order_item_lines,
    restore_order_stock,
    search_filter,
    set_order_status,
)
from table_meta import OPTION_SOURCES, TABLES, nav_tables, translate_columns, translate_fields


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    init_i18n(app)

    @app.context_processor
    def inject_globals():
        return {
            "tables": nav_tables(),
            "order_statuses": ORDER_STATUSES,
            "format_iqd": format_iqd,
        }

    register_routes(app)
    return app


def _set_pref_cookie(resp, key, value):
    resp.set_cookie(key, value, max_age=60 * 60 * 24 * 365, samesite="Lax")
    return resp


def register_routes(app):
    @app.route("/")
    def dashboard():
        active_orders = Order.query.filter(Order.deleted_at.is_(None)).all()
        stats = {
            "orders": len(active_orders),
            "delivered": sum(1 for o in active_orders if o.status == "Delivered"),
            "revenue": format_iqd(sum(o.total_price for o in active_orders)),
            "drivers": Driver.query.filter(Driver.deleted_at.is_(None)).count(),
            "merchants": Merchant.query.filter(Merchant.deleted_at.is_(None)).count(),
            "posts": Post.query.filter(Post.deleted_at.is_(None)).count(),
            "items": Item.query.filter(Item.deleted_at.is_(None)).count(),
            "cities": City.query.filter(City.deleted_at.is_(None)).count(),
        }
        filter_options = {
            "provinces": [
                {"id": p.id, "name": localized(p)}
                for p in Province.query.filter(Province.deleted_at.is_(None)).order_by(Province.name_en).all()
            ],
            "cities": [
                {"id": c.id, "name": localized(c), "province_id": c.province_id}
                for c in City.query.filter(City.deleted_at.is_(None)).order_by(City.name_en).all()
            ],
            "merchants": [
                {"id": m.id, "name": localized(m)}
                for m in Merchant.query.filter(Merchant.deleted_at.is_(None)).order_by(Merchant.name_en).all()
            ],
            "drivers": [
                {"id": d.id, "name": localized(d)}
                for d in Driver.query.filter(Driver.deleted_at.is_(None)).order_by(Driver.name_en).all()
            ],
            "posts": [
                {"id": p.id, "name": localized(p)}
                for p in Post.query.filter(Post.deleted_at.is_(None)).order_by(Post.name_en).all()
            ],
            "statuses": ORDER_STATUSES,
        }
        return render_template(
            "dashboard.html",
            report_catalog=get_report_catalog(),
            filter_options=filter_options,
            stats=stats,
            active="dashboard",
        )

    @app.route("/api/report/<report_key>")
    def api_report(report_key):
        """Build one dashboard report (multiple charts) with optional filters."""
        filters = {
            "province_id": request.args.get("province_id") or None,
            "city_id": request.args.get("city_id") or None,
            "merchant_id": request.args.get("merchant_id") or None,
            "driver_id": request.args.get("driver_id") or None,
            "post_id": request.args.get("post_id") or None,
            "status": request.args.get("status") or None,
            "date_from": request.args.get("date_from") or None,
            "date_to": request.args.get("date_to") or None,
            "preset": request.args.get("preset") or None,
        }
        report = build_report(report_key, filters)
        if report is None:
            abort(404)
        return jsonify(report)

    @app.route("/api/source/<path:key>")
    def api_source(key):
        """Return Python/JS source blocks for a dashboard UI piece (student peek)."""
        data = get_source(key)
        if data is None:
            abort(404)
        return jsonify(data)

    @app.route("/api/options/<source>")
    def api_options(source):
        """Searchable combobox options: [{id, label}, ...] — label follows active language."""
        if source not in OPTION_SOURCES:
            abort(404)
        model = OPTION_SOURCES[source]
        q = request.args.get("q", "").strip()
        query = model.query.filter(model.deleted_at.is_(None))
        if q:
            query = query.filter(
                or_(
                    model.name_en.like(f"%{q}%"),
                    model.name_ar.like(f"%{q}%"),
                    model.name_ckb.like(f"%{q}%"),
                )
            )
        rows = query.order_by(model.name_en.asc()).limit(30).all()
        return jsonify([{"id": r.id, "label": localized(r)} for r in rows])

    @app.route("/settings", methods=["GET"])
    def settings_page():
        return render_template("settings.html", active="settings")

    @app.route("/settings/lang/<lang>", methods=["POST", "GET"])
    def settings_lang(lang):
        if lang not in LANGS:
            abort(404)
        session["lang"] = lang
        flash(t("settings.saved"), "success")
        nxt = request.args.get("next") or request.referrer or url_for("settings_page")
        resp = make_response(redirect(nxt))
        return _set_pref_cookie(resp, COOKIE_LANG, lang)

    @app.route("/settings/theme/<theme>", methods=["POST", "GET"])
    def settings_theme(theme):
        if theme not in THEMES:
            abort(404)
        session["theme"] = theme
        flash(t("settings.saved"), "success")
        nxt = request.args.get("next") or request.referrer or url_for("settings_page")
        resp = make_response(redirect(nxt))
        return _set_pref_cookie(resp, COOKIE_THEME, theme)

    @app.route("/settings/source/<state>", methods=["POST", "GET"])
    def settings_source(state):
        """Toggle educational </> source-peek buttons (on/off)."""
        enabled = state in {"on", "1", "true", "yes"}
        session["show_source"] = "1" if enabled else "0"
        flash(t("settings.saved"), "success")
        nxt = request.args.get("next") or request.referrer or url_for("settings_page")
        resp = make_response(redirect(nxt))
        return _set_pref_cookie(resp, COOKIE_SHOW_SOURCE, "1" if enabled else "0")

    def _table_list(name, deleted_mode):
        meta = TABLES.get(name)
        if not meta:
            abort(404)

        model = meta["model"]
        q = request.args.get("q", "").strip()
        page = request.args.get("page", 1, type=int)
        per_page = app.config["PER_PAGE"]

        if deleted_mode:
            query = model.query.filter(model.deleted_at.isnot(None))
        else:
            query = model.query.filter(model.deleted_at.is_(None))

        filt = search_filter(model, meta["search"], q)
        if filt is not True:
            query = query.filter(filt)

        if deleted_mode:
            query = query.order_by(model.deleted_at.desc())
        else:
            query = query.order_by(model.id.asc())

        pagination = paginate_query(query, page, per_page)
        rows = [enrich_row(name, row) for row in pagination.items]
        if deleted_mode:
            for row in rows:
                row["deleted_at"] = row.get("deleted_at")

        endpoint = url_for("deleted_table" if deleted_mode else "table_page", name=name)
        pager = pagination_urls(endpoint, pagination.page, pagination.pages or 1, q=q)
        view_columns = list(meta["view_columns"])
        if deleted_mode:
            view_columns = view_columns + [{"key": "deleted_at", "label_key": "table.deleted_at"}]
        view_columns = translate_columns(view_columns)
        fields = translate_fields(meta["fields"])

        return render_template(
            "table.html",
            table_name=name,
            title=(
                f"{t('nav.deleted')} — {t(meta.get('title_key', 'table.' + name))}"
                if deleted_mode
                else t(meta.get("title_key", "table." + name))
            ),
            view_columns=view_columns,
            fields=fields,
            rows=rows,
            q=q,
            pager=pager,
            total=pagination.total,
            deleted_mode=deleted_mode,
            special=meta.get("special"),
            row_link=meta.get("row_link"),
            active="deleted" if deleted_mode else name,
        )

    @app.route("/table/<name>", methods=["GET"])
    def table_page(name):
        return _table_list(name, deleted_mode=False)

    @app.route("/table/<name>/create", methods=["POST"])
    def table_create(name):
        meta = TABLES.get(name)
        if not meta:
            abort(404)

        try:
            if meta.get("special") == "orders":
                order = Order(status="Pending")
                apply_form(order, request.form, meta["fields"])
                db.session.add(order)
                lines = parse_order_item_lines(request.form)
                apply_order_items(order, lines)
                db.session.commit()
                flash("Order created and stock updated.", "success")
            else:
                instance = meta["model"]()
                apply_form(instance, request.form, meta["fields"])
                db.session.add(instance)
                db.session.commit()
                flash(f"{meta['title']} created.", "success")
        except Exception as exc:
            db.session.rollback()
            flash(f"Create failed: {exc}", "error")
        return redirect(url_for("table_page", name=name, q=request.args.get("q", "")))

    @app.route("/table/<name>/<int:row_id>/update", methods=["POST"])
    def table_update(name, row_id):
        meta = TABLES.get(name)
        if not meta:
            abort(404)
        instance = meta["model"].query.get_or_404(row_id)
        if instance.deleted_at is not None:
            abort(400)
        try:
            if meta.get("special") == "orders":
                # Restore previous stock, replace line items, subtract again
                # (only if order is not Cancelled).
                was_cancelled = instance.status == "Cancelled"
                if not was_cancelled:
                    restore_order_stock(instance, reason="order_edit_restore")
                for oi in list(instance.items):
                    db.session.delete(oi)
                db.session.flush()
                apply_form(instance, request.form, meta["fields"])
                lines = parse_order_item_lines(request.form)
                if was_cancelled:
                    # Keep cancelled: set lines without subtracting
                    total = 0.0
                    db.session.flush()
                    for line in lines:
                        item = Item.query.get(line["item_id"])
                        qty = int(line["quantity"])
                        unit = float(item.price)
                        total += unit * qty
                        db.session.add(
                            OrderItem(
                                order=instance,
                                item_id=item.id,
                                quantity=qty,
                                unit_price=unit,
                                line_total=unit * qty,
                            )
                        )
                    instance.total_price = total
                    instance.status = "Cancelled"
                else:
                    apply_order_items(instance, lines, reason="order_edit_sale")
                db.session.commit()
                flash(f"Order #{row_id} updated.", "success")
            else:
                apply_form(instance, request.form, meta["fields"])
                db.session.commit()
                flash(f"{meta['title']} #{row_id} updated.", "success")
        except Exception as exc:
            db.session.rollback()
            flash(f"Update failed: {exc}", "error")
        return redirect(
            url_for(
                "table_page",
                name=name,
                q=request.args.get("q", ""),
                page=request.args.get("page", 1),
            )
        )

    @app.route("/table/<name>/<int:row_id>/delete", methods=["POST"])
    def table_delete(name, row_id):
        meta = TABLES.get(name)
        if not meta:
            abort(404)
        instance = meta["model"].query.get_or_404(row_id)
        # Soft-deleting an active order restores stock (same as cancel).
        if name == "orders" and instance.status != "Cancelled":
            try:
                restore_order_stock(instance, reason="order_soft_delete")
                instance.status = "Cancelled"
            except Exception:
                pass
        instance.soft_delete()
        db.session.commit()
        flash(f"{meta['title']} #{row_id} moved to deleted.", "success")
        return redirect(
            url_for(
                "table_page",
                name=name,
                q=request.args.get("q", ""),
                page=request.args.get("page", 1),
            )
        )

    @app.route("/orders/<int:row_id>/status", methods=["POST"])
    def order_status(row_id):
        order = Order.query.get_or_404(row_id)
        if order.deleted_at is not None:
            abort(400)
        new_status = request.form.get("status", "")
        try:
            set_order_status(order, new_status)
            db.session.commit()
            flash(f"Order #{row_id} status → {new_status}", "success")
        except Exception as exc:
            db.session.rollback()
            flash(f"Status change failed: {exc}", "error")
        return redirect(
            url_for(
                "table_page",
                name="orders",
                q=request.args.get("q", ""),
                page=request.args.get("page", 1),
            )
        )

    @app.route("/deleted")
    def deleted_hub():
        return render_template(
            "deleted_hub.html",
            counts=deleted_counts(),
            active="deleted",
        )

    @app.route("/deleted/<name>")
    def deleted_table(name):
        return _table_list(name, deleted_mode=True)

    @app.route("/deleted/<name>/<int:row_id>/restore", methods=["POST"])
    def table_restore(name, row_id):
        meta = TABLES.get(name)
        if not meta:
            abort(404)
        instance = meta["model"].query.get_or_404(row_id)
        instance.restore()
        db.session.commit()
        flash(f"{meta['title']} #{row_id} restored.", "success")
        return redirect(
            url_for(
                "deleted_table",
                name=name,
                q=request.args.get("q", ""),
                page=request.args.get("page", 1),
            )
        )

    @app.route("/items/<int:item_id>/stock-history")
    def stock_history(item_id):
        item = Item.query.get_or_404(item_id)
        q = request.args.get("q", "").strip()
        page = request.args.get("page", 1, type=int)
        per_page = app.config["PER_PAGE"]

        query = StockHistory.query.filter_by(item_id=item_id).order_by(
            StockHistory.created_at.desc()
        )
        if q:
            query = query.filter(
                or_(
                    StockHistory.reason.like(f"%{q}%"),
                    StockHistory.note.like(f"%{q}%"),
                )
            )
        pagination = paginate_query(query, page, per_page)
        rows = [r.to_dict() for r in pagination.items]
        pager = pagination_urls(
            url_for("stock_history", item_id=item_id),
            pagination.page,
            pagination.pages or 1,
            q=q,
        )
        return render_template(
            "stock_history.html",
            item=item,
            rows=rows,
            q=q,
            pager=pager,
            total=pagination.total,
            active="items",
        )


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    print("Postal Dashboard -> http://localhost:3000")
    app.run(debug=True, host="localhost", port=3000)
