import os, sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "fsuumc.db")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-before-public-hosting")

MODES = ["Vanilla", "UHC", "Pot", "NethOP", "SMP", "Sword", "Axe", "Mace"]
TIERS = ["HT1", "LT1", "HT2", "LT2", "HT3", "LT3", "HT4", "LT4", "HT5", "LT5"]
POINTS = {"HT1":60, "LT1":45, "HT2":30, "LT2":20, "HT3":10, "LT3":6, "HT4":4, "LT4":3, "HT5":2, "LT5":1}
TITLES = [
    (400, "Combat Grandmaster", "grandmaster"),
    (250, "Combat Master", "master"),
    (100, "Combat Ace", "ace"),
    (50, "Combat Specialist", "specialist"),
    (20, "Combat Cadet", "cadet"),
    (10, "Combat Novice", "novice"),
    (0, "Rookie", "rookie"),
]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            region TEXT DEFAULT '',
            vanilla TEXT DEFAULT '', uhc TEXT DEFAULT '', pot TEXT DEFAULT '',
            nethop TEXT DEFAULT '', smp TEXT DEFAULT '', sword TEXT DEFAULT '',
            axe TEXT DEFAULT '', mace TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        )""")
        con.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL
        )""")
        con.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('announcement','Welcome to the FSUUMC PvP Rankings!')")
init_db()

def mode_key(mode):
    return {"Vanilla":"vanilla","UHC":"uhc","Pot":"pot","NethOP":"nethop","SMP":"smp","Sword":"sword","Axe":"axe","Mace":"mace"}[mode]

def score(player):
    total = 0
    for mode in MODES:
        tier = player[mode_key(mode)]
        if tier in POINTS:
            total += POINTS[tier]
    return total

def title_for(points):
    for threshold, label, slug in TITLES:
        if points >= threshold:
            return label, slug
    return "Rookie", "rookie"

def all_players():
    with db() as con:
        rows = con.execute("SELECT * FROM players").fetchall()
    players = []
    for row in rows:
        p = dict(row)
        p["points"] = score(p)
        p["title"], p["title_slug"] = title_for(p["points"])
        p["ranked_modes"] = sum(1 for m in MODES if p[mode_key(m)] in POINTS)
        players.append(p)
    players.sort(key=lambda p: (-p["points"], p["username"].lower()))
    return players

def announcement():
    with db() as con:
        row = con.execute("SELECT value FROM settings WHERE key='announcement'").fetchone()
    return row["value"] if row else ""

def owner_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("owner"):
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapped

@app.context_processor
def common():
    return {"MODES": MODES, "TIERS": TIERS, "POINTS": POINTS, "mode_key": mode_key}

@app.route("/")
def home():
    return render_template("index.html", players=all_players()[:10], announcement=announcement(), modes=MODES, tiers=TIERS)

@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html", players=all_players())

@app.route("/player/<int:player_id>")
def player_profile(player_id):
    with db() as con:
        row = con.execute("SELECT * FROM players WHERE id=?", (player_id,)).fetchone()
    if not row:
        abort(404)
    p = dict(row)
    p["points"] = score(p)
    p["title"], p["title_slug"] = title_for(p["points"])
    return render_template("player.html", player=p, modes=MODES)

@app.route("/tiers/<mode>/<tier>")
def tier_players(mode, tier):
    if mode not in MODES or tier not in TIERS:
        abort(404)
    key = mode_key(mode)
    players = [p for p in all_players() if p[key] == tier]
    return render_template("tier_players.html", mode=mode, tier=tier, players=players)

@app.route("/mode/<mode>")
def mode_page(mode):
    if mode not in MODES:
        abort(404)
    key = mode_key(mode)
    players = [p for p in all_players() if p[key] in TIERS]
    return render_template("mode.html", mode=mode, players=players)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        stored = os.environ.get("OWNER_PASSWORD_HASH", "")
        password = request.form.get("password", "")
        if stored and check_password_hash(stored, password):
            session["owner"] = True
            return redirect(request.args.get("next") or url_for("admin"))
        flash("Login failed. Check your password and OWNER_PASSWORD_HASH setup.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/admin")
@owner_required
def admin():
    return render_template("admin.html", players=all_players(), announcement=announcement())

@app.route("/admin/player", methods=["POST"])
@owner_required
def save_player():
    username = request.form.get("username","").strip()
    if not username:
        flash("Minecraft username is required.", "error")
        return redirect(url_for("admin"))
    values = [request.form.get(mode_key(m), "") for m in MODES]
    if any(v and v not in TIERS for v in values):
        flash("Please choose a valid tier.", "error")
        return redirect(url_for("admin"))
    region = request.form.get("region","").strip()
    notes = request.form.get("notes","").strip()
    with db() as con:
        try:
            con.execute("""INSERT INTO players(username,region,vanilla,uhc,pot,nethop,smp,sword,axe,mace,notes)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(username) DO UPDATE SET region=excluded.region, vanilla=excluded.vanilla,
            uhc=excluded.uhc,pot=excluded.pot,nethop=excluded.nethop,smp=excluded.smp,
            sword=excluded.sword,axe=excluded.axe,mace=excluded.mace,notes=excluded.notes""",
            [username,region]+values+[notes])
            flash(f"Saved {username}.", "success")
        except sqlite3.Error:
            flash("Could not save this player.", "error")
    return redirect(url_for("admin"))

@app.route("/admin/delete/<int:player_id>", methods=["POST"])
@owner_required
def delete_player(player_id):
    with db() as con:
        con.execute("DELETE FROM players WHERE id=?", (player_id,))
    flash("Player deleted.", "success")
    return redirect(url_for("admin"))

@app.route("/admin/announcement", methods=["POST"])
@owner_required
def save_announcement():
    value = request.form.get("announcement","").strip()
    with db() as con:
        con.execute("INSERT INTO settings(key,value) VALUES('announcement',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (value,))
    flash("Announcement updated.", "success")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
