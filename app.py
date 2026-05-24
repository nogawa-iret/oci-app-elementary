import os
from datetime import datetime, timezone

import oracledb
from flask import Flask, abort, render_template, request


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["APP_NAME"] = os.getenv("APP_NAME", "OCI Training Public Site")

    @app.get("/")
    def index():
        category = request.args.get("category", "").strip()
        categories = fetch_categories()
        contents = fetch_published_contents(category or None)
        return render_template(
            "index.html",
            app_name=app.config["APP_NAME"],
            categories=categories,
            contents=contents,
            selected_category=category,
        )

    @app.get("/content/<int:content_id>")
    def content_detail(content_id: int):
        content = fetch_content(content_id)
        if content is None:
            abort(404)
        return render_template("detail.html", app_name=app.config["APP_NAME"], content=content)

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "application": app.config["APP_NAME"],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/db-health")
    def db_health():
        with get_connection() as connection:
            with connection.cursor() as cursor:
                value = cursor.execute("select 1 from dual").fetchone()[0]
        return {"status": "ok", "database": value}

    return app


def get_connection():
    user = require_env("DB_USER")
    password = require_env("DB_PASSWORD")
    dsn = require_env("DB_DSN")
    return oracledb.connect(user=user, password=password, dsn=dsn)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required.")
    return value


def fetch_categories():
    sql = """
        select category_code, category_name
        from categories
        where is_active = 'Y'
        order by display_order, category_name
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            return [
                {"code": row[0], "name": row[1]}
                for row in cursor.fetchall()
            ]


def fetch_published_contents(category_code: str | None = None):
    sql = """
        select
            c.content_id,
            c.title,
            c.summary,
            c.published_at,
            cat.category_code,
            cat.category_name
        from public_contents c
        join categories cat on cat.category_id = c.category_id
        where c.status = 'PUBLISHED'
          and (:category_code is null or cat.category_code = :category_code)
        order by c.published_at desc, c.content_id desc
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, category_code=category_code)
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "summary": row[2],
                    "published_at": row[3],
                    "category_code": row[4],
                    "category_name": row[5],
                }
                for row in cursor.fetchall()
            ]


def fetch_content(content_id: int):
    sql = """
        select
            c.content_id,
            c.title,
            c.summary,
            c.body,
            c.published_at,
            cat.category_name
        from public_contents c
        join categories cat on cat.category_id = c.category_id
        where c.status = 'PUBLISHED'
          and c.content_id = :content_id
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            row = cursor.execute(sql, content_id=content_id).fetchone()
            if row is None:
                return None
            return {
                "id": row[0],
                "title": row[1],
                "summary": row[2],
                "body": row[3].read() if hasattr(row[3], "read") else row[3],
                "published_at": row[4],
                "category_name": row[5],
            }


app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", "8000")),
    )
