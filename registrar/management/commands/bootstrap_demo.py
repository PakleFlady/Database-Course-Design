"""Populate the database with demo users, courses, sections, and enrollments."""
from __future__ import annotations

import datetime
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from registrar.models import (
    Course,
    CoursePrerequisite,
    CourseSection,
    Department,
    Enrollment,
    InstructorProfile,
    MeetingTime,
    Semester,
    StudentProfile,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with demo data for admin exploration"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Creating demo data..."))
        cse, _ = Department.objects.get_or_create(code="CSE", defaults={"name": "计算机科学与工程学院"})
        math, _ = Department.objects.get_or_create(code="MATH", defaults={"name": "数学系"})

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

        admin_user, created_admin = User.objects.get_or_create(username="admin", defaults={"email": "admin@example.com"})
        if created_admin:
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.set_password("admin123")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin / admin123"))

        carol_user, _ = User.objects.get_or_create(username="carol", defaults={"first_name": "Carol", "email": "carol@example.com"})
        dave_user, _ = User.objects.get_or_create(username="dave", defaults={"first_name": "Dave", "email": "dave@example.com"})
        alice_user, _ = User.objects.get_or_create(username="alice", defaults={"first_name": "Alice", "email": "alice@example.com"})
        bob_user, _ = User.objects.get_or_create(username="bob", defaults={"first_name": "Bob", "email": "bob@example.com"})

        for user in (carol_user, dave_user, alice_user, bob_user):
            if not user.has_usable_password():
                user.set_password("12345678")
                user.save()

        carol_profile, _ = InstructorProfile.objects.get_or_create(user=carol_user, defaults={"department": cse, "title": "副教授"})
        dave_profile, _ = InstructorProfile.objects.get_or_create(user=dave_user, defaults={"department": math, "title": "讲师"})

        alice_profile, _ = StudentProfile.objects.get_or_create(
            user=alice_user,
            defaults={
                "gender": "female",
                "college": "计算机学院",
                "major": "软件工程",
                "contact_email": "alice@example.com",
            },
        )
        bob_profile, _ = StudentProfile.objects.get_or_create(
            user=bob_user,
            defaults={
                "gender": "male",
                "college": "计算机学院",
                "major": "计算机科学与技术",
                "contact_email": "bob@example.com",
            },
        )

        cse100, _ = Course.objects.get_or_create(
            code="CSE100",
            defaults={
                "name": "程序设计基础",
                "credits": 3.0,
                "department": cse,
                "course_type": "general_required",
            },
        )
        cse200, _ = Course.objects.get_or_create(
            code="CSE200",
            defaults={
                "name": "数据结构",
                "credits": 3.0,
                "department": cse,
                "course_type": "major_required",
            },
        )
        cse210, _ = Course.objects.get_or_create(
            code="CSE210",
            defaults={
                "name": "数据库系统",
                "credits": 3.0,
                "department": cse,
                "course_type": "major_required",
            },
        )

        CoursePrerequisite.objects.get_or_create(course=cse200, prerequisite=cse100, defaults={"min_grade": "C"})

        section1, _ = CourseSection.objects.get_or_create(
            course=cse100,
            semester=fall,
            section_number=1,
            defaults={"instructor": carol_profile, "capacity": 50},
        )
        section2, _ = CourseSection.objects.get_or_create(
            course=cse200,
            semester=fall,
            section_number=2,
            defaults={"instructor": carol_profile, "capacity": 45},
        )
        section3, _ = CourseSection.objects.get_or_create(
            course=cse210,
            semester=fall,
            section_number=3,
            defaults={"instructor": dave_profile, "capacity": 40},
        )
        section4, _ = CourseSection.objects.get_or_create(
            course=cse200,
            semester=fall,
            section_number=4,
            defaults={"instructor": dave_profile, "capacity": 35},
        )

        MeetingTime.objects.get_or_create(section=section1, day_of_week=1, start_time=datetime.time(9, 0), end_time=datetime.time(10, 30), defaults={"location": "A101"})
        MeetingTime.objects.get_or_create(section=section2, day_of_week=2, start_time=datetime.time(9, 0), end_time=datetime.time(10, 30), defaults={"location": "A102"})
        MeetingTime.objects.get_or_create(section=section3, day_of_week=3, start_time=datetime.time(14, 0), end_time=datetime.time(15, 30), defaults={"location": "A103"})
        MeetingTime.objects.get_or_create(section=section4, day_of_week=1, start_time=datetime.time(9, 30), end_time=datetime.time(11, 0), defaults={"location": "A104"})

        Enrollment.objects.get_or_create(
            student=alice_profile,
            section=section1,
            defaults={"status": "passed", "final_grade": "A", "grade_points": 4.0},
        )
        Enrollment.objects.get_or_create(
            student=alice_profile,
            section=section2,
            defaults={"status": "enrolling"},
        )
        Enrollment.objects.get_or_create(
            student=alice_profile,
            section=section3,
            defaults={"status": "enrolling"},
        )
        Enrollment.objects.get_or_create(
            student=bob_profile,
            section=section1,
            defaults={"status": "failed", "final_grade": "F", "grade_points": 0},
        )
        Enrollment.objects.get_or_create(
            student=bob_profile,
            section=section4,
            defaults={"status": "enrolling"},
        )

        self.stdout.write(self.style.SUCCESS("Demo data ready. Log into /admin with admin/admin123"))
