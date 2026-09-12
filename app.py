from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Secret key used for login sessions
app.config["SECRET_KEY"] = "spendwise-development-key"

DATABASE = "spendwise.db"


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            user_id INTEGER,
            type TEXT DEFAULT 'OUT'
        )
    """)

    # Check existing columns
    columns = conn.execute(
        "PRAGMA table_info(expenses)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    # Add user_id if it doesn't exist
    if "user_id" not in column_names:
        conn.execute(
            "ALTER TABLE expenses ADD COLUMN user_id INTEGER"
        )

    # Add type if it doesn't exist
    if "type" not in column_names:
        conn.execute(
            "ALTER TABLE expenses ADD COLUMN type TEXT DEFAULT 'OUT'"
        )

    conn.commit()
    conn.close()

# ---------------- LOGIN SYSTEM ----------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):

    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email


@login_manager.user_loader
def load_user(user_id):

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    conn.close()

    if user:
        return User(
            user["id"],
            user["name"],
            user["email"]
        )

    return None


# ---------------- HOME ----------------

@app.route("/")
@login_required
def home():

    return render_template(
        "index.html",
        user_name=current_user.name
    )


# ---------------- SIGNUP ----------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            return "Please fill all fields."

        hashed_password = generate_password_hash(password)

        conn = get_db()

        try:

            conn.execute(
                """
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, hashed_password)
            )

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return "An account with this email already exists."

        conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            user_object = User(
                user["id"],
                user["name"],
                user["email"]
            )

            login_user(user_object)

            return redirect(url_for("home"))

        return "Invalid email or password."

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))


# ---------------- GET EXPENSES ----------------

@app.route("/api/expenses", methods=["GET"])
@login_required
def get_expenses():

    conn = get_db()

    expenses = conn.execute(
        """
        SELECT *
        FROM expenses
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (current_user.id,)
    ).fetchall()

    conn.close()

    return jsonify([
        dict(expense)
        for expense in expenses
    ])


# ---------------- ADD EXPENSE ----------------

@app.route("/api/expenses", methods=["POST"])
@login_required
def add_expense():
    data = request.get_json()

    title = data.get("title")
    amount = data.get("amount")
    category = data.get("category")
    transaction_type = data.get("type", "OUT")

    if not title or not amount or not category:
        return jsonify({"error": "Please fill all fields"}), 400

    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"error": "Amount must be a number"}), 400

    if transaction_type not in ["IN", "OUT"]:
        transaction_type = "OUT"

    date = datetime.now().strftime("%Y-%m-%d")

    conn = get_db()

    conn.execute(
        """
        INSERT INTO expenses
        (title, amount, category, date, user_id, type)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            amount,
            category,
            date,
            current_user.id,
            transaction_type
        )
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Transaction added successfully"})

# ---------------- DELETE EXPENSE ----------------

@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
@login_required
def delete_expense(expense_id):

    conn = get_db()

    conn.execute(
        """
        DELETE FROM expenses
        WHERE id = ? AND user_id = ?
        """,
        (
            expense_id,
            current_user.id
        )
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Expense deleted"
    })


# ---------------- START APP ----------------

if __name__ == "__main__":
    create_database()
    app.run(debug=True)