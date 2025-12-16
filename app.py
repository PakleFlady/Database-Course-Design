"""CLI toolkit for the course registration and grade management demo (SQLite + Python).

This script builds the schema, loads seed data, and exposes helper commands to
exercise common workflows such as prerequisite checks, conflict detection, and
GPA calculation. It uses only the Python standard library (sqlite3 + argparse).
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Iterable, List, Tuple

DB_PATH = Path("university_demo.db")

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS colleges (
    college_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    dean            TEXT,
    contact_email   TEXT
);

CREATE TABLE IF NOT EXISTS departments (
    department_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id      INTEGER NOT NULL REFERENCES colleges(college_id),
    name            TEXT NOT NULL,
    office_location TEXT,
    contact_email   TEXT,
    UNIQUE (college_id, name)
);

CREATE TABLE IF NOT EXISTS majors (
    major_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id   INTEGER NOT NULL REFERENCES departments(department_id),
    name            TEXT NOT NULL,
    degree_level    TEXT NOT NULL CHECK (degree_level IN ('bachelor', 'master', 'phd')),
    required_credits INTEGER NOT NULL CHECK (required_credits > 0),
    UNIQUE (department_id, name)
);

CREATE TABLE IF NOT EXISTS semesters (
    semester_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    start_date      TEXT NOT NULL,
    end_date        TEXT NOT NULL,
    add_deadline    TEXT,
    drop_deadline   TEXT,
    CHECK (start_date < end_date)
);

CREATE TABLE IF NOT EXISTS users (
    user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('student', 'instructor', 'admin')),
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'disabled')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS students (
    student_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL UNIQUE REFERENCES users(user_id),
    major_id        INTEGER NOT NULL REFERENCES majors(major_id),
    college_id      INTEGER NOT NULL REFERENCES colleges(college_id),
    full_name       TEXT NOT NULL,
    gender          TEXT,
    date_of_birth   TEXT,
    email           TEXT,
    phone           TEXT,
    address         TEXT,
    enrollment_year INTEGER CHECK (enrollment_year >= 1900),
    expected_graduation_year INTEGER,
    gpa_cache       REAL
);

CREATE TABLE IF NOT EXISTS instructors (
    instructor_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL UNIQUE REFERENCES users(user_id),
    department_id   INTEGER NOT NULL REFERENCES departments(department_id),
    full_name       TEXT NOT NULL,
    title           TEXT,
    email           TEXT,
    phone           TEXT,
    office          TEXT,
    status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'on_leave', 'retired'))
);

CREATE TABLE IF NOT EXISTS courses (
    course_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id   INTEGER NOT NULL REFERENCES departments(department_id),
    course_code     TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    credits         REAL NOT NULL CHECK (credits > 0),
    course_type     TEXT NOT NULL CHECK (course_type IN ('general_required', 'major_required', 'major_elective', 'university_elective', 'practical')),
    description     TEXT,
    repeatable      INTEGER NOT NULL DEFAULT 0,
    active          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS course_sections (
    section_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id       INTEGER NOT NULL REFERENCES courses(course_id),
    semester_id     INTEGER NOT NULL REFERENCES semesters(semester_id),
    instructor_id   INTEGER NOT NULL REFERENCES instructors(instructor_id),
    section_code    TEXT NOT NULL,
    capacity        INTEGER NOT NULL CHECK (capacity >= 0),
    waitlist_capacity INTEGER NOT NULL DEFAULT 0 CHECK (waitlist_capacity >= 0),
    location_note   TEXT,
    status          TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('planned', 'open', 'closed', 'cancelled')),
    language        TEXT DEFAULT 'English',
    grading_scheme  TEXT NOT NULL DEFAULT 'numeric' CHECK (grading_scheme IN ('numeric', 'letter', 'pass_fail')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (course_id, semester_id, section_code)
);

CREATE TABLE IF NOT EXISTS section_meetings (
    meeting_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id      INTEGER NOT NULL REFERENCES course_sections(section_id),
    day_of_week     INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    start_time      TEXT NOT NULL,
    end_time        TEXT NOT NULL,
    room            TEXT,
    building        TEXT,
    CHECK (start_time < end_time)
);

CREATE TABLE IF NOT EXISTS course_prerequisites (
    course_id           INTEGER NOT NULL REFERENCES courses(course_id),
    prereq_course_id    INTEGER NOT NULL REFERENCES courses(course_id),
    min_grade           TEXT NOT NULL,
    all_of              INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (course_id, prereq_course_id)
);

CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL REFERENCES students(student_id),
    section_id      INTEGER NOT NULL REFERENCES course_sections(section_id),
    status          TEXT NOT NULL DEFAULT 'enrolling' CHECK (status IN ('enrolling', 'dropped', 'completed', 'failed', 'passed', 'retake_pending')),
    requested_at    TEXT NOT NULL DEFAULT (datetime('now')),
    approved_at     TEXT,
    dropped_at      TEXT,
    grade_mode      TEXT NOT NULL DEFAULT 'normal' CHECK (grade_mode IN ('normal', 'audit')),
    UNIQUE (student_id, section_id)
);

CREATE TABLE IF NOT EXISTS grades (
    grade_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id   INTEGER NOT NULL UNIQUE REFERENCES enrollments(enrollment_id),
    numeric_grade   REAL,
    letter_grade    TEXT,
    grade_points    REAL,
    recorded_at     TEXT NOT NULL DEFAULT (datetime('now')),
    recorded_by     INTEGER NOT NULL REFERENCES instructors(instructor_id),
    is_final        INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS enrollment_overrides (
    override_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id   INTEGER NOT NULL REFERENCES enrollments(enrollment_id),
    override_type   TEXT NOT NULL CHECK (override_type IN ('capacity', 'prerequisite', 'time_conflict', 'retake')),
    approved_by     INTEGER REFERENCES users(user_id),
    approved_at     TEXT,
    reason          TEXT
);

CREATE INDEX IF NOT EXISTS idx_course_sections_course_semester ON course_sections(course_id, semester_id);
CREATE INDEX IF NOT EXISTS idx_section_meetings_section_day ON section_meetings(section_id, day_of_week, start_time);
CREATE INDEX IF NOT EXISTS idx_enrollments_student_section ON enrollments(student_id, section_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_section ON enrollments(section_id);
CREATE INDEX IF NOT EXISTS idx_grades_enrollment ON grades(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_course_prereq_course ON course_prerequisites(course_id);
"""

