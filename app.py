from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "database.db"

admin_username = "Volkodavov"
admin_pass = "qwerty12345"


def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Товары (минимум полей)
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    # Секреты (оставляем)
    cursor.execute("""
        CREATE TABLE app_secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            secret TEXT NOT NULL
        )
    """)

    test_products = [
        ("Кофе в зёрнах 1 кг", "Напитки", 1299.90),
        ("Чай улун 250 г", "Напитки", 499.00),
        ("Клавиатура механическая", "Техника", 5590.00),
        ("Мышь беспроводная", "Техника", 1690.00),
        ("Шоколад 85% какао", "Еда", 219.00),
    ]
    for name, category, price in test_products:
        cursor.execute(
            "INSERT INTO products (name, category, price) VALUES (?, ?, ?)",
            (name, category, price),
        )

    test_secrets = [
        ("admin_username", admin_username),
        ("admin_pass", admin_pass),
    ]
    for name, secret in test_secrets:
        cursor.execute(
            "INSERT INTO app_secrets (name, secret) VALUES (?, ?)",
            (name, secret),
        )

    conn.commit()
    conn.close()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    """Каталог товаров (УЯЗВИМО к SQLi в GET)"""
    query = request.args.get("q", "")
    products = []
    error = None

    message = request.args.get("message")
    message_type = request.args.get("message_type", "info")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # TODO ⚠️ УЯЗВИМОСТЬ: конкатенация пользовательского ввода
        sql = (
            f"SELECT name, category, price FROM products WHERE name LIKE '%{query}%' ORDER BY rowid;"
        )

        cursor.execute(sql)
        products = cursor.fetchall()
        conn.close()
    except Exception as e:
        error = f"SQL Error: {str(e)}"

    return render_template(
        "index.html",
        products=products,
        error=error,
        message=message,
        message_type=message_type,
        request=request,
    )


@app.route("/create", methods=["POST"])
def create():
    """Добавление товара (УЯЗВИМО к SQLi в POST)"""
    name = request.form.get("name", "")
    category = request.form.get("category", "")
    price = request.form.get("price", "")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # TODO ⚠️ УЯЗВИМОСТЬ: конкатенация в INSERT (price без кавычек)
        sql = (
            f"INSERT INTO products (name, category, price) VALUES ('{name}', '{category}', {price})"
        )

        cursor.execute(sql)
        conn.commit()
        conn.close()

        message = f"✅ Товар «{name}» добавлен"
        message_type = "success"
    except Exception as e:
        message = f"❌ Ошибка: {str(e)}"
        message_type = "error"

    return redirect(url_for("index", _anchor="create", message=message, message_type=message_type))


@app.errorhandler(404)
def not_found(e):
    return redirect(url_for("index"))


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()

    app.run(debug=True, host="127.0.0.1", port=5000)
