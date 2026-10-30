import os
from io import BytesIO
from functools import wraps

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-development-key")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "student_performance"),
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def query_all(sql, params=()):
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def execute(sql, params=()):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        cur.close()
        conn.close()

def get_students():
    return query_all("SELECT * FROM students ORDER BY section, roll_no")

def get_subjects():
    return query_all("SELECT * FROM subjects ORDER BY subject_name")

def get_mark_rows():
    return query_all("""
        SELECT m.mark_id, m.student_id, s.roll_no, s.name, s.section,
               sub.subject_id, sub.subject_name, sub.max_marks, sub.pass_marks,
               m.assessment, m.marks_obtained
        FROM marks m
        JOIN students s ON s.student_id=m.student_id
        JOIN subjects sub ON sub.subject_id=m.subject_id
        ORDER BY s.section, s.roll_no, sub.subject_name, m.assessment
    """)

def grade_for(percentage):
    if percentage >= 90: return "A"
    if percentage >= 80: return "B"
    if percentage >= 70: return "C"
    if percentage >= 60: return "D"
    if percentage >= 40: return "E"
    return "F"

@app.route("/")
def dashboard():
    students = query_all("SELECT COUNT(*) AS n FROM students")[0]["n"]
    subjects = query_all("SELECT COUNT(*) AS n FROM subjects")[0]["n"]
    marks_count = query_all("SELECT COUNT(*) AS n FROM marks")[0]["n"]
    rows = get_mark_rows()
    if rows:
        df = pd.DataFrame(rows)
        df["percentage"] = df["marks_obtained"] / df["max_marks"] * 100
        df["passed"] = df["marks_obtained"] >= df["pass_marks"]
        pass_rate = round(float(df["passed"].mean() * 100), 1)
        average = round(float(np.mean(df["percentage"])), 1)
    else:
        pass_rate, average = 0, 0
    threshold = float(request.args.get("threshold", 40))
    low = low_performers(threshold)
    return render_template("dashboard.html", students=students, subjects=subjects,
                           marks_count=marks_count, pass_rate=pass_rate,
                           average=average, low=low, threshold=threshold)

@app.route("/students")
def students():
    return render_template("students.html", students=get_students())