SAMPLE_DATA_SQL = """
INSERT INTO colleges (college_id, name, dean, contact_email) VALUES
 (1, 'College of Engineering', 'Dr. Ada Lovelace', 'eng-dean@example.edu'),
 (2, 'College of Sciences', 'Dr. Marie Curie', 'sci-dean@example.edu');

INSERT INTO departments (department_id, college_id, name, office_location, contact_email) VALUES
 (1, 1, 'Computer Science and Engineering', 'ENG-201', 'cse@example.edu'),
 (2, 1, 'Electrical Engineering', 'ENG-310', 'ee@example.edu');

INSERT INTO majors (major_id, department_id, name, degree_level, required_credits) VALUES
 (1, 1, 'Software Engineering', 'bachelor', 140),
 (2, 1, 'Computer Science', 'bachelor', 140);

INSERT INTO semesters (semester_id, code, name, start_date, end_date, add_deadline, drop_deadline) VALUES
 (1, '2025FALL', 'Fall 2025', '2025-09-01', '2025-12-20', '2025-09-10', '2025-10-15'),
 (2, '2026SPR', 'Spring 2026', '2026-02-20', '2026-06-10', '2026-03-05', '2026-04-10');

INSERT INTO users (user_id, username, password_hash, role, status) VALUES
 (1, 'alice', 'hash1', 'student', 'approved'),
 (2, 'bob', 'hash2', 'student', 'approved'),
 (3, 'carol', 'hash3', 'instructor', 'approved'),
 (4, 'dave', 'hash4', 'instructor', 'approved'),
 (5, 'admin', 'hash5', 'admin', 'approved');

INSERT INTO students (student_id, user_id, major_id, college_id, full_name, gender, date_of_birth, email, phone, address, enrollment_year, expected_graduation_year)
VALUES
 (1, 1, 1, 1, 'Alice Zhang', 'F', '2004-06-01', 'alice@example.edu', '555-0001', 'Dorm 1', 2023, 2027),
 (2, 2, 2, 1, 'Bob Li', 'M', '2003-08-12', 'bob@example.edu', '555-0002', 'Dorm 2', 2022, 2026);

INSERT INTO instructors (instructor_id, user_id, department_id, full_name, title, email, phone, office)
VALUES
 (1, 3, 1, 'Carol Wang', 'Professor', 'carol@example.edu', '555-1001', 'ENG-410'),
 (2, 4, 1, 'Dave Chen', 'Associate Professor', 'dave@example.edu', '555-1002', 'ENG-420');

INSERT INTO courses (course_id, department_id, course_code, name, credits, course_type, description) VALUES
 (1, 1, 'CSE100', 'Introduction to Programming', 3.0, 'general_required', 'Fundamentals of programming'),
 (2, 1, 'CSE200', 'Data Structures', 3.0, 'major_required', 'Core data structures'),
 (3, 1, 'CSE210', 'Discrete Mathematics', 3.0, 'major_required', 'Logic and combinatorics'),
 (4, 1, 'CSE300', 'Algorithms', 3.0, 'major_required', 'Algorithm design'),
 (5, 1, 'CSE350', 'Operating Systems', 3.0, 'major_required', 'OS concepts'),
 (6, 1, 'CSE360', 'Database Systems', 3.0, 'major_required', 'Relational databases');

INSERT INTO course_prerequisites (course_id, prereq_course_id, min_grade, all_of) VALUES
 (2, 1, 'C', 1),
 (4, 2, 'C', 1),
 (5, 2, 'C', 1),
 (6, 2, 'C', 1);

INSERT INTO course_sections (section_id, course_id, semester_id, instructor_id, section_code, capacity, waitlist_capacity, location_note)
VALUES
 (1, 1, 1, 1, 'A01', 2, 1, 'ENG-101'),
 (2, 2, 1, 1, 'A01', 2, 1, 'ENG-102'),
 (3, 3, 1, 2, 'A01', 2, 1, 'ENG-103'),
 (4, 4, 1, 2, 'A01', 2, 1, 'ENG-104');

INSERT INTO section_meetings (meeting_id, section_id, day_of_week, start_time, end_time, room, building) VALUES
 (1, 1, 1, '09:00', '10:30', '101', 'ENG'),
 (2, 2, 1, '09:30', '11:00', '102', 'ENG'),
 (3, 3, 1, '10:30', '12:00', '103', 'ENG'),
 (4, 4, 1, '09:00', '10:30', '104', 'ENG');

-- Alice has completed Intro and is attempting Data Structures
INSERT INTO enrollments (enrollment_id, student_id, section_id, status, requested_at) VALUES
 (1, 1, 1, 'passed', datetime('now')),
 (2, 1, 2, 'enrolling', datetime('now')),
 (3, 2, 1, 'failed', datetime('now')),
 (4, 2, 4, 'enrolling', datetime('now')),
 (5, 1, 3, 'enrolling', datetime('now'));

INSERT INTO grades (grade_id, enrollment_id, numeric_grade, letter_grade, grade_points, recorded_by) VALUES
 (1, 1, 95, 'A', 4.0, 1),
 (2, 3, 55, 'F', 0.0, 1);

INSERT INTO enrollment_overrides (override_id, enrollment_id, override_type, approved_by, approved_at, reason) VALUES
 (1, 2, 'prerequisite', 5, datetime('now'), 'Prerequisite satisfied after summer session');
"""

