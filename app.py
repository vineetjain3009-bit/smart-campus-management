import os
import sqlite3
from contextlib import closing
from datetime import date, timedelta
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database" / "campus.db"
DEPARTMENTS = ["Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil"]
SUBJECTS = ["Data Structures", "Database Systems", "Web Technologies", "Computer Networks", "Software Engineering"]
VALID_ATTENDANCE = {"Present", "Absent"}
VALID_ASSIGNMENT_STATUS = {"Pending", "Submitted", "Overdue"}

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "change-this-secret-before-production"),
    DATABASE=str(DATABASE_PATH),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def fetch_one_or_404(query, params=()):
    row = get_db().execute(query, params).fetchone()
    if row is None:
        abort(404)
    return row


def db_execute(query, params=()):
    db = get_db()
    cursor = db.execute(query, params)
    db.commit()
    return cursor


def attendance_percentage(student_db_id):
    row = get_db().execute(
        """SELECT COUNT(*) AS total,
                  COALESCE(SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END), 0) AS present
           FROM attendance WHERE student_id = ?""",
        (student_db_id,),
    ).fetchone()
    return round((row["present"] / row["total"] * 100) if row["total"] else 0, 1)


def validate_student(form):
    data = {
        "student_id": form.get("student_id", "").strip().upper(),
        "name": form.get("name", "").strip(),
        "email": form.get("email", "").strip().lower(),
        "department": form.get("department", "").strip(),
        "semester": form.get("semester", "").strip(),
        "phone": form.get("phone", "").strip(),
    }
    if not all(data.values()):
        return data, "Please complete every student field."
    if data["department"] not in DEPARTMENTS:
        return data, "Please choose a valid department."
    if not data["semester"].isdigit() or not 1 <= int(data["semester"]) <= 8:
        return data, "Semester must be between 1 and 8."
    if "@" not in data["email"] or "." not in data["email"].split("@")[-1]:
        return data, "Enter a valid email address."
    return data, None


def validate_assignment(form):
    data = {field: form.get(field, "").strip() for field in ["title", "subject", "description", "assigned_date", "due_date", "status"]}
    if not all(data.values()):
        return data, "Please complete every assignment field."
    if data["subject"] not in SUBJECTS or data["status"] not in VALID_ASSIGNMENT_STATUS:
        return data, "Choose a valid subject and status."
    if data["due_date"] < data["assigned_date"]:
        return data, "Due date cannot be before the assigned date."
    return data, None


def validate_event(form):
    data = {field: form.get(field, "").strip() for field in ["name", "description", "event_date", "event_time", "venue", "organizer"]}
    if not all(data.values()):
        return data, "Please complete every event field."
    return data, None


