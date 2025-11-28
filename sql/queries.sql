-- Common queries for the University Course Registration and Grade Management System

-- 1. Student transcript with GPA calculation
WITH transcript AS (
    SELECT s.student_id,
           c.course_code,
           c.name AS course_name,
           c.credits,
           g.letter_grade,
           g.numeric_grade,
           g.grade_points,
           sem.code AS semester_code
    FROM enrollments e
    JOIN students s ON s.student_id = e.student_id
    JOIN course_sections cs ON cs.section_id = e.section_id
    JOIN courses c ON c.course_id = cs.course_id
    JOIN semesters sem ON sem.semester_id = cs.semester_id
    LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
    WHERE e.status IN ('completed', 'passed', 'failed')
)
SELECT t.*, 
       ROUND(SUM(t.grade_points * t.credits) OVER (PARTITION BY t.student_id) /
             NULLIF(SUM(t.credits) OVER (PARTITION BY t.student_id), 0), 2) AS cumulative_gpa
FROM transcript t
ORDER BY t.student_id, t.semester_code, t.course_code;

-- 2. Courses taken by a student with pass/fail indicator
SELECT c.course_code,
       c.name,
       c.credits,
       g.letter_grade,
       g.numeric_grade,
       CASE WHEN e.status IN ('failed') OR (g.grade_points IS NOT NULL AND g.grade_points < 2.0)
            THEN 'needs_retake' ELSE 'passed' END AS completion_status
FROM enrollments e
JOIN course_sections cs ON cs.section_id = e.section_id
JOIN courses c ON c.course_id = cs.course_id
LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
WHERE e.student_id = :student_id
ORDER BY cs.section_id;

-- 3. Prerequisite validation for a requested course
SELECT prereq.prereq_course_id, prereq.min_grade
FROM course_prerequisites prereq
WHERE prereq.course_id = :course_id
EXCEPT
SELECT c.course_id, prereq.min_grade
FROM course_prerequisites prereq
JOIN courses c ON c.course_id = prereq.prereq_course_id
JOIN course_sections cs ON cs.course_id = c.course_id
JOIN enrollments e ON e.section_id = cs.section_id AND e.student_id = :student_id
JOIN grades g ON g.enrollment_id = e.enrollment_id
WHERE g.grade_points IS NOT NULL AND g.grade_points >=
      CASE prereq.min_grade
           WHEN 'A' THEN 4.0 WHEN 'A-' THEN 3.7 WHEN 'B+' THEN 3.3 WHEN 'B' THEN 3.0
           WHEN 'B-' THEN 2.7 WHEN 'C+' THEN 2.3 WHEN 'C' THEN 2.0 WHEN 'D' THEN 1.0 ELSE 0.0 END;
-- If result set is empty, prerequisites are satisfied.

-- 4. Student timetable credit load validation for a semester
SELECT SUM(c.credits) AS planned_credits
FROM enrollments e
JOIN course_sections cs ON cs.section_id = e.section_id
JOIN courses c ON c.course_id = cs.course_id
WHERE e.student_id = :student_id AND cs.semester_id = :semester_id AND e.status IN ('enrolling', 'passed', 'failed', 'completed');
-- Application should enforce planned_credits BETWEEN 10 AND 40.

-- 5. Time conflict detection for a student when enrolling into a new section
SELECT existing.section_id AS conflicting_section
FROM section_meetings candidate
JOIN section_meetings existing ON existing.day_of_week = candidate.day_of_week
    AND existing.start_time < candidate.end_time
    AND candidate.start_time < existing.end_time
JOIN enrollments e ON e.section_id = existing.section_id AND e.student_id = :student_id AND e.status IN ('enrolling', 'passed', 'failed', 'completed')
WHERE candidate.section_id = :requested_section_id;

-- 6. Instructor time conflict detection before assigning a section
SELECT cs.section_id, sm.day_of_week, sm.start_time, sm.end_time
FROM course_sections cs
JOIN section_meetings sm ON sm.section_id = cs.section_id
WHERE cs.instructor_id = :instructor_id AND sm.day_of_week = :day_of_week
  AND sm.start_time < :candidate_end_time AND :candidate_start_time < sm.end_time;

-- 7. Pass rate per course offering
SELECT c.course_code, cs.section_code, sem.code AS semester_code,
       COUNT(g.grade_id) FILTER (WHERE g.grade_points >= 2.0) AS passed,
       COUNT(g.grade_id) AS graded,
       ROUND(COUNT(g.grade_id) FILTER (WHERE g.grade_points >= 2.0)::NUMERIC / NULLIF(COUNT(g.grade_id), 0), 2) AS pass_rate
FROM course_sections cs
JOIN courses c ON c.course_id = cs.course_id
JOIN semesters sem ON sem.semester_id = cs.semester_id
LEFT JOIN enrollments e ON e.section_id = cs.section_id
LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
GROUP BY c.course_code, cs.section_code, sem.code
ORDER BY semester_code, course_code, section_code;

-- 8. GPA distribution for a semester
SELECT sem.code AS semester_code,
       width_bucket(g.grade_points, 0, 4, 8) AS gpa_bucket,
       COUNT(*) AS student_count
FROM grades g
JOIN enrollments e ON e.enrollment_id = g.enrollment_id
JOIN course_sections cs ON cs.section_id = e.section_id
JOIN semesters sem ON sem.semester_id = cs.semester_id
WHERE sem.semester_id = :semester_id AND g.grade_points IS NOT NULL
GROUP BY sem.code, width_bucket(g.grade_points, 0, 4, 8)
ORDER BY gpa_bucket;

-- 9. Curriculum lookup by course type for a major
SELECT c.course_code, c.name, c.credits, c.course_type
FROM courses c
JOIN departments d ON d.department_id = c.department_id
JOIN majors m ON m.department_id = d.department_id
WHERE m.major_id = :major_id AND c.course_type = :course_type AND c.active = TRUE;

-- 10. Waitlist and capacity status for a section
SELECT cs.section_id, cs.capacity, cs.waitlist_capacity,
       COUNT(e.enrollment_id) FILTER (WHERE e.status = 'enrolling') AS enrolled,
       COUNT(e.enrollment_id) FILTER (WHERE e.status = 'waitlisted') AS waitlisted
FROM course_sections cs
LEFT JOIN enrollments e ON e.section_id = cs.section_id
WHERE cs.section_id = :section_id
GROUP BY cs.section_id, cs.capacity, cs.waitlist_capacity;