def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH, with_sample: bool = False) -> None:
    if db_path.exists():
        db_path.unlink()
    conn = connect(db_path)
    with conn:
        conn.executescript(SCHEMA_SQL)
        if with_sample:
            conn.executescript(SAMPLE_DATA_SQL)
    conn.close()


def load_sample_data(db_path: Path = DB_PATH) -> None:
    conn = connect(db_path)
    with conn:
        conn.executescript(SAMPLE_DATA_SQL)
    conn.close()


def _fetch_one(conn: sqlite3.Connection, query: str, params: Iterable) -> sqlite3.Row | None:
    cur = conn.execute(query, params)
    return cur.fetchone()


def student_id_for_username(conn: sqlite3.Connection, username: str) -> int:
    row = _fetch_one(conn, "SELECT student_id FROM students s JOIN users u ON u.user_id = s.user_id WHERE u.username = ?", (username,))
    if not row:
        raise SystemExit(f"Student username '{username}' not found")
    return int(row[0])


def course_id_for_code(conn: sqlite3.Connection, course_code: str) -> int:
    row = _fetch_one(conn, "SELECT course_id FROM courses WHERE course_code = ?", (course_code,))
    if not row:
        raise SystemExit(f"Course code '{course_code}' not found")
    return int(row[0])


def print_transcript(conn: sqlite3.Connection, student_id: int) -> None:
    rows = conn.execute(
        """
        SELECT sem.code AS semester_code,
               c.course_code,
               c.name AS course_name,
               c.credits,
               e.status,
               g.letter_grade,
               g.numeric_grade,
               g.grade_points
        FROM enrollments e
        JOIN course_sections cs ON cs.section_id = e.section_id
        JOIN courses c ON c.course_id = cs.course_id
        JOIN semesters sem ON sem.semester_id = cs.semester_id
        LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
        WHERE e.student_id = ?
        ORDER BY sem.start_date, c.course_code
        """,
        (student_id,),
    ).fetchall()
    if not rows:
        print("No enrollments found.")
        return

    total_points = 0.0
    total_credits = 0.0
    for row in rows:
        credits = row["credits"]
        gp = row["grade_points"]
        if gp is not None:
            total_points += credits * gp
            total_credits += credits
    gpa = round(total_points / total_credits, 2) if total_credits else None

    print("Semester | Course | Credits | Status | Grade")
    for r in rows:
        grade_display = r["letter_grade"] or ("%.1f" % r["numeric_grade"] if r["numeric_grade"] is not None else "-")
        print(f"{r['semester_code']:9} {r['course_code']:7} {r['credits']:7.1f} {r['status']:9} {grade_display}")
    print(f"Cumulative GPA: {gpa if gpa is not None else 'N/A'}")