def init_db():
    DATABASE_PATH.parent.mkdir(exist_ok=True)
    with closing(sqlite3.connect(DATABASE_PATH)) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                department TEXT NOT NULL,
                semester INTEGER NOT NULL CHECK (semester BETWEEN 1 AND 8),
                phone TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                attendance_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('Present', 'Absent')),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE(student_id, subject, attendance_date)
            );
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                assigned_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('Pending', 'Submitted', 'Overdue'))
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                event_date TEXT NOT NULL,
                event_time TEXT NOT NULL,
                venue TEXT NOT NULL,
                organizer TEXT NOT NULL
            );
            """
        )
        if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            seed_database(db)
        db.commit()


def seed_database(db):
    db.execute(
        "INSERT INTO users (username, password_hash, display_name) VALUES (?, ?, ?)",
        ("admin", generate_password_hash("admin123"), "Campus Administrator"),
    )
    students = [
        ("CS2024001", "Aarav Sharma", "aarav.sharma@campus.edu", "Computer Science", 5, "+91 98765 10001"),
        ("CS2024002", "Diya Patel", "diya.patel@campus.edu", "Computer Science", 5, "+91 98765 10002"),
        ("IT2024003", "Kabir Singh", "kabir.singh@campus.edu", "Information Technology", 5, "+91 98765 10003"),
        ("IT2024004", "Ananya Rao", "ananya.rao@campus.edu", "Information Technology", 3, "+91 98765 10004"),
        ("EC2024005", "Ishaan Verma", "ishaan.verma@campus.edu", "Electronics", 3, "+91 98765 10005"),
        ("ME2024006", "Meera Nair", "meera.nair@campus.edu", "Mechanical", 7, "+91 98765 10006"),
        ("CV2024007", "Rohan Gupta", "rohan.gupta@campus.edu", "Civil", 7, "+91 98765 10007"),
        ("CS2024008", "Zoya Khan", "zoya.khan@campus.edu", "Computer Science", 1, "+91 98765 10008"),
        ("IT2024009", "Arjun Das", "arjun.das@campus.edu", "Information Technology", 1, "+91 98765 10009"),
    ]
    db.executemany(
        "INSERT INTO students (student_id, name, email, department, semester, phone) VALUES (?, ?, ?, ?, ?, ?)", students
    )
    student_rows = db.execute("SELECT id FROM students ORDER BY id").fetchall()
    today = date.today()
    attendance = []
    for day_offset in range(20):
        class_date = (today - timedelta(days=day_offset)).isoformat()
        for index, student in enumerate(student_rows):
            for subject_index, subject in enumerate(SUBJECTS[:3]):
                present = (index * 3 + day_offset + subject_index) % 11 != 0
                attendance.append((student[0], subject, class_date, "Present" if present else "Absent"))
    db.executemany(
        "INSERT INTO attendance (student_id, subject, attendance_date, status) VALUES (?, ?, ?, ?)", attendance
    )
    assignments = [
        ("Normalize the Library Schema", "Database Systems", "Design a normalized relational schema and SQL queries.", (today - timedelta(days=4)).isoformat(), (today + timedelta(days=2)).isoformat(), "Pending"),
        ("Responsive Portfolio", "Web Technologies", "Build a responsive portfolio page using semantic HTML and CSS.", (today - timedelta(days=10)).isoformat(), (today - timedelta(days=1)).isoformat(), "Overdue"),
        ("Graph Traversal Lab", "Data Structures", "Implement BFS and DFS with complexity analysis.", (today - timedelta(days=8)).isoformat(), (today + timedelta(days=4)).isoformat(), "Submitted"),
        ("Subnetting Worksheet", "Computer Networks", "Complete the IPv4 subnetting worksheet.", (today - timedelta(days=3)).isoformat(), (today + timedelta(days=6)).isoformat(), "Pending"),
        ("SRS Review", "Software Engineering", "Review and refine the software requirements specification.", (today - timedelta(days=12)).isoformat(), (today - timedelta(days=3)).isoformat(), "Submitted"),
    ]
    db.executemany(
        """INSERT INTO assignments (title, subject, description, assigned_date, due_date, status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        assignments,
    )
    events = [
        ("Innovation Showcase", "Student teams present practical campus and community projects.", (today + timedelta(days=3)).isoformat(), "10:00", "Main Auditorium", "Innovation Cell"),
        ("Career Readiness Workshop", "A hands-on session on resumes, interviews and portfolios.", (today + timedelta(days=7)).isoformat(), "14:00", "Seminar Hall B", "Career Services"),
        ("Annual Sports Meet", "Inter-department athletics and team events.", (today + timedelta(days=12)).isoformat(), "08:30", "College Ground", "Sports Committee"),
        ("Alumni Tech Talk", "Alumni share lessons from early-career engineering roles.", (today - timedelta(days=5)).isoformat(), "16:00", "Auditorium", "Alumni Office"),
    ]
    db.executemany(
        "INSERT INTO events (name, description, event_date, event_time, venue, organizer) VALUES (?, ?, ?, ?, ?, ?)", events
    )


@app.context_processor
def inject_globals():
    return {"departments": DEPARTMENTS, "subjects": SUBJECTS, "today": date.today().isoformat()}


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["display_name"] = user["display_name"]
            flash("Welcome back, Campus Administrator.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html", title="Sign in")


