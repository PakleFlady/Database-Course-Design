INSERT INTO colleges (college_id, name, dean, contact_email) VALUES
 (1, 'College of Engineering', 'Dr. Ada Lovelace', 'eng-dean@example.edu'),
 (2, 'College of Sciences', 'Dr. Marie Curie', 'sci-dean@example.edu');

INSERT INTO departments (department_id, college_id, name, office_location, contact_email) VALUES
 (1, 1, 'Computer Science and Engineering', 'ENG-201', 'cse@example.edu'),
 (2, 1, 'Electrical Engineering', 'ENG-310', 'ee@example.edu');

INSERT INTO class_groups (class_group_id, department_id, name) VALUES
 (1, 1, 'CS2301');

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

INSERT INTO students (student_id, user_id, student_number, major_id, college_id, department_id, class_group_id, full_name, gender, date_of_birth, email, phone, address, enrollment_year, expected_graduation_year)
VALUES
 (1, 1, '2025001001', 1, 1, 1, 1, 'Alice Zhang', 'F', '2004-06-01', 'alice@example.edu', '555-0001', 'Dorm 1', 2023, 2027),
 (2, 2, '2025001002', 2, 1, 1, 1, 'Bob Li', 'M', '2003-08-12', 'bob@example.edu', '555-0002', 'Dorm 2', 2022, 2026);

INSERT INTO instructors (instructor_id, user_id, department_id, full_name, title, email, phone, office)
VALUES
 (1, 3, 1, 'Carol Wang', 'Professor', 'carol@example.edu', '555-1001', 'ENG-410'),
 (2, 4, 1, 'Dave Chen', 'Associate Professor', 'dave@example.edu', '555-1002', 'ENG-420');

INSERT INTO courses (course_id, department_id, course_code, name, credits, course_type, description) VALUES
 (1, 1, 'CSE100', 'Introduction to Programming', 3.0, 'foundational_required', 'Fundamentals of programming'),
 (2, 1, 'CSE200', 'Data Structures', 3.0, 'major_required', 'Core data structures'),
 (3, 1, 'CSE210', 'Discrete Mathematics', 3.0, 'major_required', 'Logic and combinatorics'),
 (4, 1, 'CSE300', 'Algorithms', 3.0, 'major_required', 'Algorithm design'),
 (5, 1, 'CSE350', 'Operating Systems', 3.0, 'major_required', 'OS concepts'),
 (6, 1, 'CSE360', 'Database Systems', 3.0, 'lab', 'Relational databases and labs');

INSERT INTO course_prerequisites (course_id, prereq_course_id, min_grade, all_of) VALUES
 (2, 1, 'C', 1),
 (4, 2, 'C', 1),
 (5, 2, 'C', 1),
 (6, 2, 'C', 1);

INSERT INTO program_plans (plan_id, department_id, major, academic_year, enrollment_start, enrollment_end, total_credits, is_active) VALUES
 (1, 1, 'Software Engineering', '2025', '2025-08-01', '2025-09-15', 140.0, TRUE);

INSERT INTO program_requirements (requirement_id, plan_id, category, required_credits, recommended_term, selection_start, selection_end, notes) VALUES
 (1, 1, 'foundational_required', 30.0, 'Year 1', '2025-08-01', '2025-09-15', 'Core foundations'),
 (2, 1, 'major_required', 80.0, 'Year 2-3', '2025-08-01', '2025-09-15', 'Major backbone'),
 (3, 1, 'lab', 6.0, 'Year 3', '2025-08-01', '2025-09-15', 'Hands-on labs');

INSERT INTO program_requirement_courses (requirement_id, course_id) VALUES
 (1, 1), (2, 2), (2, 3), (2, 4), (2, 5), (3, 6);

INSERT INTO course_sections (section_id, course_id, semester_id, instructor_id, section_code, capacity, waitlist_capacity, grades_locked, location_note, status, language, grading_scheme, notes)
VALUES
 (1, 1, 1, 1, 'A01', 2, 1, FALSE, 'ENG-101', 'open', 'English', 'numeric', 'Freshman intro'),
 (2, 2, 1, 1, 'A01', 2, 1, FALSE, 'ENG-102', 'open', 'English', 'numeric', 'Requires CSE100'),
 (3, 3, 1, 2, 'A01', 2, 1, FALSE, 'ENG-103', 'open', 'English', 'numeric', NULL),
 (4, 4, 1, 2, 'A01', 2, 1, FALSE, 'ENG-104', 'open', 'English', 'numeric', NULL);

INSERT INTO section_meetings (meeting_id, section_id, day_of_week, start_time, end_time, room, building) VALUES
 (1, 1, 1, '09:00', '10:30', '101', 'ENG'),
 (2, 2, 1, '09:30', '11:00', '102', 'ENG'),
 (3, 3, 1, '10:30', '12:00', '103', 'ENG'),
 (4, 4, 1, '09:00', '10:30', '104', 'ENG');

INSERT INTO enrollments (enrollment_id, student_id, section_id, status, requested_at) VALUES
 (1, 1, 1, 'passed', CURRENT_TIMESTAMP),
 (2, 1, 2, 'enrolling', CURRENT_TIMESTAMP),
 (3, 2, 1, 'failed', CURRENT_TIMESTAMP),
 (4, 2, 4, 'enrolling', CURRENT_TIMESTAMP),
 (5, 1, 3, 'enrolling', CURRENT_TIMESTAMP);

INSERT INTO grades (grade_id, enrollment_id, numeric_grade, letter_grade, grade_points, recorded_by) VALUES
 (1, 1, 95, 'A', 4.0, 1),
 (2, 3, 55, 'F', 0.0, 1);

INSERT INTO enrollment_overrides (override_id, enrollment_id, override_type, approved_by, approved_at, reason) VALUES
 (1, 2, 'prerequisite', 5, CURRENT_TIMESTAMP, 'Prerequisite satisfied after summer session');

INSERT INTO student_requests (request_id, student_id, section_id, request_type, reason, status, reviewed_by, reviewed_at, metadata) VALUES
 (1, 1, 2, 'retake', 'Student passed but wants GPA improvement', 'pending', NULL, NULL, '{"previous_grade": "B"}'),
 (2, 2, 4, 'credit_overload', 'Need extra credits for graduation', 'approved', 5, CURRENT_TIMESTAMP, '{"term_load": 42}');

INSERT INTO approval_logs (approval_log_id, request_id, action, actor, note, created_at) VALUES
 (1, 2, 'approved', 5, 'Allowed overload based on graduation audit', CURRENT_TIMESTAMP);
