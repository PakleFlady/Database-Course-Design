-- Sample data to exercise enrollment, prerequisites, conflicts, and grading
-- Assumes schema.sql has been executed.

-- Reference data
INSERT INTO colleges (name, dean, contact_email) VALUES
 ('College of Engineering', 'Dr. Ada Lovelace', 'eng-dean@example.edu'),
 ('College of Sciences', 'Dr. Marie Curie', 'sci-dean@example.edu');

INSERT INTO departments (college_id, name, office_location, contact_email) VALUES
 (1, 'Computer Science and Engineering', 'ENG-201', 'cse@example.edu'),
 (1, 'Electrical Engineering', 'ENG-310', 'ee@example.edu');

INSERT INTO majors (department_id, name, degree_level, required_credits) VALUES
 (1, 'Software Engineering', 'bachelor', 140),
 (1, 'Computer Science', 'bachelor', 140);

INSERT INTO semesters (code, name, start_date, end_date, add_deadline, drop_deadline) VALUES
 ('2025FALL', 'Fall 2025', '2025-09-01', '2025-12-20', '2025-09-10', '2025-10-15'),
 ('2026SPR', 'Spring 2026', '2026-02-20', '2026-06-10', '2026-03-05', '2026-04-10');

-- Users and profiles
INSERT INTO users (username, password_hash, role, status) VALUES
 ('alice', 'hash1', 'student', 'approved'),
 ('bob', 'hash2', 'student', 'approved'),
 ('carol', 'hash3', 'instructor', 'approved'),
 ('dave', 'hash4', 'instructor', 'approved'),
 ('admin', 'hash5', 'admin', 'approved');

INSERT INTO students (user_id, major_id, college_id, full_name, gender, date_of_birth, email, phone, address, enrollment_year, expected_graduation_year)
VALUES
 (1, 1, 1, 'Alice Zhang', 'F', '2004-06-01', 'alice@example.edu', '555-0001', 'Dorm 1', 2023, 2027),
 (2, 2, 1, 'Bob Li', 'M', '2003-08-12', 'bob@example.edu', '555-0002', 'Dorm 2', 2022, 2026);

INSERT INTO instructors (user_id, department_id, full_name, title, email, phone, office)
VALUES
 (3, 1, 'Carol Wang', 'Professor', 'carol@example.edu', '555-1001', 'ENG-410'),
 (4, 1, 'Dave Chen', 'Associate Professor', 'dave@example.edu', '555-1002', 'ENG-420');

-- Courses
INSERT INTO courses (department_id, course_code, name, credits, course_type, description) VALUES
 (1, 'CSE100', 'Introduction to Programming', 3.0, 'general_required', 'Fundamentals of programming'),
 (1, 'CSE200', 'Data Structures', 3.0, 'major_required', 'Core data structures'),
 (1, 'CSE210', 'Discrete Mathematics', 3.0, 'major_required', 'Logic and combinatorics'),
 (1, 'CSE300', 'Algorithms', 3.0, 'major_required', 'Algorithm design'),
 (1, 'CSE350', 'Operating Systems', 3.0, 'major_required', 'OS concepts'),
 (1, 'CSE360', 'Database Systems', 3.0, 'major_required', 'Relational databases');

-- Prerequisites
INSERT INTO course_prerequisites (course_id, prereq_course_id, min_grade, all_of) VALUES
 (2, 1, 'C', TRUE),  -- Data Structures requires Intro to Programming
 (4, 2, 'C', TRUE),  -- Algorithms requires Data Structures
 (5, 2, 'C', TRUE),  -- Operating Systems requires Data Structures
 (6, 2, 'C', TRUE);  -- Database Systems requires Data Structures

-- Sections and meetings (Fall 2025)
INSERT INTO course_sections (course_id, semester_id, instructor_id, section_code, capacity, waitlist_capacity, location_note)
VALUES
 (1, 1, 3, 'A01', 2, 1, 'ENG-101'),
 (2, 1, 3, 'A01', 2, 1, 'ENG-102'),
 (3, 1, 4, 'A01', 2, 1, 'ENG-103'),
 (4, 1, 4, 'A01', 2, 1, 'ENG-104');

-- Section meetings create conflicts:
INSERT INTO section_meetings (section_id, day_of_week, start_time, end_time, room, building) VALUES
 (1, 1, '09:00', '10:30', '101', 'ENG'), -- Intro Monday
 (2, 1, '09:30', '11:00', '102', 'ENG'), -- Data Structures overlaps for conflict testing
 (3, 1, '10:30', '12:00', '103', 'ENG'), -- Discrete after overlap window
 (4, 1, '09:00', '10:30', '104', 'ENG');  -- Algorithms conflicts with Intro

-- Enrollments
INSERT INTO enrollments (student_id, section_id, status) VALUES
 (1, 1, 'enrolling'), -- Alice in Intro
 (1, 2, 'enrolling'), -- Alice attempts Data Structures (prereq should fail initially)
 (2, 1, 'enrolling'), -- Bob in Intro
 (2, 4, 'enrolling'); -- Bob attempts Algorithms (prereq should fail initially)

-- Grades: Alice passes Intro, Bob fails Intro
INSERT INTO grades (enrollment_id, numeric_grade, letter_grade, grade_points, recorded_by)
VALUES
 (1, 95, 'A', 4.0, 3),
 (3, 55, 'F', 0.0, 3);

-- Overrides: Alice approved to retake Data Structures after passing Intro
INSERT INTO enrollment_overrides (enrollment_id, override_type, approved_by, approved_at, reason)
VALUES
 (2, 'prerequisite', 5, CURRENT_TIMESTAMP, 'Prerequisite satisfied after summer session');

-- Additional enrollment to hit capacity
INSERT INTO enrollments (student_id, section_id, status) VALUES
 (1, 3, 'enrolling');
