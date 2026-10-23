import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this-secret-key")

# Render: set DB_PATH=/var/data/users.db only if using a persistent disk.
# Without that, SQLite is fine for a demo but its data may reset on redeploy/restart.
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "users.db"))


def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
                    CHECK (role IN ('admin', 'user'))
            )
        """)
        g.db.commit()
        # Bootstrap the first admin only when no admin account exists.
        admin = g.db.execute(
            "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()
        if admin is None:
            username = os.environ.get("ADMIN_USERNAME", "admin")
            password = os.environ.get("ADMIN_PASSWORD", "12345")
            g.db.execute(
                "INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, 'admin')",
                (username, generate_password_hash(password))
            )
            g.db.commit()
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Akses ditolak. Fitur ini hanya untuk admin.", "danger")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("Hak akses: Izinkan masuk Aplikasi Db", "success")
            return redirect(url_for("dashboard"))

        flash("Akses ditolak! Username atau password salah.", "danger")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    users = db.execute(
        "SELECT id, username, role FROM users ORDER BY id"
    ).fetchall()
    return render_template("dashboard.html", users=users)


@app.route("/users/add", methods=["POST"])
@admin_required
def add_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "user")

    if len(username) < 3:
        flash("Username minimal 3 karakter.", "danger")
    elif len(password) < 5:
        flash("Password minimal 5 karakter.", "danger")
    elif role not in ("admin", "user"):
        flash("Hak akses tidak valid.", "danger")
    else:
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), role)
            )
            db.commit()
            flash(f"Akun '{username}' berhasil ditambahkan.", "success")
        except sqlite3.IntegrityError:
            flash("Username sudah digunakan.", "danger")

    return redirect(url_for("dashboard"))


@app.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    db = get_db()
    target = db.execute(
        "SELECT id, username, role FROM users WHERE id = ?", (user_id,)
    ).fetchone()

    if target is None:
        flash("Akun tidak ditemukan.", "danger")
    elif target["id"] == session["user_id"]:
        flash("Admin yang sedang login tidak dapat menghapus akunnya sendiri.", "warning")
    elif target["role"] == "admin":
        admin_count = db.execute(
            "SELECT COUNT(*) AS n FROM users WHERE role = 'admin'"
        ).fetchone()["n"]
        if admin_count <= 1:
            flash("Minimal harus ada satu akun admin.", "warning")
        else:
            db.execute("DELETE FROM users WHERE id = ?", (user_id,))
            db.commit()
            flash(f"Akun '{target['username']}' berhasil dihapus.", "success")
    else:
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
        flash(f"Akun '{target['username']}' berhasil dihapus.", "success")

    return redirect(url_for("dashboard"))


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("Kamu sudah logout.", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