def check_prerequisites(conn: sqlite3.Connection, student_id: int, course_id: int) -> List[Tuple[str, str, bool]]:
    prereqs = conn.execute(
        """
        SELECT prereq.prereq_course_id,
               prereq.min_grade,
               c.course_code AS prereq_code
        FROM course_prerequisites prereq
        JOIN courses c ON c.course_id = prereq.prereq_course_id
        WHERE prereq.course_id = ?
        """,
        (course_id,),
    ).fetchall()
    results: List[Tuple[str, str, bool]] = []
    for row in prereqs:
        met = conn.execute(
            """
            SELECT 1
            FROM enrollments e
            JOIN grades g ON g.enrollment_id = e.enrollment_id
            WHERE e.student_id = ? AND e.section_id IN (
                SELECT cs.section_id FROM course_sections cs WHERE cs.course_id = ?
            )
            AND g.grade_points >= (
                CASE ?
                    WHEN 'A' THEN 4.0 WHEN 'A-' THEN 3.7 WHEN 'B+' THEN 3.3 WHEN 'B' THEN 3.0
                    WHEN 'B-' THEN 2.7 WHEN 'C+' THEN 2.3 WHEN 'C' THEN 2.0 WHEN 'D' THEN 1.0 ELSE 0.0
                END
            )
            LIMIT 1
            """,
            (student_id, row["prereq_course_id"], row["min_grade"]),
        ).fetchone()
        results.append((row["prereq_code"], row["min_grade"], bool(met)))
    return results


