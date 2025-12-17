"""Create a lightweight demo dataset for quick walkthroughs."""
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
    Semester,
    StudentProfile,
    UserSecurity,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seed a small dataset (few dozen records) for quick demo sessions"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Creating compact demo data..."))

        cse, _ = Department.objects.get_or_create(code="CSE", defaults={"name": "计算机科学与工程学院"})
        bus, _ = Department.objects.get_or_create(code="BUS", defaults={"name": "经济管理学院"})

        class_groups = {
            "CSE": ClassGroup.objects.get_or_create(name="软件2301", department=cse)[0],
            "BUS": ClassGroup.objects.get_or_create(name="信管2301", department=bus)[0],
        }

        fall, _ = Semester.objects.get_or_create(
            code="2025FALL",
            defaults={
                "name": "2025 秋季学期",
                "start_date": datetime.date(2025, 9, 1),
                "end_date": datetime.date(2026, 1, 10),
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
        ensure_password_and_security(admin_user)

        instructor_accounts = [
            ("carol", "Carol", cse, "副教授"),
            ("dave", "Dave", bus, "讲师"),
        ]
        instructors = {}
        for username, name, dept, title in instructor_accounts:
            user, _ = User.objects.get_or_create(username=username, defaults={"first_name": name, "email": f"{username}@example.com"})
            ensure_password_and_security(user)
            profile, _ = InstructorProfile.objects.get_or_create(user=user, defaults={"department": dept, "title": title})
            instructors[username] = profile

        students_data = [
            ("alice", "Alice", "female", cse, class_groups["CSE"], "软件工程"),
            ("bob", "Bob", "male", cse, class_groups["CSE"], "软件工程"),
            ("cindy", "Cindy", "female", bus, class_groups["BUS"], "信息管理"),
            ("derek", "Derek", "male", bus, class_groups["BUS"], "信息管理"),
        ]

        students: list[StudentProfile] = []
        for username, first_name, gender, dept, group, major in students_data:
            user, _ = User.objects.get_or_create(username=username, defaults={"first_name": first_name, "email": f"{username}@example.com"})
            ensure_password_and_security(user)
            profile, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={"gender": gender, "department": dept, "class_group": group, "major": major, "contact_email": f"{username}@example.com"},
            )
            if not profile.student_number:
                profile.save()
            students.append(profile)

        courses = [
            ("CSE100", "程序设计基础", 3.0, cse, "foundational_required"),
            ("CSE200", "数据结构", 3.0, cse, "major_required"),
            ("BUS110", "管理学原理", 2.0, bus, "general_elective"),
            ("BUS160", "数据可视化", 2.0, bus, "general_elective"),
        ]
        for code, name, credits, dept, ctype in courses:
            Course.objects.get_or_create(code=code, defaults={"name": name, "credits": credits, "department": dept, "course_type": ctype})

        course_lookup = {c.code: c for c in Course.objects.filter(code__in=[c[0] for c in courses])}
        CoursePrerequisite.objects.get_or_create(course=course_lookup["CSE200"], prerequisite=course_lookup["CSE100"], defaults={"min_grade": "C"})

        sections = [
            (course_lookup["CSE100"], instructors["carol"], 60),
            (course_lookup["CSE200"], instructors["carol"], 50),
            (course_lookup["BUS110"], instructors["dave"], 80),
            (course_lookup["BUS160"], instructors["dave"], 80),
        ]
        created_sections = []
        for idx, (course, instructor, capacity) in enumerate(sections, start=1):
            section, _ = CourseSection.objects.get_or_create(
                course=course,
                semester=fall,
                section_number=idx,
                defaults={"instructor": instructor, "capacity": capacity},
            )
            created_sections.append(section)
            MeetingTime.objects.get_or_create(
                section=section,
                day_of_week=((idx % 5) + 1),
                start_time=datetime.time(8 + (idx % 3) * 2, 0),
                end_time=datetime.time(9 + (idx % 3) * 2, 50),
                defaults={"location": f"B{200 + idx}"},
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

        sample_grades = [("passed", 92), ("passed", 85), ("failed", 55), ("enrolling", None)]
        for idx, student in enumerate(students):
            section = created_sections[idx % len(created_sections)]
            status, grade = sample_grades[idx % len(sample_grades)]
            Enrollment.objects.update_or_create(
                student=student,
                section=section,
                defaults={"status": status, "final_grade": grade, "grade_points": calc_points(grade)},
            )

        self.stdout.write(self.style.SUCCESS("Compact demo data ready. Use admin/admin123 to log in."))