@app.route("/students/add", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        roll = request.form.get("roll_no", "").strip()
        name = request.form.get("name", "").strip()
        section = request.form.get("section", "").strip()
        if not roll or not name or not section:
            flash("Please fill in every field.", "error")
        else:
            try:
                execute("INSERT INTO students (roll_no,name,section) VALUES (%s,%s,%s)",
                        (roll, name, section))
                flash("Student added.", "success")
                return redirect(url_for("students"))
            except mysql.connector.IntegrityError:
                flash("That roll number already exists.", "error")
    return render_template("student_form.html", student=None)

@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
def edit_student(student_id):
    result = query_all("SELECT * FROM students WHERE student_id=%s", (student_id,))
    if not result:
        flash("Student not found.", "error")
        return redirect(url_for("students"))
    student = result[0]
    if request.method == "POST":
        values = (request.form.get("roll_no", "").strip(),
                  request.form.get("name", "").strip(),
                  request.form.get("section", "").strip(), student_id)
        if not all(values[:3]):
            flash("Please fill in every field.", "error")
        else:
            try:
                execute("UPDATE students SET roll_no=%s,name=%s,section=%s WHERE student_id=%s", values)
                flash("Student updated.", "success")
                return redirect(url_for("students"))
            except mysql.connector.IntegrityError:
                flash("That roll number already exists.", "error")
    return render_template("student_form.html", student=student)

@app.post("/students/<int:student_id>/delete")
def delete_student(student_id):
    execute("DELETE FROM students WHERE student_id=%s", (student_id,))
    flash("Student and their marks deleted.", "success")
    return redirect(url_for("students"))

@app.route("/subjects")
def subjects():
    return render_template("subjects.html", subjects=get_subjects())

@app.route("/subjects/add", methods=["GET", "POST"])
def add_subject():
    if request.method == "POST":
        name = request.form.get("subject_name", "").strip()
        try:
            maximum = int(request.form.get("max_marks", ""))
            passing = int(request.form.get("pass_marks", ""))
            if not name or maximum <= 0 or passing < 0 or passing > maximum:
                raise ValueError
            execute("INSERT INTO subjects (subject_name,max_marks,pass_marks) VALUES (%s,%s,%s)",
                    (name, maximum, passing))
            flash("Subject added.", "success")
            return redirect(url_for("subjects"))
        except (ValueError, TypeError, mysql.connector.IntegrityError):
            flash("Enter a unique subject name, max marks > 0, and pass marks from 0 to max marks.", "error")
    return render_template("subject_form.html")

@app.post("/subjects/<int:subject_id>/delete")
def delete_subject(subject_id):
    execute("DELETE FROM subjects WHERE subject_id=%s", (subject_id,))
    flash("Subject and its marks deleted.", "success")
    return redirect(url_for("subjects"))

@app.route("/marks")
def marks():
    return render_template("marks.html", marks=get_mark_rows(), students=get_students(), subjects=get_subjects())

@app.route("/marks/add", methods=["GET", "POST"])
def add_mark():
    students, subjects = get_students(), get_subjects()
    if request.method == "POST":
        try:
            student_id = int(request.form["student_id"])
            subject_id = int(request.form["subject_id"])
            assessment = request.form.get("assessment", "").strip()
            score = float(request.form["marks_obtained"])
            subject_rows = query_all("SELECT * FROM subjects WHERE subject_id=%s", (subject_id,))
            if not subject_rows or not assessment or not np.isfinite(score) or score < 0 or score > subject_rows[0]["max_marks"]:
                raise ValueError
            execute("INSERT INTO marks (student_id,subject_id,assessment,marks_obtained) VALUES (%s,%s,%s,%s)",
                    (student_id, subject_id, assessment, score))
            flash("Mark saved.", "success")
            return redirect(url_for("marks"))
        except (ValueError, KeyError, TypeError, mysql.connector.IntegrityError):
            flash("Invalid data. Marks must be between 0 and the subject's maximum marks.", "error")
    return render_template("mark_form.html", students=students, subjects=subjects)

@app.route("/marks/<int:mark_id>/edit", methods=["GET", "POST"])
def edit_mark(mark_id):
    found = query_all("SELECT * FROM marks WHERE mark_id=%s", (mark_id,))
    if not found:
        flash("Mark record not found.", "error")
        return redirect(url_for("marks"))
    mark = found[0]
    students, subjects = get_students(), get_subjects()
    if request.method == "POST":
        try:
            sid, subid = int(request.form["student_id"]), int(request.form["subject_id"])
            assessment, score = request.form["assessment"].strip(), float(request.form["marks_obtained"])
            sub = query_all("SELECT * FROM subjects WHERE subject_id=%s", (subid,))
            if not sub or not assessment or not np.isfinite(score) or score < 0 or score > sub[0]["max_marks"]:
                raise ValueError
            execute("UPDATE marks SET student_id=%s,subject_id=%s,assessment=%s,marks_obtained=%s WHERE mark_id=%s",
                    (sid, subid, assessment, score, mark_id))
            flash("Mark updated.", "success")
            return redirect(url_for("marks"))
        except (ValueError, KeyError, TypeError, mysql.connector.IntegrityError):
            flash("Invalid data or marks outside the permitted range.", "error")
    return render_template("mark_form.html", students=students, subjects=subjects, mark=mark)

@app.post("/marks/<int:mark_id>/delete")
def delete_mark(mark_id):
    execute("DELETE FROM marks WHERE mark_id=%s", (mark_id,))
    flash("Mark deleted.", "success")
    return redirect(url_for("marks"))

def performance_report():
    rows = get_mark_rows()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["percentage"] = df["marks_obtained"] / df["max_marks"] * 100
    df["passed"] = df["marks_obtained"] >= df["pass_marks"]
    return df

def low_performers(threshold=40):
    df = performance_report()
    if df.empty:
        return []
    student = (df.groupby(["student_id", "roll_no", "name", "section"], as_index=False)
                 .agg(average_percentage=("percentage", "mean")))
    student["average_percentage"] = student["average_percentage"].round(1)
    return student[student["average_percentage"] < threshold].sort_values("average_percentage").to_dict("records")

@app.route("/reports")
def reports():
    df = performance_report()
    if df.empty:
        subject_summary, section_summary, toppers, pass_summary = [], [], [], []
    else:
        subject_summary = df.groupby("subject_name", as_index=False).agg(
            attempts=("marks_obtained", "count"),
            average_marks=("marks_obtained", "mean"),
            pass_percentage=("passed", lambda x: x.mean() * 100))
        subject_summary[["average_marks", "pass_percentage"]] = subject_summary[["average_marks", "pass_percentage"]].round(1)
        section_summary = df.groupby("section", as_index=False).agg(
            attempts=("marks_obtained", "count"),
            average_percentage=("percentage", "mean"),
            pass_percentage=("passed", lambda x: x.mean() * 100))
        section_summary[["average_percentage", "pass_percentage"]] = section_summary[["average_percentage", "pass_percentage"]].round(1)
        toppers = (df.groupby(["student_id", "roll_no", "name", "section"], as_index=False)
                     .agg(average_percentage=("percentage", "mean"))
                     .sort_values("average_percentage", ascending=False).head(10))
        toppers["average_percentage"] = toppers["average_percentage"].round(1)
        pass_summary = [{"status": "Pass", "count": int(df["passed"].sum())},
                        {"status": "Fail", "count": int((~df["passed"]).sum())}]
        subject_summary = subject_summary.to_dict("records")
        section_summary = section_summary.to_dict("records")
        toppers = toppers.to_dict("records")
    threshold = float(request.args.get("threshold", 40))
    return render_template("reports.html", subject_summary=subject_summary,
                           section_summary=section_summary, toppers=toppers,
                           pass_summary=pass_summary, low=low_performers(threshold),
                           threshold=threshold, has_data=not df.empty)

@app.route("/reports/export.csv")
def export_csv():
    df = performance_report()
    if df.empty:
        df = pd.DataFrame(columns=["roll_no", "name", "section", "subject_name", "assessment", "marks_obtained", "max_marks", "pass_marks", "percentage", "passed"])
    output = BytesIO()
    output.write(df.to_csv(index=False).encode("utf-8"))
    output.seek(0)
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name="student_performance_report.csv")