def check_time_conflict(conn: sqlite3.Connection, student_id: int, requested_section_id: int) -> List[int]:
    rows = conn.execute(
        """
        SELECT DISTINCT existing.section_id
        FROM section_meetings candidate
        JOIN section_meetings existing ON existing.day_of_week = candidate.day_of_week
            AND existing.start_time < candidate.end_time
            AND candidate.start_time < existing.end_time
        JOIN enrollments e ON e.section_id = existing.section_id AND e.student_id = ? AND e.status IN ('enrolling','passed','failed','completed')
        WHERE candidate.section_id = ? AND existing.section_id != candidate.section_id
        """,
        (student_id, requested_section_id),
    ).fetchall()
    return [row[0] for row in rows]


def planned_credits(conn: sqlite3.Connection, student_id: int, semester_code: str) -> float:
    row = _fetch_one(
        conn,
        """
        SELECT SUM(c.credits) AS planned
        FROM enrollments e
        JOIN course_sections cs ON cs.section_id = e.section_id
        JOIN courses c ON c.course_id = cs.course_id
        JOIN semesters sem ON sem.semester_id = cs.semester_id
        WHERE e.student_id = ? AND sem.code = ? AND e.status IN ('enrolling','passed','failed','completed')
        """,
        (student_id, semester_code),
    )
    return float(row[0] or 0.0)


def capacity_status(conn: sqlite3.Connection, section_id: int) -> sqlite3.Row:
    return conn.execute(
        """
        SELECT cs.section_id, cs.capacity, cs.waitlist_capacity,
               SUM(CASE WHEN e.status = 'enrolling' THEN 1 ELSE 0 END) AS enrolled
        FROM course_sections cs
        LEFT JOIN enrollments e ON e.section_id = cs.section_id
        WHERE cs.section_id = ?
        GROUP BY cs.section_id
        """,
        (section_id,),
    ).fetchone()


def pass_rate(conn: sqlite3.Connection, semester_code: str) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT c.course_code, cs.section_code, sem.code AS semester_code,
               SUM(CASE WHEN g.grade_points >= 2.0 THEN 1 ELSE 0 END) AS passed,
               COUNT(g.grade_id) AS graded,
               CASE WHEN COUNT(g.grade_id) = 0 THEN NULL ELSE ROUND(SUM(CASE WHEN g.grade_points >= 2.0 THEN 1 ELSE 0 END) * 1.0 / COUNT(g.grade_id), 2) END AS pass_rate
        FROM course_sections cs
        JOIN courses c ON c.course_id = cs.course_id
        JOIN semesters sem ON sem.semester_id = cs.semester_id
        LEFT JOIN enrollments e ON e.section_id = cs.section_id
        LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
        WHERE sem.code = ?
        GROUP BY c.course_code, cs.section_code, sem.code
        ORDER BY semester_code, course_code, section_code
        """,
        (semester_code,),
    ).fetchall()


def gpa_distribution(conn: sqlite3.Connection, semester_code: str) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT sem.code AS semester_code,
               CAST((g.grade_points * 2) AS INT) / 1.0 / 2 AS bucket_floor,
               COUNT(*) AS student_count
        FROM grades g
        JOIN enrollments e ON e.enrollment_id = g.enrollment_id
        JOIN course_sections cs ON cs.section_id = e.section_id
        JOIN semesters sem ON sem.semester_id = cs.semester_id
        WHERE sem.code = ? AND g.grade_points IS NOT NULL
        GROUP BY sem.code, bucket_floor
        ORDER BY bucket_floor
        """,
        (semester_code,),
    ).fetchall()


