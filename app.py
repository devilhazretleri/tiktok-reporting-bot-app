from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config["DATABASE"] = "reports.db"

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = sqlite3.connect(app.config["DATABASE"])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_name TEXT NOT NULL,
            target_url TEXT,
            target_type TEXT,
            reason TEXT NOT NULL,
            urgency TEXT DEFAULT 'medium',
            evidence_links TEXT,
            status TEXT DEFAULT 'new',
            notes TEXT,
            created_at TEXT NOT NULL
        )
    """)
    db.commit()

@app.route("/")
def index():
    db = get_db()
    cases = db.execute("""
        SELECT * FROM cases
        ORDER BY created_at DESC
    """).fetchall()
    return render_template("index.html", cases=cases)

@app.route("/case/<int:case_id>")
def detail(case_id):
    db = get_db()
    case = db.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    if case is None:
        return redirect(url_for("index"))
    return render_template("detail.html", case=case)

@app.route("/add", methods=["POST"])
def add_case():
    creator_name = request.form.get("creator_name", "").strip()
    target_url = request.form.get("target_url", "").strip()
    target_type = request.form.get("target_type", "profile")
    reason = request.form.get("reason", "").strip()
    urgency = request.form.get("urgency", "medium")
    evidence_links = request.form.get("evidence_links", "").strip()
    notes = request.form.get("notes", "").strip()

    if not creator_name or not reason:
        return redirect(url_for("index"))

    db = get_db()
    db.execute("""
        INSERT INTO cases (creator_name, target_url, target_type, reason, urgency, evidence_links, status, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'new', ?, ?)
    """, (creator_name, target_url, target_type, reason, urgency, evidence_links, notes, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
    db.commit()
    return redirect(url_for("index"))

@app.route("/update/<int:case_id>", methods=["POST"])
def update_case(case_id):
    status = request.form.get("status", "new")
    notes = request.form.get("notes", "").strip()
    db = get_db()
    db.execute("""
        UPDATE cases
        SET status = ?, notes = ?
        WHERE id = ?
    """, (status, notes, case_id))
    db.commit()
    return redirect(url_for("detail", case_id=case_id))

@app.route("/delete/<int:case_id>")
def delete_case(case_id):
    db = get_db()
    db.execute("DELETE FROM cases WHERE id = ?", (case_id,))
    db.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