@app.route("/charts/subjects.png")
def subject_chart():
    df = performance_report()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if df.empty:
        ax.text(0.5, 0.5, "No marks recorded yet", ha="center", va="center")
        ax.set_axis_off()
    else:
        summary = df.groupby("subject_name")["marks_obtained"].mean().sort_values(ascending=False)
        ax.bar(summary.index, summary.values)
        ax.set_title("Subject-wise Average Marks")
        ax.set_ylabel("Average marks")
        ax.tick_params(axis="x", rotation=25)
        fig.tight_layout()
    image = BytesIO()
    fig.savefig(image, format="png", bbox_inches="tight")
    plt.close(fig)
    image.seek(0)
    return send_file(image, mimetype="image/png")

@app.route("/charts/pass.png")
def pass_chart():
    df = performance_report()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if df.empty:
        ax.text(0.5, 0.5, "No marks recorded yet", ha="center", va="center")
        ax.set_axis_off()
    else:
        summary = (df.groupby("subject_name")["passed"].mean() * 100).round(1)
        ax.bar(summary.index, summary.values)
        ax.set_title("Subject-wise Pass Percentage")
        ax.set_ylabel("Pass percentage (%)")
        ax.set_ylim(0, 100)
        ax.tick_params(axis="x", rotation=25)
        fig.tight_layout()
    image = BytesIO()
    fig.savefig(image, format="png", bbox_inches="tight")
    plt.close(fig)
    image.seek(0)
    return send_file(image, mimetype="image/png")

if __name__ == "__main__":
    app.run(debug=True)
