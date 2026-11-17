"""
Postal System — Flask dashboard with MySQL ORM CRUD.

Entry point: python app.py  →  http://localhost:3000

Architecture for presentation:
- create_app()      factory that builds the Flask app
- register_routes() all URL endpoints
- models + services + table_meta do the heavy lifting
"""

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from charts import build_all_charts
from config import Config
from extensions import db
from models import City, Driver, Item, Merchant, Order, Post
from services import (
    apply_form,
    deleted_counts,
    paginate_query,
    pagination_urls,
    search_filter,
)
from table_meta import TABLES, nav_tables


def create_app():
    """
    Application factory pattern.
    Why? seed.py can create an app context to talk to the DB
    without calling app.run() (which would start the web server).
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    @app.context_processor
    def inject_globals():
        # Makes `tables` available in EVERY template (sidebar links)
        # without passing it manually from each route.
        return {"tables": nav_tables()}

    register_routes(app)
    return app


def register_routes(app):
    @app.route("/")
    def dashboard():
        # Charts are generated on each request from live (non-deleted) DB data.
        charts = build_all_charts()
        stats = {
            "orders": Order.query.filter(Order.deleted_at.is_(None)).count(),
            "delivered": Order.query.filter(
                Order.deleted_at.is_(None), Order.status == "Delivered"
            ).count(),
            "revenue": sum(
                o.total_price
                for o in Order.query.filter(Order.deleted_at.is_(None)).all()
            ),
            "drivers": Driver.query.filter(Driver.deleted_at.is_(None)).count(),
            "merchants": Merchant.query.filter(Merchant.deleted_at.is_(None)).count(),
            "posts": Post.query.filter(Post.deleted_at.is_(None)).count(),
            "items": Item.query.filter(Item.deleted_at.is_(None)).count(),
            "cities": City.query.filter(City.deleted_at.is_(None)).count(),
        }
        return render_template(
            "dashboard.html",
            charts=charts,
            stats=stats,
            active="dashboard",
        )

    @app.route("/table/<name>", methods=["GET"])
    def table_page(name):
        """
        One route serves ALL entity tables.
        `name` is a key from table_meta.TABLES (e.g. 'drivers', 'orders').
        """
        meta = TABLES.get(name)
        if not meta:
            abort(404)

        model = meta["model"]
        q = request.args.get("q", "").strip()
        page = request.args.get("page", 1, type=int)
        per_page = app.config["PER_PAGE"]

        # Active rows only: soft-deleted rows are hidden here.
        query = model.query.filter(model.deleted_at.is_(None))
        filt = search_filter(model, meta["search"], q)
        if filt is not True:
            query = query.filter(filt)
        query = query.order_by(model.id.asc())
        pagination = paginate_query(query, page, per_page)

        rows = [row.to_dict() for row in pagination.items]
        # pagination.pages can be 0 when the table is empty → treat as 1 for UI.
        pager = pagination_urls(
            url_for("table_page", name=name),
            pagination.page,
            pagination.pages or 1,
            q=q,
        )

        return render_template(
            "table.html",
            table_name=name,
            title=meta["title"],
            columns=meta["columns"],
            fields=meta["fields"],
            rows=rows,
            q=q,
            pager=pager,
            total=pagination.total,
            deleted_mode=False,  # show Add / Edit / Delete buttons
            active=name,
        )

    @app.route("/table/<name>/create", methods=["POST"])
    def table_create(name):
        meta = TABLES.get(name)
        if not meta:
            abort(404)
        instance = meta["model"]()
        try:
            apply_form(instance, request.form, meta["fields"])
            db.session.add(instance)
            db.session.commit()
            flash(f"{meta['title']} created.", "success")
        except Exception as exc:
            # Roll back so a failed insert does not leave a broken transaction open.
            db.session.rollback()
            flash(f"Create failed: {exc}", "error")
        return redirect(url_for("table_page", name=name, q=request.args.get("q", "")))

    @app.route("/table/<name>/<int:row_id>/update", methods=["POST"])
    def table_update(name, row_id):
        meta = TABLES.get(name)
        if not meta:
            abort(404)
        instance = meta["model"].query.get_or_404(row_id)
        # Do not allow editing a soft-deleted row from the active page.
        if instance.deleted_at is not None:
            abort(400)
        try:
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
        """Soft delete: set deleted_at, do NOT remove the MySQL row."""
        meta = TABLES.get(name)
        if not meta:
            abort(404)
        instance = meta["model"].query.get_or_404(row_id)
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

    @app.route("/deleted")
    def deleted_hub():
        # Cards for each table + how many soft-deleted rows they have.
        counts = deleted_counts()
        return render_template(
            "deleted_hub.html",
            counts=counts,
            active="deleted",
        )

    @app.route("/deleted/<name>")
    def deleted_table(name):
        """Same table.html template, but deleted_mode=True → Restore button."""
        meta = TABLES.get(name)
        if not meta:
            abort(404)

        model = meta["model"]
        q = request.args.get("q", "").strip()
        page = request.args.get("page", 1, type=int)
        per_page = app.config["PER_PAGE"]

        query = model.query.filter(model.deleted_at.isnot(None))
        filt = search_filter(model, meta["search"], q)
        if filt is not True:
            query = query.filter(filt)
        query = query.order_by(model.deleted_at.desc())
        pagination = paginate_query(query, page, per_page)

        rows = [row.to_dict() for row in pagination.items]
        pager = pagination_urls(
            url_for("deleted_table", name=name),
            pagination.page,
            pagination.pages or 1,
            q=q,
        )

        return render_template(
            "table.html",
            table_name=name,
            title=f"Deleted — {meta['title']}",
            columns=meta["columns"] + ["deleted_at"],
            fields=meta["fields"],
            rows=rows,
            q=q,
            pager=pager,
            total=pagination.total,
            deleted_mode=True,
            active="deleted",
        )

    @app.route("/deleted/<name>/<int:row_id>/restore", methods=["POST"])
    def table_restore(name, row_id):
        """Undo soft delete: deleted_at = NULL → row appears in active table again."""
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


# Module-level app used by `python app.py` and by Flask's reloader.
app = create_app()


if __name__ == "__main__":
    with app.app_context():
        # Safety net: create missing tables if someone skipped seed.py.
        db.create_all()
    print("Postal Dashboard -> http://localhost:3000")
    app.run(debug=True, host="localhost", port=3000)