def print_table(rows: Iterable[sqlite3.Row]) -> None:
    for row in rows:
        print({k: row[k] for k in row.keys()})


def main() -> None:
    parser = argparse.ArgumentParser(description="SQLite demo for course registration DB")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="Path to SQLite database file (default: university_demo.db)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Create a fresh database (drops existing)")
    sub.add_parser("seed", help="Load sample data into an existing database")

    transcript_cmd = sub.add_parser("transcript", help="Show transcript and GPA for a student username")
    transcript_cmd.add_argument("username")

    prereq_cmd = sub.add_parser("prereq", help="Check whether a student satisfies prerequisites for a course code")
    prereq_cmd.add_argument("username")
    prereq_cmd.add_argument("course_code")

    conflict_cmd = sub.add_parser("conflict", help="Check time conflicts for a student and requested section id")
    conflict_cmd.add_argument("username")
    conflict_cmd.add_argument("section_id", type=int)

    load_cmd = sub.add_parser("credit-load", help="Calculate planned credits for a student in a semester code")
    load_cmd.add_argument("username")
    load_cmd.add_argument("semester_code")

    capacity_cmd = sub.add_parser("capacity", help="Show capacity/enrollment counts for a section id")
    capacity_cmd.add_argument("section_id", type=int)

    passrate_cmd = sub.add_parser("pass-rate", help="Pass rate per section for a semester code")
    passrate_cmd.add_argument("semester_code")

    gpa_cmd = sub.add_parser("gpa-distribution", help="Bucketed GPA distribution for a semester code")
    gpa_cmd.add_argument("semester_code")

    args = parser.parse_args()
    db_path: Path = args.db

    if args.command == "init-db":
        init_db(db_path, with_sample=True)
        print(f"Created database at {db_path} with sample data.")
        return

    if not db_path.exists():
        raise SystemExit(f"Database {db_path} does not exist. Run init-db first.")

    conn = connect(db_path)

    if args.command == "seed":
        load_sample_data(db_path)
        print("Sample data inserted.")
    elif args.command == "transcript":
        sid = student_id_for_username(conn, args.username)
        print_transcript(conn, sid)
    elif args.command == "prereq":
        sid = student_id_for_username(conn, args.username)
        cid = course_id_for_code(conn, args.course_code)
        results = check_prerequisites(conn, sid, cid)
        if not results:
            print("No prerequisites defined for the course.")
        else:
            for prereq_code, min_grade, met in results:
                print(f"{prereq_code} (min {min_grade}): {'OK' if met else 'NOT MET'}")
    elif args.command == "conflict":
        sid = student_id_for_username(conn, args.username)
        conflicts = check_time_conflict(conn, sid, args.section_id)
        if conflicts:
            print("Conflicts with sections:", ", ".join(map(str, conflicts)))
        else:
            print("No conflicts detected.")
    elif args.command == "credit-load":
        sid = student_id_for_username(conn, args.username)
        total = planned_credits(conn, sid, args.semester_code)
        status = "OK" if 10 <= total <= 40 else "OUT_OF_RANGE"
        print(f"Planned credits: {total:.1f} ({status})")
    elif args.command == "capacity":
        row = capacity_status(conn, args.section_id)
        if row:
            print(dict(row))
        else:
            print("Section not found")
    elif args.command == "pass-rate":
        rows = pass_rate(conn, args.semester_code)
        print_table(rows)
    elif args.command == "gpa-distribution":
        rows = gpa_distribution(conn, args.semester_code)
        print_table(rows)
    else:
        parser.error("Unknown command")

    conn.close()


if __name__ == "__main__":
    main()