@app.post("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.get("/")
@login_required
def dashboard():
    db = get_db()
    summary = db.execute(
        """SELECT
            (SELECT COUNT(*) FROM students) AS total_students,
            (SELECT COUNT(*) FROM assignments WHERE status = 'Pending') AS pending_assignments,
            (SELECT COUNT(*) FROM events WHERE event_date >= ?) AS upcoming_events,
            (SELECT ROUND(100.0 * SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) FROM attendance) AS average_attendance""",
        (date.today().isoformat(),),
    ).fetchone()
    events = db.execute("SELECT * FROM events WHERE event_date >= ? ORDER BY event_date, event_time LIMIT 4", (date.today().isoformat(),)).fetchall()
    activity = db.execute(
        """SELECT 'assignment' AS type, title AS label, due_date AS event_date, status AS detail FROM assignments
           UNION ALL
           SELECT 'event' AS type, name AS label, event_date, venue AS detail FROM events
           ORDER BY event_date DESC LIMIT 6"""
    ).fetchall()
    return render_template("dashboard.html", title="Dashboard", summary=summary, events=events, activity=activity)


@app.get("/students")
@login_required
def students():
    search = request.args.get("q", "").strip()
    department = request.args.get("department", "").strip()
    conditions, params = [], []
    if search:
        conditions.append("(s.name LIKE ? OR s.student_id LIKE ? OR s.email LIKE ?)")
        params.extend([f"%{search}%"] * 3)
    if department in DEPARTMENTS:
        conditions.append("s.department = ?")
        params.append(department)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = get_db().execute(
        f"""SELECT s.*, ROUND(100.0 * SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / NULLIF(COUNT(a.id), 0), 1) AS attendance_percentage
             FROM students s LEFT JOIN attendance a ON a.student_id = s.id {where}
             GROUP BY s.id ORDER BY s.name""",
        params,
    ).fetchall()
    return render_template("students.html", title="Students", students=rows, search=search, selected_department=department)


@app.route("/students/new", methods=["GET", "POST"])
@login_required
def add_student():
    student = None
    if request.method == "POST":
        student, error = validate_student(request.form)
        if not error:
            try:
                db_execute(
                    "INSERT INTO students (student_id, name, email, department, semester, phone) VALUES (?, ?, ?, ?, ?, ?)",
                    (student["student_id"], student["name"], student["email"], student["department"], student["semester"], student["phone"]),
                )
            except sqlite3.IntegrityError:
                error = "Student ID and email must both be unique."
            else:
                flash("Student added successfully.", "success")
                return redirect(url_for("students"))
        flash(error, "danger")
    return render_template("student_form.html", title="Add student", student=student, form_action=url_for("add_student"))


@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    existing = fetch_one_or_404("SELECT * FROM students WHERE id = ?", (student_id,))
    student = existing
    if request.method == "POST":
        student, error = validate_student(request.form)
        if not error:
            try:
                db_execute(
                    """UPDATE students SET student_id = ?, name = ?, email = ?, department = ?, semester = ?, phone = ? WHERE id = ?""",
                    (student["student_id"], student["name"], student["email"], student["department"], student["semester"], student["phone"], student_id),
                )
            except sqlite3.IntegrityError:
                error = "Student ID and email must both be unique."
            else:
                flash("Student updated successfully.", "success")
                return redirect(url_for("student_detail", student_id=student_id))
        flash(error, "danger")
    return render_template("student_form.html", title="Edit student", student=student, form_action=url_for("edit_student", student_id=student_id))


@app.get("/students/<int:student_id>")
@login_required
def student_detail(student_id):
    student = fetch_one_or_404("SELECT * FROM students WHERE id = ?", (student_id,))
    subject_attendance = get_db().execute(
        """SELECT subject, COUNT(*) AS total, SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) AS present,
                  ROUND(100.0 * SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) / COUNT(*), 1) AS percentage
           FROM attendance WHERE student_id = ? GROUP BY subject ORDER BY subject""",
        (student_id,),
    ).fetchall()
    records = get_db().execute("SELECT * FROM attendance WHERE student_id = ? ORDER BY attendance_date DESC LIMIT 12", (student_id,)).fetchall()
    return render_template("student_detail.html", title=student["name"], student=student, percentage=attendance_percentage(student_id), subject_attendance=subject_attendance, records=records)


@app.post("/students/<int:student_id>/delete")
@login_required
def delete_student(student_id):
    fetch_one_or_404("SELECT id FROM students WHERE id = ?", (student_id,))
    db_execute("DELETE FROM students WHERE id = ?", (student_id,))
    flash("Student and related attendance records were deleted.", "success")
    return redirect(url_for("students"))


@app.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    db = get_db()
    if request.method == "POST":
        student_id = request.form.get("student_id", type=int)
        subject = request.form.get("subject", "").strip()
        attendance_date = request.form.get("attendance_date", "").strip()
        status = request.form.get("status", "").strip()
        if not student_id or subject not in SUBJECTS or status not in VALID_ATTENDANCE or not attendance_date:
            flash("Select a student, subject, date and valid attendance status.", "danger")
        elif not db.execute("SELECT id FROM students WHERE id = ?", (student_id,)).fetchone():
            flash("The selected student no longer exists.", "danger")
        else:
            existing = db.execute("SELECT id FROM attendance WHERE student_id = ? AND subject = ? AND attendance_date = ?", (student_id, subject, attendance_date)).fetchone()
            if existing:
                db_execute("UPDATE attendance SET status = ? WHERE id = ?", (status, existing["id"]))
                flash("Attendance record updated.", "success")
            else:
                db_execute("INSERT INTO attendance (student_id, subject, attendance_date, status) VALUES (?, ?, ?, ?)", (student_id, subject, attendance_date, status))
                flash("Attendance marked successfully.", "success")
            return redirect(url_for("attendance"))
    rows = db.execute(
        """SELECT s.id, s.student_id, s.name, s.department,
                  ROUND(100.0 * SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / NULLIF(COUNT(a.id), 0), 1) AS percentage,
                  COUNT(a.id) AS classes
           FROM students s LEFT JOIN attendance a ON a.student_id = s.id
           GROUP BY s.id ORDER BY percentage ASC, s.name"""
    ).fetchall()
    recent_records = db.execute(
        """SELECT a.*, s.name, s.student_id FROM attendance a JOIN students s ON s.id = a.student_id
           ORDER BY a.attendance_date DESC, a.id DESC LIMIT 10"""
    ).fetchall()
    all_students = db.execute("SELECT id, student_id, name FROM students ORDER BY name").fetchall()
    overall = db.execute("SELECT ROUND(100.0 * SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS percentage FROM attendance").fetchone()["percentage"] or 0
    return render_template("attendance.html", title="Attendance", students=rows, all_students=all_students, recent_records=recent_records, overall=overall)


@app.post("/attendance/<int:record_id>/delete")
@login_required
def delete_attendance(record_id):
    fetch_one_or_404("SELECT id FROM attendance WHERE id = ?", (record_id,))
    db_execute("DELETE FROM attendance WHERE id = ?", (record_id,))
    flash("Attendance record deleted.", "success")
    return redirect(url_for("attendance"))


@app.get("/assignments")
@login_required
def assignments():
    status = request.args.get("status", "").strip()
    query, params = "SELECT * FROM assignments", []
    if status in VALID_ASSIGNMENT_STATUS:
        query += " WHERE status = ?"
        params.append(status)
    query += " ORDER BY due_date, id DESC"
    rows = get_db().execute(query, params).fetchall()
    return render_template("assignments.html", title="Assignments", assignments=rows, selected_status=status)


@app.route("/assignments/new", methods=["GET", "POST"])
@login_required
def add_assignment():
    assignment = None
    if request.method == "POST":
        assignment, error = validate_assignment(request.form)
        if not error:
            db_execute("INSERT INTO assignments (title, subject, description, assigned_date, due_date, status) VALUES (?, ?, ?, ?, ?, ?)", tuple(assignment.values()))
            flash("Assignment added successfully.", "success")
            return redirect(url_for("assignments"))
        flash(error, "danger")
    return render_template("assignment_form.html", title="Add assignment", assignment=assignment, form_action=url_for("add_assignment"))


@app.route("/assignments/<int:assignment_id>/edit", methods=["GET", "POST"])
@login_required
def edit_assignment(assignment_id):
    assignment = fetch_one_or_404("SELECT * FROM assignments WHERE id = ?", (assignment_id,))
    if request.method == "POST":
        assignment, error = validate_assignment(request.form)
        if not error:
            db_execute("""UPDATE assignments SET title = ?, subject = ?, description = ?, assigned_date = ?, due_date = ?, status = ? WHERE id = ?""", (*assignment.values(), assignment_id))
            flash("Assignment updated successfully.", "success")
            return redirect(url_for("assignments"))
        flash(error, "danger")
    return render_template("assignment_form.html", title="Edit assignment", assignment=assignment, form_action=url_for("edit_assignment", assignment_id=assignment_id))


@app.post("/assignments/<int:assignment_id>/delete")
@login_required
def delete_assignment(assignment_id):
    fetch_one_or_404("SELECT id FROM assignments WHERE id = ?", (assignment_id,))
    db_execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
    flash("Assignment deleted.", "success")
    return redirect(url_for("assignments"))


@app.get("/events")
@login_required
def events():
    rows = get_db().execute("SELECT *, event_date < ? AS is_past FROM events ORDER BY event_date, event_time", (date.today().isoformat(),)).fetchall()
    return render_template("events.html", title="Events", events=rows)


@app.route("/events/new", methods=["GET", "POST"])
@login_required
def add_event():
    event = None
    if request.method == "POST":
        event, error = validate_event(request.form)
        if not error:
            db_execute("INSERT INTO events (name, description, event_date, event_time, venue, organizer) VALUES (?, ?, ?, ?, ?, ?)", tuple(event.values()))
            flash("Event added successfully.", "success")
            return redirect(url_for("events"))
        flash(error, "danger")
    return render_template("event_form.html", title="Add event", event=event, form_action=url_for("add_event"))


@app.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def edit_event(event_id):
    event = fetch_one_or_404("SELECT * FROM events WHERE id = ?", (event_id,))
    if request.method == "POST":
        event, error = validate_event(request.form)
        if not error:
            db_execute("""UPDATE events SET name = ?, description = ?, event_date = ?, event_time = ?, venue = ?, organizer = ? WHERE id = ?""", (*event.values(), event_id))
            flash("Event updated successfully.", "success")
            return redirect(url_for("events"))
        flash(error, "danger")
    return render_template("event_form.html", title="Edit event", event=event, form_action=url_for("edit_event", event_id=event_id))


@app.post("/events/<int:event_id>/delete")
@login_required
def delete_event(event_id):
    fetch_one_or_404("SELECT id FROM events WHERE id = ?", (event_id,))
    db_execute("DELETE FROM events WHERE id = ?", (event_id,))
    flash("Event deleted.", "success")
    return redirect(url_for("events"))


@app.post("/events/delete-past")
@login_required
def delete_past_events():
    result = db_execute("DELETE FROM events WHERE event_date < ?", (date.today().isoformat(),))
    flash(f"Deleted {result.rowcount} past event{'s' if result.rowcount != 1 else ''}.", "success")
    return redirect(url_for("events"))


@app.get("/analytics")
@login_required
def analytics():
    return render_template("analytics.html", title="Analytics")


@app.get("/api/analytics")
@login_required
def analytics_data():
    db = get_db()
    department_rows = db.execute("SELECT department, COUNT(*) AS count FROM students GROUP BY department ORDER BY count DESC").fetchall()
    attendance_rows = db.execute(
        """SELECT CASE
                  WHEN percentage < 60 THEN 'Below 60%'
                  WHEN percentage < 75 THEN '60–74%'
                  WHEN percentage < 90 THEN '75–89%'
                  ELSE '90% and above' END AS band, COUNT(*) AS count
           FROM (
               SELECT s.id, 100.0 * SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / NULLIF(COUNT(a.id), 0) AS percentage
               FROM students s LEFT JOIN attendance a ON a.student_id = s.id GROUP BY s.id
           ) GROUP BY band"""
    ).fetchall()
    assignment_rows = db.execute("SELECT status, COUNT(*) AS count FROM assignments GROUP BY status").fetchall()
    trend_rows = db.execute(
        """SELECT attendance_date AS date,
                  ROUND(100.0 * SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) / COUNT(*), 1) AS percentage
           FROM attendance GROUP BY attendance_date ORDER BY attendance_date"""
    ).fetchall()
    student_rows = db.execute(
        """SELECT s.name, ROUND(100.0 * SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / NULLIF(COUNT(a.id), 0), 1) AS percentage
           FROM students s LEFT JOIN attendance a ON a.student_id = s.id GROUP BY s.id ORDER BY percentage DESC, s.name LIMIT 8"""
    ).fetchall()
    return jsonify(
        departments=[dict(row) for row in department_rows],
        attendance_distribution=[dict(row) for row in attendance_rows],
        assignments=[dict(row) for row in assignment_rows],
        trend=[dict(row) for row in trend_rows],
        student_performance=[dict(row) for row in student_rows],
    )


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html", title="Page not found"), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
