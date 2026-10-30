# Student Performance Analysis System

A beginner-friendly Flask + MySQL application to manage student profiles, subjects, marks, and academic performance reports.

## Features
- Student and subject CRUD (create, view, update students; add/delete subjects)
- Add, edit, view, and delete marks
- Validates marks against each subject's maximum marks
- Calculates percentage, pass/fail, subject and section summaries
- Top 10 students by average assessment percentage
- Configurable below-threshold list
- Pandas and NumPy analysis
- Matplotlib charts and CSV export

## Stack
Python, Flask, MySQL, pandas, NumPy, Matplotlib, HTML/CSS.

## Rules used
- A mark is passed when `marks_obtained >= pass_marks`.
- Percentage for an attempt is `marks_obtained / max_marks * 100`.
- Student average percentage is the mean of their recorded assessment percentages.
- Default low-performance threshold is 40%; change it on the dashboard/reports page.
- Grades: A >= 90, B >= 80, C >= 70, D >= 60, E >= 40, F < 40. (The current report emphasizes percentages and pass/fail.)

## Setup (Windows)
1. Install Python 3.10+ and MySQL Server. Ensure the MySQL service is running.
2. Open Command Prompt or PowerShell in this project folder.
3. Create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```
4. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
5. Create database and tables:
   ```powershell
   mysql -u root -p < schema.sql
   ```
   If `mysql` is not recognized, open MySQL Workbench, open `schema.sql`, and execute it.
6. Copy `.env.example` to `.env`, then edit `.env` with your MySQL username/password.
7. Start the app:
   ```powershell
   python app.py
   ```
8. Visit http://127.0.0.1:5000 in your browser.

## GitHub upload
1. Create a new empty repository on GitHub, e.g. `student-performance-analysis`.
2. In this folder, run:
   ```bash
   git init
   git add .
   git commit -m "Initial student performance analysis system"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/student-performance-analysis.git
   git push -u origin main
   ```
3. Replace `YOUR-USERNAME` with your GitHub username. Do not commit `.env`; it is ignored by Git.

## Notes
- This is a local learning project, not production-ready authentication software.
- Use sample or institution-approved data only. Do not publish real student personal data to a public repository.
- MySQL CHECK constraints are enforced in current MySQL versions; the Flask layer also validates marks.
