# Smart Campus Management System

A polished Flask and SQLite application for managing student records, attendance, assignments, campus events, and reporting from one responsive admin workspace.

## Project Overview

SmartCampus is designed as a portfolio-ready college administration project. It seeds a realistic demo workspace on first launch, so dashboards and charts are useful immediately.

## Features

- Session-protected administrator login and logout
- Student directory with search, department filtering, full CRUD, attendance indicators, and individual profiles
- Daily attendance marking with automatic updates for duplicate student/subject/date entries
- Student-wise and subject-wise attendance reporting with low-attendance highlights
- Assignment CRUD and status filtering for pending, submitted, and overdue work
- Event CRUD, past-event cleanup, and upcoming events on the dashboard
- Chart.js dashboard and analytics views driven by live SQLite data
- Responsive sidebar, dark mode, toast messages, empty states, and confirmation dialogs

## Technology Stack

- Python 3
- Flask
- SQLite
- HTML5, CSS3, and vanilla JavaScript
- Chart.js (loaded from CDN)
- Jinja2 templates

## Screenshots

Launch the app locally to view the dashboard, student directory, attendance board, calendar, and analytics screens. The interface is responsive from desktop down to mobile layouts.

## Project Structure

```text
smart-campus-management/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── database/
│   └── campus.db              # created automatically on first run
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── students.html
│   ├── student_form.html
│   ├── student_detail.html
│   ├── attendance.html
│   ├── assignments.html
│   ├── assignment_form.html
│   ├── events.html
│   ├── event_form.html
│   ├── analytics.html
│   └── 404.html
└── static/
    ├── css/style.css
    └── js/
        ├── main.js
        ├── dashboard.js
        └── charts.js
```

## Installation

```bash
git clone <repository-url>
cd smart-campus-management
python -m venv .venv
```

Activate the virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python app.py
```

Open `http://127.0.0.1:5000` in a browser. On the first launch, the app creates `database/campus.db`, applies its schema, and inserts realistic demo records.

## Demo Login

| Field | Value |
| --- | --- |
| Username | `admin` |
| Password | `admin123` |

## Database

The application initializes SQLite tables for users, students, attendance, assignments, and events. It uses parameterized queries throughout; related attendance data is removed automatically when a student is deleted.

## Future Improvements

- Add role-specific staff and faculty accounts
- Add CSV import/export for student and attendance data
- Add CSRF protection before deploying publicly
- Add email reminders for deadlines and attendance thresholds

## Author

Built as a B.Tech portfolio project for campus administration workflows.
