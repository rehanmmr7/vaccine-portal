from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import date

app = Flask(__name__)
DB = "database.db"

# ---------- DATABASE SETUP ----------
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS vaccines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        purpose TEXT,
        disease TEXT,
        age_group TEXT,
        dosage TEXT,
        category TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS centres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vaccine_id INTEGER,
        centre_name TEXT,
        city TEXT,
        address TEXT,
        phone TEXT,
        price REAL,
        availability TEXT,
        last_updated TEXT,
        FOREIGN KEY (vaccine_id) REFERENCES vaccines (id)
    )''')
    conn.commit()

    # Add sample data only if empty
    count = conn.execute("SELECT COUNT(*) FROM vaccines").fetchone()[0]
    if count == 0:
        conn.execute("INSERT INTO vaccines (name, purpose, disease, age_group, dosage, category) VALUES (?,?,?,?,?,?)",
                     ("Covishield", "Prevents COVID-19", "COVID-19", "18+ years", "2 doses, 12 weeks apart", "Routine"))
        conn.execute("INSERT INTO vaccines (name, purpose, disease, age_group, dosage, category) VALUES (?,?,?,?,?,?)",
                     ("Rabies Vaccine", "Prevents Rabies after dog bite", "Rabies", "All ages", "5 doses on Day 0,3,7,14,28", "Routine"))
        conn.execute("INSERT INTO vaccines (name, purpose, disease, age_group, dosage, category) VALUES (?,?,?,?,?,?)",
                     ("Yellow Fever", "Required for travel to Africa / South America", "Yellow Fever", "9 months+", "1 dose, valid for lifetime", "Travel"))
        conn.commit()

        conn.execute("INSERT INTO centres (vaccine_id, centre_name, city, address, phone, price, availability, last_updated) VALUES (?,?,?,?,?,?,?,?)",
                     (1, "Belagavi District Hospital", "Belagavi", "Station Road, Belagavi", "0831-1234567", 780, "Available", str(date.today())))
        conn.execute("INSERT INTO centres (vaccine_id, centre_name, city, address, phone, price, availability, last_updated) VALUES (?,?,?,?,?,?,?,?)",
                     (2, "Belagavi District Hospital", "Belagavi", "Station Road, Belagavi", "0831-1234567", 350, "Available", str(date.today())))
        conn.execute("INSERT INTO centres (vaccine_id, centre_name, city, address, phone, price, availability, last_updated) VALUES (?,?,?,?,?,?,?,?)",
                     (2, "KLE Hospital", "Belagavi", "Nehru Nagar, Belagavi", "0831-7654321", 450, "Limited Stock", str(date.today())))
        conn.execute("INSERT INTO centres (vaccine_id, centre_name, city, address, phone, price, availability, last_updated) VALUES (?,?,?,?,?,?,?,?)",
                     (3, "Belagavi Travel Health Clinic", "Belagavi", "College Road, Belagavi", "0831-2345678", 1800, "Available", str(date.today())))
        conn.commit()
    conn.close()

init_db()

# ---------- USER PAGES ----------
@app.route("/")
def home():
    search = request.args.get("search", "")
    city = request.args.get("city", "")
    category = request.args.get("category", "")

    conn = get_db()
    query = "SELECT * FROM vaccines WHERE 1=1"
    params = []
    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")
    if category:
        query += " AND category = ?"
        params.append(category)
    vaccines = conn.execute(query, params).fetchall()
    conn.close()
    return render_template("index.html", vaccines=vaccines, search=search, city=city, category=category)

@app.route("/vaccine/<int:vaccine_id>")
def vaccine_detail(vaccine_id):
    city = request.args.get("city", "")
    conn = get_db()
    vaccine = conn.execute("SELECT * FROM vaccines WHERE id=?", (vaccine_id,)).fetchone()
    if city:
        centres = conn.execute("SELECT * FROM centres WHERE vaccine_id=? AND city LIKE ?", (vaccine_id, f"%{city}%")).fetchall()
    else:
        centres = conn.execute("SELECT * FROM centres WHERE vaccine_id=?", (vaccine_id,)).fetchall()
    conn.close()
    return render_template("vaccine.html", vaccine=vaccine, centres=centres, city=city)

@app.route("/centres")
def all_centres():
    city = request.args.get("city", "")
    conn = get_db()
    if city:
        centres = conn.execute("SELECT centres.*, vaccines.name as vaccine_name FROM centres JOIN vaccines ON centres.vaccine_id = vaccines.id WHERE centres.city LIKE ?", (f"%{city}%",)).fetchall()
    else:
        centres = conn.execute("SELECT centres.*, vaccines.name as vaccine_name FROM centres JOIN vaccines ON centres.vaccine_id = vaccines.id").fetchall()
    conn.close()
    return render_template("centres.html", centres=centres, city=city)

# ---------- ADMIN PAGES ----------
@app.route("/admin")
def admin():
    conn = get_db()
    vaccines = conn.execute("SELECT * FROM vaccines").fetchall()
    centres = conn.execute("SELECT centres.*, vaccines.name as vaccine_name FROM centres JOIN vaccines ON centres.vaccine_id = vaccines.id").fetchall()
    conn.close()
    return render_template("admin.html", vaccines=vaccines, centres=centres)

@app.route("/admin/add_vaccine", methods=["POST"])
def add_vaccine():
    conn = get_db()
    conn.execute("INSERT INTO vaccines (name, purpose, disease, age_group, dosage, category) VALUES (?,?,?,?,?,?)",
                 (request.form["name"], request.form["purpose"], request.form["disease"], request.form["age_group"], request.form["dosage"], request.form["category"]))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/admin/add_centre", methods=["POST"])
def add_centre():
    conn = get_db()
    conn.execute("INSERT INTO centres (vaccine_id, centre_name, city, address, phone, price, availability, last_updated) VALUES (?,?,?,?,?,?,?,?)",
                 (request.form["vaccine_id"], request.form["centre_name"], request.form["city"], request.form["address"], request.form["phone"], request.form["price"], request.form["availability"], str(date.today())))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/admin/delete_vaccine/<int:id>")
def delete_vaccine(id):
    conn = get_db()
    conn.execute("DELETE FROM vaccines WHERE id=?", (id,))
    conn.execute("DELETE FROM centres WHERE vaccine_id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/admin/delete_centre/<int:id>")
def delete_centre(id):
    conn = get_db()
    conn.execute("DELETE FROM centres WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


from datetime import date, timedelta

@app.route("/child-schedule", methods=["GET", "POST"])
def child_schedule():
    schedule = None
    dob_str = ""
    child_name = ""
    if request.method == "POST":
        child_name = request.form.get("child_name", "")
        dob_str = request.form.get("dob", "")
        if dob_str:
            dob = date.fromisoformat(dob_str)
            items = [
                ("At Birth", 0, "BCG, OPV-0, Hepatitis B-1"),
                ("6 Weeks", 42, "Pentavalent-1, Rotavirus-1, PCV-1, OPV-1, IPV-1"),
                ("10 Weeks", 70, "Pentavalent-2, Rotavirus-2, PCV-2, OPV-2"),
                ("14 Weeks", 98, "Pentavalent-3, Rotavirus-3, PCV-3, OPV-3, IPV-2"),
                ("6 Months", 182, "Hepatitis B-3"),
                ("9 Months", 273, "Measles-Rubella-1, JE-1, PCV Booster"),
                ("12 Months", 365, "Hepatitis A-1, Typhoid"),
                ("15 Months", 456, "MMR-1, Varicella-1, PCV Booster"),
                ("16-18 Months", 500, "DPT Booster-1, IPV Booster, Hib Booster"),
                ("2 Years", 730, "Hepatitis A-2, Typhoid Booster"),
                ("5 Years", 1825, "DPT Booster-2"),
                ("10 Years", 3650, "Td (Tetanus)"),
                ("16 Years", 5840, "Td (Tetanus)"),
            ]
            schedule = []
            today = date.today()
            for label, days, vaccines in items:
                due = dob + timedelta(days=days)
                if due < today:
                    status = "Done / Overdue - Check with doctor"
                    color = "red"
                elif (due - today).days <= 7:
                    status = "DUE NOW"
                    color = "orange"
                else:
                    status = f"In {(due - today).days} days"
                    color = "green"
                schedule.append({"label": label, "due": due.strftime("%d %b %Y"), "vaccines": vaccines, "status": status, "color": color})
    return render_template("child_schedule.html", schedule=schedule, dob=dob_str, child_name=child_name)

import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)