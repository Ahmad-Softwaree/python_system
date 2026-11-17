"""
Postal System — Flask dashboard with MySQL ORM CRUD.
Entry: python app.py  →  http://localhost:3000
"""

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy import or_

from charts import build_chart_by_id, get_chart_catalog
from config import Config
from extensions import db
from models import (
    ORDER_STATUSES,
    City,
    Driver,
    Item,
    Merchant,
    Order,
    OrderItem,
    Post,
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
from table_meta import OPTION_SOURCES, TABLES, nav_tables


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    @app.context_processor
    def inject_globals():
        return {
            "tables": nav_tables(),
            "order_statuses": ORDER_STATUSES,
            "format_iqd": format_iqd,
        }

    register_routes(app)
    return app


def register_routes(app):
    @app.route("/")
    def dashboard():
        chart_catalog = get_chart_catalog()
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
        return render_template(
            "dashboard.html",
            chart_catalog=chart_catalog,
            stats=stats,
            active="dashboard",
        )

    @app.route("/api/chart/<int:chart_id>")
    def api_chart(chart_id):
        chart = build_chart_by_id(chart_id)
        if chart is None:
            abort(404)
        return jsonify(chart)

    @app.route("/api/options/<source>")
    def api_options(source):
        """Searchable combobox options: [{id, label}, ...]."""
        if source not in OPTION_SOURCES:
            abort(404)
        model, label_attr = OPTION_SOURCES[source]
        q = request.args.get("q", "").strip()
        query = model.query.filter(model.deleted_at.is_(None))
        if q:
            column = getattr(model, label_attr)
            query = query.filter(column.like(f"%{q}%"))
        rows = query.order_by(getattr(model, label_attr).asc()).limit(30).all()
        return jsonify([{"id": r.id, "label": getattr(r, label_attr)} for r in rows])

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
            view_columns = view_columns + [{"key": "deleted_at", "label": "Deleted At"}]

        return render_template(
            "table.html",
            table_name=name,
            title=(f"Deleted — {meta['title']}" if deleted_mode else meta["title"]),
            view_columns=view_columns,
            fields=meta["fields"],
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
