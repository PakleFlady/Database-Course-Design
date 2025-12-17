"""Populate the database with demo users, courses, sections, and enrollments."""
from __future__ import annotations

import datetime
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings

from registrar.models import (
    ClassGroup,
    Course,
    CoursePrerequisite,
    CourseSection,
    Department,
    Enrollment,
    InstructorProfile,
    MeetingTime,
    ProgramPlan,
    ProgramRequirement,
    Semester,
    StudentProfile,
    UserSecurity,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with demo data for admin exploration"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Creating demo data..."))

        cse, _ = Department.objects.get_or_create(code="CSE", defaults={"name": "计算机科学与工程学院"})
        math, _ = Department.objects.get_or_create(code="MATH", defaults={"name": "数学系"})
        ee, _ = Department.objects.get_or_create(code="EE", defaults={"name": "电子与信息工程学院"})
        bus, _ = Department.objects.get_or_create(code="BUS", defaults={"name": "经济管理学院"})

        cse_class_a, _ = ClassGroup.objects.get_or_create(name="软件2301", department=cse)
        cse_class_b, _ = ClassGroup.objects.get_or_create(name="计科2301", department=cse)
        cse_class_c, _ = ClassGroup.objects.get_or_create(name="网安2301", department=cse)
        cse_class_d, _ = ClassGroup.objects.get_or_create(name="人工智能2301", department=cse)
        math_class_a, _ = ClassGroup.objects.get_or_create(name="数院2301", department=math)
        math_class_b, _ = ClassGroup.objects.get_or_create(name="统计2301", department=math)
        ee_class_a, _ = ClassGroup.objects.get_or_create(name="信息2301", department=ee)
        ee_class_b, _ = ClassGroup.objects.get_or_create(name="智能2301", department=ee)
        bus_class_a, _ = ClassGroup.objects.get_or_create(name="信管2301", department=bus)
        bus_class_b, _ = ClassGroup.objects.get_or_create(name="工商2301", department=bus)

        class_groups = {
            cse: [cse_class_a, cse_class_b, cse_class_c, cse_class_d],
            math: [math_class_a, math_class_b],
            ee: [ee_class_a, ee_class_b],
            bus: [bus_class_a, bus_class_b],
        }

        fall, _ = Semester.objects.get_or_create(
            code="2025FALL",
            defaults={
                "name": "2025 秋季学期",
                "start_date": datetime.date(2025, 9, 1),
                "end_date": datetime.date(2026, 1, 10),
            },
        )
        spring, _ = Semester.objects.get_or_create(
            code="2025SPRING",
            defaults={
                "name": "2025 春季学期",
                "start_date": datetime.date(2025, 2, 20),
                "end_date": datetime.date(2025, 7, 1),
            },
        )

        def ensure_password_and_security(user: User):
            if not user.password or not user.has_usable_password():
                user.set_password(settings.DEFAULT_INITIAL_PASSWORD)
                user.save(update_fields=["password"])
            security, _ = UserSecurity.objects.get_or_create(user=user)
            if not user.is_staff and not user.is_superuser:
                security.must_change_password = True
                security.save(update_fields=["must_change_password"])

        admin_user, created_admin = User.objects.get_or_create(username="admin", defaults={"email": "admin@example.com"})
        if created_admin:
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.set_password("admin123")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin / admin123"))
        ensure_password_and_security(admin_user)

        instructors_data = [
            ("carol", "Carol", cse, "副教授"),
            ("dave", "Dave", math, "讲师"),
            ("erin", "Erin", cse, "教授"),
            ("frank", "Frank", ee, "副教授"),
            ("henry", "Henry", bus, "副教授"),
            ("irene", "Irene", cse, "讲师"),
        ]
        instructor_profiles: dict[str, InstructorProfile] = {}
        for username, first_name, dept, title in instructors_data:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first_name, "email": f"{username}@example.com"},
            )
            ensure_password_and_security(user)
            profile, _ = InstructorProfile.objects.get_or_create(user=user, defaults={"department": dept, "title": title})
            instructor_profiles[username] = profile

        named_students = [
            ("alice", "Alice", "female", cse, cse_class_a, "软件工程"),
            ("bob", "Bob", "male", cse, cse_class_b, "计算机科学与技术"),
            ("charlie", "Charlie", "male", cse, cse_class_b, "人工智能"),
            ("diana", "Diana", "female", cse, cse_class_a, "软件工程"),
            ("eric", "Eric", "male", cse, cse_class_b, "数据科学"),
            ("fiona", "Fiona", "female", ee, ee_class_a, "信息工程"),
            ("grace", "Grace", "female", bus, bus_class_a, "信息管理与信息系统"),
        ]

        student_profiles: list[StudentProfile] = []
        for username, first_name, gender, dept, group, major in named_students:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first_name, "email": f"{username}@example.com"},
            )
            ensure_password_and_security(user)
            profile, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    "gender": gender,
                    "department": dept,
                    "class_group": group,
                    "major": major,
                    "contact_email": f"{username}@example.com",
                },
            )
            if not profile.student_number:
                profile.save()
            student_profiles.append(profile)

        majors_map = {
            cse: ["软件工程", "计算机科学与技术", "人工智能", "网络安全", "数据科学"],
            math: ["应用数学", "统计学", "金融数学"],
            ee: ["电子信息工程", "通信工程", "智能感知"],
            bus: ["信息管理与信息系统", "工商管理", "金融科技"],
        }
        dept_cycle = [cse, math, ee, bus]
        for idx in range(1, 111):
            username = f"stu{idx:03d}"
            dept = dept_cycle[idx % len(dept_cycle)]
            group = class_groups[dept][idx % len(class_groups[dept])]
            major_choices = majors_map[dept]
            major = major_choices[idx % len(major_choices)]
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"first_name": f"学生{idx:03d}", "email": f"{username}@example.com"},
            )
            ensure_password_and_security(user)
            profile, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    "gender": "male" if idx % 2 else "female",
                    "department": dept,
                    "class_group": group,
                    "major": major,
                    "contact_email": f"{username}@example.com",
                },
            )
            if not profile.student_number:
                profile.save()
            student_profiles.append(profile)

        course_rows = [
            {"code": "CSE100", "name": "程序设计基础", "credits": 3.0, "department": cse, "course_type": "foundational_required"},
            {"code": "CSE110", "name": "面向对象程序设计", "credits": 3.0, "department": cse, "course_type": "major_required"},
            {"code": "CSE120", "name": "计算机系统导论", "credits": 3.0, "department": cse, "course_type": "foundational_required"},
            {"code": "CSE130", "name": "离散数学", "credits": 3.0, "department": cse, "course_type": "foundational_required"},
            {"code": "CSE140", "name": "线性代数 A", "credits": 3.0, "department": cse, "course_type": "foundational_required"},
            {"code": "CSE150", "name": "程序设计实践", "credits": 2.0, "department": cse, "course_type": "lab"},
            {"code": "CSE160", "name": "Web 开发基础", "credits": 2.0, "department": cse, "course_type": "general_elective"},
            {"code": "CSE170", "name": "移动应用开发", "credits": 2.0, "department": cse, "course_type": "major_elective"},
            {"code": "CSE180", "name": "Python 数据分析", "credits": 2.0, "department": cse, "course_type": "major_elective"},
            {"code": "CSE190", "name": "云计算概论", "credits": 2.5, "department": cse, "course_type": "major_elective"},
            {"code": "CSE200", "name": "数据结构", "credits": 3.0, "department": cse, "course_type": "major_required"},
            {"code": "CSE210", "name": "数据库系统", "credits": 3.0, "department": cse, "course_type": "major_required"},
            {"code": "CSE215", "name": "数据库实践", "credits": 1.5, "department": cse, "course_type": "lab"},
            {"code": "CSE220", "name": "操作系统", "credits": 3.0, "department": cse, "course_type": "major_required"},
            {"code": "CSE230", "name": "计算机网络", "credits": 3.0, "department": cse, "course_type": "major_required"},
            {"code": "CSE240", "name": "算法设计与分析", "credits": 3.0, "department": cse, "course_type": "major_required"},
            {"code": "CSE250", "name": "人工智能导论", "credits": 3.0, "department": cse, "course_type": "major_elective"},
            {"code": "CSE260", "name": "机器学习", "credits": 3.0, "department": cse, "course_type": "major_elective"},
            {"code": "CSE270", "name": "分布式系统", "credits": 3.0, "department": cse, "course_type": "major_required"},
            {"code": "CSE280", "name": "信息安全导论", "credits": 2.5, "department": cse, "course_type": "major_required"},
            {"code": "CSE290", "name": "软件工程", "credits": 3.0, "department": cse, "course_type": "major_required"},
            {"code": "CSE300", "name": "深度学习", "credits": 3.0, "department": cse, "course_type": "major_elective"},
            {"code": "CSE310", "name": "大数据处理", "credits": 3.0, "department": cse, "course_type": "major_elective"},
            {"code": "CSE320", "name": "编译原理", "credits": 3.0, "department": cse, "course_type": "major_required"},
            {"code": "CSE330", "name": "计算机图形学", "credits": 3.0, "department": cse, "course_type": "major_elective"},
            {"code": "CSE340", "name": "推荐系统基础", "credits": 2.5, "department": cse, "course_type": "major_elective"},
            {"code": "MATH101", "name": "高等数学 I", "credits": 4.0, "department": math, "course_type": "foundational_required"},
            {"code": "MATH102", "name": "高等数学 II", "credits": 4.0, "department": math, "course_type": "foundational_required"},
            {"code": "MATH120", "name": "概率与统计", "credits": 3.0, "department": math, "course_type": "foundational_required"},
            {"code": "MATH130", "name": "数学建模", "credits": 2.0, "department": math, "course_type": "major_elective"},
            {"code": "MATH140", "name": "数理逻辑", "credits": 2.5, "department": math, "course_type": "major_elective"},
            {"code": "MATH150", "name": "组合数学", "credits": 3.0, "department": math, "course_type": "major_required"},
            {"code": "MATH160", "name": "数值分析", "credits": 3.0, "department": math, "course_type": "major_required"},
            {"code": "MATH170", "name": "线性代数 B", "credits": 3.0, "department": math, "course_type": "foundational_required"},
            {"code": "MATH180", "name": "随机过程", "credits": 2.5, "department": math, "course_type": "major_elective"},
            {"code": "MATH190", "name": "金融数学", "credits": 3.0, "department": math, "course_type": "major_elective"},
            {"code": "EE150", "name": "数字电路基础", "credits": 2.5, "department": ee, "course_type": "major_required"},
            {"code": "EE160", "name": "模拟电路", "credits": 2.5, "department": ee, "course_type": "major_required"},
            {"code": "EE170", "name": "信号与系统", "credits": 3.0, "department": ee, "course_type": "major_required"},
            {"code": "EE180", "name": "通信原理", "credits": 3.0, "department": ee, "course_type": "major_required"},
            {"code": "EE190", "name": "嵌入式系统", "credits": 2.5, "department": ee, "course_type": "lab"},
            {"code": "EE200", "name": "计算机组成", "credits": 3.0, "department": ee, "course_type": "major_required"},
            {"code": "EE210", "name": "物联网概论", "credits": 2.0, "department": ee, "course_type": "general_elective"},
            {"code": "EE220", "name": "数字信号处理", "credits": 3.0, "department": ee, "course_type": "major_elective"},
            {"code": "EE230", "name": "自动控制原理", "credits": 3.0, "department": ee, "course_type": "major_required"},
            {"code": "EE240", "name": "电子测量与仪表", "credits": 2.5, "department": ee, "course_type": "major_elective"},
            {"code": "BUS110", "name": "管理学原理", "credits": 2.0, "department": bus, "course_type": "general_elective"},
            {"code": "BUS120", "name": "运营管理", "credits": 2.5, "department": bus, "course_type": "general_elective"},
            {"code": "BUS130", "name": "财务管理", "credits": 2.5, "department": bus, "course_type": "general_elective"},
            {"code": "BUS140", "name": "市场营销", "credits": 2.5, "department": bus, "course_type": "general_elective"},
            {"code": "BUS150", "name": "项目管理", "credits": 2.0, "department": bus, "course_type": "general_elective"},
            {"code": "BUS160", "name": "数据可视化", "credits": 2.0, "department": bus, "course_type": "general_elective"},
            {"code": "BUS170", "name": "管理信息系统", "credits": 2.5, "department": bus, "course_type": "general_elective"},
            {"code": "BUS180", "name": "组织行为学", "credits": 2.0, "department": bus, "course_type": "general_elective"},
            {"code": "BUS190", "name": "商业伦理", "credits": 2.0, "department": bus, "course_type": "general_elective"},
            {"code": "BUS200", "name": "供应链管理", "credits": 2.5, "department": bus, "course_type": "general_elective"},
        ]

        for row in course_rows:
            Course.objects.get_or_create(code=row["code"], defaults=row)

        course_lookup = {c.code: c for c in Course.objects.filter(code__in=[row["code"] for row in course_rows])}

        prerequisite_rows = [
            ("CSE200", "CSE100", "C"),
            ("CSE210", "CSE200", "C"),
            ("CSE215", "CSE210", "C"),
            ("CSE220", "CSE200", "C"),
            ("CSE230", "CSE200", "C"),
            ("CSE260", "CSE250", "B"),
            ("CSE270", "CSE220", "C"),
            ("CSE320", "CSE220", "C"),
            ("EE180", "EE170", "C"),
            ("EE200", "EE150", "D"),
        ]
        for course_code, prereq_code, min_grade in prerequisite_rows:
            course = course_lookup.get(course_code)
            prereq = course_lookup.get(prereq_code)
            if course and prereq:
                CoursePrerequisite.objects.get_or_create(course=course, prerequisite=prereq, defaults={"min_grade": min_grade})

        section_specs = [
            ("CSE100", fall, 1, instructor_profiles.get("carol"), 120),
            ("CSE110", fall, 1, instructor_profiles.get("carol"), 90),
            ("CSE200", fall, 1, instructor_profiles.get("carol"), 80),
            ("CSE210", fall, 1, instructor_profiles.get("dave"), 70),
            ("CSE220", fall, 1, instructor_profiles.get("erin"), 70),
            ("CSE230", fall, 1, instructor_profiles.get("erin"), 70),
            ("CSE240", fall, 1, instructor_profiles.get("carol"), 70),
            ("CSE250", fall, 1, instructor_profiles.get("dave"), 60),
            ("CSE260", fall, 1, instructor_profiles.get("dave"), 60),
            ("CSE270", fall, 1, instructor_profiles.get("irene"), 60),
            ("CSE290", fall, 1, instructor_profiles.get("irene"), 60),
            ("MATH101", fall, 1, instructor_profiles.get("dave"), 120),
            ("MATH120", fall, 1, instructor_profiles.get("dave"), 110),
            ("EE170", fall, 1, instructor_profiles.get("frank"), 90),
            ("EE180", fall, 1, instructor_profiles.get("frank"), 90),
            ("BUS110", fall, 1, instructor_profiles.get("henry"), 150),
            ("BUS170", fall, 1, instructor_profiles.get("henry"), 140),
        ]

        created_sections: list[CourseSection] = []
        for code, semester, sec_no, instructor, capacity in section_specs:
            course = course_lookup.get(code)
            if not course or not instructor:
                continue
            section, _ = CourseSection.objects.get_or_create(
                course=course,
                semester=semester,
                section_number=sec_no,
                defaults={"instructor": instructor, "capacity": capacity},
            )
            created_sections.append(section)

        for idx, section in enumerate(created_sections, start=1):
            MeetingTime.objects.get_or_create(
                section=section,
                day_of_week=((idx % 5) + 1),
                start_time=datetime.time(8 + (idx % 3) * 2, 0),
                end_time=datetime.time(9 + (idx % 3) * 2, 50),
                defaults={"location": f"A{100 + idx}"},
            )

        def calc_points(score: float | None):
            if score is None:
                return None
            if score >= 90:
                return 4.0
            if score >= 80:
                return 3.0
            if score >= 70:
                return 2.0
            if score >= 60:
                return 1.0
            return 0.0

        status_pattern = [("passed", 95), ("passed", 85), ("failed", 55), ("enrolling", None), ("passed", 72)]
        sections_for_enroll = created_sections[:10]
        if not sections_for_enroll:
            self.stdout.write(self.style.ERROR("No sections were created; cannot seed enrollments."))
            return
        for idx, student in enumerate(student_profiles[:100]):
            primary_section = sections_for_enroll[idx % len(sections_for_enroll)]
            status, grade = status_pattern[idx % len(status_pattern)]
            Enrollment.objects.update_or_create(
                student=student,
                section=primary_section,
                defaults={
                    "status": status,
                    "final_grade": grade,
                    "grade_points": calc_points(grade),
                },
            )

            secondary_section = sections_for_enroll[(idx + 3) % len(sections_for_enroll)]
            sec_status, sec_grade = status_pattern[(idx + 2) % len(status_pattern)]
            Enrollment.objects.update_or_create(
                student=student,
                section=secondary_section,
                defaults={
                    "status": sec_status,
                    "final_grade": sec_grade,
                    "grade_points": calc_points(sec_grade),
                },
            )

        cse_plan_defaults = {
            "total_credits": 140,
            "enrollment_start": datetime.date(2025, 2, 10),
            "enrollment_end": datetime.date(2025, 3, 10),
        }
        cse_plan, _ = ProgramPlan.objects.get_or_create(
            name="计算机科学与技术培养方案（2025版）",
            department=cse,
            major="计算机科学与技术/软件工程",
            academic_year="2025",
            defaults=cse_plan_defaults,
        )
        for field, value in cse_plan_defaults.items():
            setattr(cse_plan, field, value)
        cse_plan.is_active = True
        cse_plan.save()

        cse_requirement_rows = [
            ("foundational_required", 36, "大一-大二", ["CSE100", "CSE120", "CSE130", "CSE140", "MATH101", "MATH102", "MATH170"]),
            ("major_required", 60, "大二-大三", ["CSE110", "CSE200", "CSE210", "CSE215", "CSE220", "CSE230", "CSE240", "CSE270", "CSE280", "CSE290", "CSE320"]),
            ("major_elective", 30, "大三-大四", ["CSE250", "CSE260", "CSE300", "CSE310", "CSE330", "CSE340", "CSE170", "CSE180", "CSE190"]),
            ("general_elective", 16, "贯穿学年", ["BUS110", "BUS140", "BUS170", "BUS200", "EE210", "EE180", "EE220"]),
            ("lab", 8, "每学年", ["CSE150", "CSE215", "EE190"]),
        ]

        for category, credits, term, course_codes in cse_requirement_rows:
            req, _ = ProgramRequirement.objects.get_or_create(
                plan=cse_plan,
                category=category,
                recommended_term=term,
                defaults={"required_credits": credits, "selection_start": cse_plan.enrollment_start, "selection_end": cse_plan.enrollment_end},
            )
            req.required_credits = credits
            req.selection_start = cse_plan.enrollment_start
            req.selection_end = cse_plan.enrollment_end
            req.notes = "自动导入的示例培养方案，可在后台调整或复制。"
            req.save()
            req.courses.set([course_lookup[c] for c in course_codes if c in course_lookup])

        math_plan, _ = ProgramPlan.objects.get_or_create(
            name="数学与应用数学方案（2025版）",
            department=math,
            major="数学与应用数学",
            academic_year="2025",
            defaults={
                "total_credits": 130,
                "enrollment_start": datetime.date(2025, 2, 15),
                "enrollment_end": datetime.date(2025, 3, 8),
            },
        )
        math_plan.is_active = True
        math_plan.save()
        math_requirements = [
            ("foundational_required", 30, "大一-大二", ["MATH101", "MATH102", "MATH170", "CSE100"]),
            ("major_required", 54, "大二-大三", ["MATH120", "MATH150", "MATH160", "MATH180", "MATH190"]),
            ("major_elective", 24, "大三-大四", ["MATH130", "MATH140", "BUS160", "CSE180"]),
            ("general_elective", 12, "贯穿学年", ["BUS110", "BUS130", "BUS150", "EE210"]),
        ]
        for category, credits, term, course_codes in math_requirements:
            req, _ = ProgramRequirement.objects.get_or_create(
                plan=math_plan,
                category=category,
                recommended_term=term,
                defaults={"required_credits": credits, "selection_start": math_plan.enrollment_start, "selection_end": math_plan.enrollment_end},
            )
            req.required_credits = credits
            req.selection_start = math_plan.enrollment_start
            req.selection_end = math_plan.enrollment_end
            req.notes = "数学方案示例，可用于筛查学分与课程类别。"
            req.save()
            req.courses.set([course_lookup[c] for c in course_codes if c in course_lookup])

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data ready with {Course.objects.count()} courses, {StudentProfile.objects.count()} students, and {ProgramPlan.objects.count()} plans. Log into /admin with admin/admin123"
            )
        )
