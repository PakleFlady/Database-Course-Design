-- Schema for University Course Registration and Grade Management System
-- Target: ANSI SQL (PostgreSQL-friendly)

CREATE TABLE colleges (
    college_id      SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL UNIQUE,
    dean            VARCHAR(255),
    contact_email   VARCHAR(255)
);

CREATE TABLE departments (
    department_id   SERIAL PRIMARY KEY,
    college_id      INTEGER NOT NULL REFERENCES colleges(college_id),
    name            VARCHAR(255) NOT NULL,
    office_location VARCHAR(255),
    contact_email   VARCHAR(255),
    UNIQUE (college_id, name)
);

CREATE TABLE majors (
    major_id        SERIAL PRIMARY KEY,
    department_id   INTEGER NOT NULL REFERENCES departments(department_id),
    name            VARCHAR(255) NOT NULL,
    degree_level    VARCHAR(50) NOT NULL CHECK (degree_level IN ('bachelor', 'master', 'phd')),
    required_credits INTEGER NOT NULL CHECK (required_credits > 0),
    UNIQUE (department_id, name)
);

CREATE TABLE semesters (
    semester_id     SERIAL PRIMARY KEY,
    code            VARCHAR(20) NOT NULL UNIQUE,
    name            VARCHAR(100) NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    add_deadline    DATE,
    drop_deadline   DATE,
    CHECK (start_date < end_date)
);

CREATE TABLE users (
    user_id         SERIAL PRIMARY KEY,
    username        VARCHAR(100) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('student', 'instructor', 'admin')),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'disabled')),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE students (
    student_id      SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL UNIQUE REFERENCES users(user_id),
    major_id        INTEGER NOT NULL REFERENCES majors(major_id),
    college_id      INTEGER NOT NULL REFERENCES colleges(college_id),
    full_name       VARCHAR(255) NOT NULL,
    gender          VARCHAR(20),
    date_of_birth   DATE,
    email           VARCHAR(255),
    phone           VARCHAR(50),
    address         VARCHAR(255),
    enrollment_year INTEGER CHECK (enrollment_year >= 1900),
    expected_graduation_year INTEGER,
    gpa_cache       NUMERIC(3,2)
);

CREATE TABLE instructors (
    instructor_id   SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL UNIQUE REFERENCES users(user_id),
    department_id   INTEGER NOT NULL REFERENCES departments(department_id),
    full_name       VARCHAR(255) NOT NULL,
    title           VARCHAR(100),
    email           VARCHAR(255),
    phone           VARCHAR(50),
    office          VARCHAR(100),
    status          VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'on_leave', 'retired'))
);

CREATE TABLE courses (
    course_id       SERIAL PRIMARY KEY,
    department_id   INTEGER NOT NULL REFERENCES departments(department_id),
    course_code     VARCHAR(50) NOT NULL UNIQUE,
    name            VARCHAR(255) NOT NULL,
    credits         NUMERIC(3,1) NOT NULL CHECK (credits > 0),
    course_type     VARCHAR(40) NOT NULL CHECK (course_type IN ('general_required', 'major_required', 'major_elective', 'university_elective', 'practical')),
    description     TEXT,
    repeatable      BOOLEAN NOT NULL DEFAULT FALSE,
    active          BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE course_sections (
    section_id      SERIAL PRIMARY KEY,
    course_id       INTEGER NOT NULL REFERENCES courses(course_id),
    semester_id     INTEGER NOT NULL REFERENCES semesters(semester_id),
    instructor_id   INTEGER NOT NULL REFERENCES instructors(instructor_id),
    section_code    VARCHAR(20) NOT NULL,
    capacity        INTEGER NOT NULL CHECK (capacity >= 0),
    waitlist_capacity INTEGER NOT NULL DEFAULT 0 CHECK (waitlist_capacity >= 0),
    location_note   VARCHAR(255),
    status          VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('planned', 'open', 'closed', 'cancelled')),
    language        VARCHAR(30) DEFAULT 'English',
    grading_scheme  VARCHAR(20) NOT NULL DEFAULT 'numeric' CHECK (grading_scheme IN ('numeric', 'letter', 'pass_fail')),
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (course_id, semester_id, section_code)
);

CREATE TABLE section_meetings (
    meeting_id      SERIAL PRIMARY KEY,
    section_id      INTEGER NOT NULL REFERENCES course_sections(section_id),
    day_of_week     INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    start_time      TIME NOT NULL,
    end_time        TIME NOT NULL,
    room            VARCHAR(50),
    building        VARCHAR(50),
    CHECK (start_time < end_time)
);

CREATE TABLE course_prerequisites (
    course_id           INTEGER NOT NULL REFERENCES courses(course_id),
    prereq_course_id    INTEGER NOT NULL REFERENCES courses(course_id),
    min_grade           VARCHAR(5) NOT NULL,
    all_of              BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (course_id, prereq_course_id)
);

CREATE TABLE enrollments (
    enrollment_id   SERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL REFERENCES students(student_id),
    section_id      INTEGER NOT NULL REFERENCES course_sections(section_id),
    status          VARCHAR(20) NOT NULL DEFAULT 'enrolling' CHECK (status IN ('enrolling', 'waitlisted', 'dropped', 'completed', 'failed', 'passed', 'retake_pending')),
    requested_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at     TIMESTAMP,
    dropped_at      TIMESTAMP,
    grade_mode      VARCHAR(20) NOT NULL DEFAULT 'normal' CHECK (grade_mode IN ('normal', 'audit')),
    UNIQUE (student_id, section_id)
);

CREATE TABLE grades (
    grade_id        SERIAL PRIMARY KEY,
    enrollment_id   INTEGER NOT NULL UNIQUE REFERENCES enrollments(enrollment_id),
    numeric_grade   NUMERIC(5,2),
    letter_grade    VARCHAR(5),
    grade_points    NUMERIC(3,2),
    recorded_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    recorded_by     INTEGER NOT NULL REFERENCES instructors(instructor_id),
    is_final        BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE enrollment_overrides (
    override_id     SERIAL PRIMARY KEY,
    enrollment_id   INTEGER NOT NULL REFERENCES enrollments(enrollment_id),
    override_type   VARCHAR(30) NOT NULL CHECK (override_type IN ('capacity', 'prerequisite', 'time_conflict', 'retake')),
    approved_by     INTEGER REFERENCES users(user_id),
    approved_at     TIMESTAMP,
    reason          TEXT
);

-- Indexes for performance
CREATE INDEX idx_course_sections_course_semester ON course_sections(course_id, semester_id);
CREATE INDEX idx_section_meetings_section_day ON section_meetings(section_id, day_of_week, start_time);
CREATE INDEX idx_enrollments_student_section ON enrollments(student_id, section_id);
CREATE INDEX idx_enrollments_section ON enrollments(section_id);
CREATE INDEX idx_grades_enrollment ON grades(enrollment_id);
CREATE INDEX idx_course_prereq_course ON course_prerequisites(course_id);
