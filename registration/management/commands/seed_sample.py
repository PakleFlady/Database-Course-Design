from datetime import date, time
from django.core.management.base import BaseCommand
from registration import models


class Command(BaseCommand):
    help = "导入示例学院、课程、教师、学生和选课数据。"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("创建学院/院系/专业..."))
        sci, _ = models.College.objects.get_or_create(code="CSE", name="计算机科学与工程学院")
        math_college, _ = models.College.objects.get_or_create(code="SCI", name="理学院")

        cs_dept, _ = models.Department.objects.get_or_create(code="CS", name="计算机科学系", college=sci)
        se_dept, _ = models.Department.objects.get_or_create(code="SE", name="软件工程系", college=sci)
        math_dept, _ = models.Department.objects.get_or_create(code="MATH", name="数学系", college=math_college)

        cs_major, _ = models.Major.objects.get_or_create(code="CS-BS", name="计算机科学与技术", department=cs_dept)
        se_major, _ = models.Major.objects.get_or_create(code="SE-BS", name="软件工程", department=se_dept)

        self.stdout.write(self.style.MIGRATE_HEADING("创建学期..."))
        fall, _ = models.Semester.objects.get_or_create(
            code="2025-FALL", name="2025 秋季学期", start_date=date(2025, 9, 1), end_date=date(2026, 1, 10)
        )

        self.stdout.write(self.style.MIGRATE_HEADING("创建课程..."))
        algo, _ = models.Course.objects.get_or_create(
            course_code="CSE200",
            name="算法设计与分析",
            credits=3.0,
            department=cs_dept,
            course_type="MAJOR_REQUIRED",
        )
        dbsys, _ = models.Course.objects.get_or_create(
            course_code="CSE210",
            name="数据库系统",
            credits=3.0,
            department=cs_dept,
            course_type="MAJOR_REQUIRED",
        )
        se_practice, _ = models.Course.objects.get_or_create(
            course_code="SE320",
            name="软件工程综合实践",
            credits=2.0,
            department=se_dept,
            course_type="PRACTICE",
        )
        calc, _ = models.Course.objects.get_or_create(
            course_code="MATH101",
            name="高等数学",
            credits=4.0,
            department=math_dept,
            course_type="GENERAL_REQUIRED",
        )

        models.CoursePrerequisite.objects.get_or_create(course=dbsys, prerequisite=algo, min_grade=60)
        models.CoursePrerequisite.objects.get_or_create(course=se_practice, prerequisite=dbsys, min_grade=70)

        self.stdout.write(self.style.MIGRATE_HEADING("创建教师..."))
        instructor_lee, _ = models.Instructor.objects.get_or_create(
            employee_id="T1001", full_name="李老师", gender="M", email="lee@example.edu", department=cs_dept
        )
        instructor_wang, _ = models.Instructor.objects.get_or_create(
            employee_id="T2001", full_name="王老师", gender="F", email="wang@example.edu", department=se_dept
        )
        instructor_zhang, _ = models.Instructor.objects.get_or_create(
            employee_id="T3001", full_name="张老师", gender="M", email="zhang@example.edu", department=math_dept
        )

        self.stdout.write(self.style.MIGRATE_HEADING("创建课程班..."))
        algo_sec, _ = models.CourseSection.objects.get_or_create(
            course=algo,
            semester=fall,
            section_code="A",
            instructor=instructor_lee,
            capacity=50,
            location="综合楼 301",
            weekday=1,
            start_time=time(8, 0),
            end_time=time(9, 50),
            schedule_notes="周一上午",
        )
        db_sec, _ = models.CourseSection.objects.get_or_create(
            course=dbsys,
            semester=fall,
            section_code="A",
            instructor=instructor_lee,
            capacity=45,
            location="综合楼 302",
            weekday=1,
            start_time=time(10, 0),
            end_time=time(11, 50),
            schedule_notes="紧跟算法课后",
        )
        se_sec, _ = models.CourseSection.objects.get_or_create(
            course=se_practice,
            semester=fall,
            section_code="P1",
            instructor=instructor_wang,
            capacity=30,
            location="实验楼 210",
            weekday=3,
            start_time=time(14, 0),
            end_time=time(16, 50),
            schedule_notes="周三下午实验",
        )
        calc_sec, _ = models.CourseSection.objects.get_or_create(
            course=calc,
            semester=fall,
            section_code="01",
            instructor=instructor_zhang,
            capacity=120,
            location="教学楼 101",
            weekday=1,
            start_time=time(8, 0),
            end_time=time(9, 50),
            schedule_notes="时间与算法冲突",
        )

        self.stdout.write(self.style.MIGRATE_HEADING("创建学生与选课..."))
        alice, _ = models.Student.objects.get_or_create(
            student_id="S2025001",
            full_name="Alice",
            gender="F",
            date_of_birth=date(2005, 5, 12),
            email="alice@example.edu",
            phone="13800000001",
            college=sci,
            major=cs_major,
        )
        bob, _ = models.Student.objects.get_or_create(
            student_id="S2025002",
            full_name="Bob",
            gender="M",
            date_of_birth=date(2004, 8, 8),
            email="bob@example.edu",
            phone="13800000002",
            college=sci,
            major=se_major,
        )

        models.Enrollment.objects.get_or_create(student=alice, section=algo_sec, status="PASSED", final_grade=85, grade_letter="B+", grade_points=3.5)
        models.Enrollment.objects.get_or_create(student=alice, section=db_sec, status="ENROLLED")
        models.Enrollment.objects.get_or_create(student=alice, section=calc_sec, status="FAILED", final_grade=55, grade_letter="F", grade_points=0)
        models.Enrollment.objects.get_or_create(student=bob, section=algo_sec, status="PASSED", final_grade=78, grade_letter="C+", grade_points=2.7)
        models.Enrollment.objects.get_or_create(student=bob, section=se_sec, status="RETAKE")

        self.stdout.write(self.style.SUCCESS("示例数据已准备完毕，可在 Django Admin 中查看/维护。"))
