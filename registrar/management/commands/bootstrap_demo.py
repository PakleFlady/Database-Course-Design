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
        ee_class_a, _ = ClassGroup.objects.get_or_create(name="信息2301", department=ee)
        bus_class_a, _ = ClassGroup.objects.get_or_create(name="信管2301", department=bus)

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
        erin_user, _ = User.objects.get_or_create(username="erin", defaults={"first_name": "Erin", "email": "erin@example.com"})
        frank_user, _ = User.objects.get_or_create(username="frank", defaults={"first_name": "Frank", "email": "frank@example.com"})
        alice_user, _ = User.objects.get_or_create(username="alice", defaults={"first_name": "Alice", "email": "alice@example.com"})
        bob_user, _ = User.objects.get_or_create(username="bob", defaults={"first_name": "Bob", "email": "bob@example.com"})
        charlie_user, _ = User.objects.get_or_create(username="charlie", defaults={"first_name": "Charlie", "email": "charlie@example.com"})
        diana_user, _ = User.objects.get_or_create(username="diana", defaults={"first_name": "Diana", "email": "diana@example.com"})
        eric_user, _ = User.objects.get_or_create(username="eric", defaults={"first_name": "Eric", "email": "eric@example.com"})
        fiona_user, _ = User.objects.get_or_create(username="fiona", defaults={"first_name": "Fiona", "email": "fiona@example.com"})
        grace_user, _ = User.objects.get_or_create(username="grace", defaults={"first_name": "Grace", "email": "grace@example.com"})

        for user in (
            carol_user,
            dave_user,
            erin_user,
            frank_user,
            alice_user,
            bob_user,
            charlie_user,
            diana_user,
            eric_user,
            fiona_user,
            grace_user,
        ):
            if not user.password or not user.has_usable_password():
                user.set_password(settings.DEFAULT_INITIAL_PASSWORD)
                user.save(update_fields=["password"])
            security, _ = UserSecurity.objects.get_or_create(user=user)
            if not user.is_staff and not user.is_superuser:
                security.must_change_password = True
                security.save(update_fields=["must_change_password"])

        carol_profile, _ = InstructorProfile.objects.get_or_create(user=carol_user, defaults={"department": cse, "title": "副教授"})
        dave_profile, _ = InstructorProfile.objects.get_or_create(user=dave_user, defaults={"department": math, "title": "讲师"})
        erin_profile, _ = InstructorProfile.objects.get_or_create(user=erin_user, defaults={"department": cse, "title": "教授"})
        frank_profile, _ = InstructorProfile.objects.get_or_create(user=frank_user, defaults={"department": ee, "title": "副教授"})

        alice_profile, _ = StudentProfile.objects.get_or_create(
            user=alice_user,
            defaults={
                "gender": "female",
                "department": cse,
                "class_group": cse_class_a,
                "major": "软件工程",
                "contact_email": "alice@example.com",
            },
        )
        bob_profile, _ = StudentProfile.objects.get_or_create(
            user=bob_user,
            defaults={
                "gender": "male",
                "department": cse,
                "class_group": cse_class_b,
                "major": "计算机科学与技术",
                "contact_email": "bob@example.com",
            },
        )
        charlie_profile, _ = StudentProfile.objects.get_or_create(
            user=charlie_user,
            defaults={
                "gender": "male",
                "department": cse,
                "class_group": cse_class_b,
                "major": "人工智能",
                "contact_email": "charlie@example.com",
            },
        )
        diana_profile, _ = StudentProfile.objects.get_or_create(
            user=diana_user,
            defaults={
                "gender": "female",
                "department": cse,
                "class_group": cse_class_a,
                "major": "软件工程",
                "contact_email": "diana@example.com",
            },
        )
        eric_profile, _ = StudentProfile.objects.get_or_create(
            user=eric_user,
            defaults={
                "gender": "male",
                "department": cse,
                "class_group": cse_class_b,
                "major": "数据科学",
                "contact_email": "eric@example.com",
            },
        )
        fiona_profile, _ = StudentProfile.objects.get_or_create(
            user=fiona_user,
            defaults={
                "gender": "female",
                "department": ee,
                "class_group": ee_class_a,
                "major": "信息工程",
                "contact_email": "fiona@example.com",
            },
        )
        grace_profile, _ = StudentProfile.objects.get_or_create(
            user=grace_user,
            defaults={
                "gender": "female",
                "department": bus,
                "class_group": bus_class_a,
                "major": "信息管理与信息系统",
                "contact_email": "grace@example.com",
            },
        )

        for profile in (
            alice_profile,
            bob_profile,
            charlie_profile,
            diana_profile,
            eric_profile,
            fiona_profile,
            grace_profile,
        ):
            if not profile.student_number:
                profile.save()

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
        cse220, _ = Course.objects.get_or_create(
            code="CSE220",
            defaults={
                "name": "操作系统",
                "credits": 3.0,
                "department": cse,
                "course_type": "major_required",
            },
        )
        cse230, _ = Course.objects.get_or_create(
            code="CSE230",
            defaults={
                "name": "计算机网络",
                "credits": 3.0,
                "department": cse,
                "course_type": "major_required",
            },
        )
        cse240, _ = Course.objects.get_or_create(
            code="CSE240",
            defaults={
                "name": "算法设计与分析",
                "credits": 3.0,
                "department": cse,
                "course_type": "major_required",
            },
        )
        cse250, _ = Course.objects.get_or_create(
            code="CSE250",
            defaults={
                "name": "人工智能导论",
                "credits": 3.0,
                "department": cse,
                "course_type": "major_elective",
            },
        )
        cse260, _ = Course.objects.get_or_create(
            code="CSE260",
            defaults={
                "name": "机器学习",
                "credits": 3.0,
                "department": cse,
                "course_type": "major_elective",
            },
        )
        ee150, _ = Course.objects.get_or_create(
            code="EE150",
            defaults={
                "name": "数字电路基础",
                "credits": 2.5,
                "department": ee,
                "course_type": "major_required",
            },
        )
        bus110, _ = Course.objects.get_or_create(
            code="BUS110",
            defaults={
                "name": "管理学原理",
                "credits": 2.0,
                "department": bus,
                "course_type": "university_elective",
            },
        )

        CoursePrerequisite.objects.get_or_create(course=cse200, prerequisite=cse100, defaults={"min_grade": "C"})
        CoursePrerequisite.objects.get_or_create(course=cse210, prerequisite=cse200, defaults={"min_grade": "C"})
        CoursePrerequisite.objects.get_or_create(course=cse220, prerequisite=cse200, defaults={"min_grade": "C"})
        CoursePrerequisite.objects.get_or_create(course=cse230, prerequisite=cse200, defaults={"min_grade": "C"})
        CoursePrerequisite.objects.get_or_create(course=cse260, prerequisite=cse250, defaults={"min_grade": "B"})

        section1, _ = CourseSection.objects.get_or_create(
            course=cse100,
            semester=fall,
            section_number=1,
            defaults={"instructor": carol_profile, "capacity": 80},
        )
        section2, _ = CourseSection.objects.get_or_create(
            course=cse200,
            semester=fall,
            section_number=2,
            defaults={"instructor": carol_profile, "capacity": 60},
        )
        section3, _ = CourseSection.objects.get_or_create(
            course=cse210,
            semester=fall,
            section_number=3,
            defaults={"instructor": dave_profile, "capacity": 55},
        )
        section4, _ = CourseSection.objects.get_or_create(
            course=cse220,
            semester=fall,
            section_number=4,
            defaults={"instructor": erin_profile, "capacity": 55},
        )
        section5, _ = CourseSection.objects.get_or_create(
            course=cse230,
            semester=fall,
            section_number=5,
            defaults={"instructor": erin_profile, "capacity": 55},
        )
        section6, _ = CourseSection.objects.get_or_create(
            course=cse240,
            semester=fall,
            section_number=6,
            defaults={"instructor": carol_profile, "capacity": 50},
        )
        section7, _ = CourseSection.objects.get_or_create(
            course=cse250,
            semester=fall,
            section_number=7,
            defaults={"instructor": dave_profile, "capacity": 40},
        )
        section8, _ = CourseSection.objects.get_or_create(
            course=cse260,
            semester=fall,
            section_number=8,
            defaults={"instructor": dave_profile, "capacity": 40},
        )
        section9, _ = CourseSection.objects.get_or_create(
            course=ee150,
            semester=fall,
            section_number=1,
            defaults={"instructor": frank_profile, "capacity": 35},
        )
        section10, _ = CourseSection.objects.get_or_create(
            course=bus110,
            semester=fall,
            section_number=1,
            defaults={"instructor": frank_profile, "capacity": 90},
        )

        MeetingTime.objects.get_or_create(section=section1, day_of_week=1, start_time=datetime.time(9, 0), end_time=datetime.time(10, 30), defaults={"location": "A101"})
        MeetingTime.objects.get_or_create(section=section1, day_of_week=4, start_time=datetime.time(9, 0), end_time=datetime.time(10, 30), defaults={"location": "A101"})
        MeetingTime.objects.get_or_create(section=section2, day_of_week=2, start_time=datetime.time(9, 0), end_time=datetime.time(10, 30), defaults={"location": "A102"})
        MeetingTime.objects.get_or_create(section=section3, day_of_week=3, start_time=datetime.time(14, 0), end_time=datetime.time(15, 30), defaults={"location": "A103"})
        MeetingTime.objects.get_or_create(section=section4, day_of_week=1, start_time=datetime.time(13, 0), end_time=datetime.time(14, 30), defaults={"location": "A104"})
        MeetingTime.objects.get_or_create(section=section5, day_of_week=3, start_time=datetime.time(9, 50), end_time=datetime.time(11, 20), defaults={"location": "A105"})
        MeetingTime.objects.get_or_create(section=section6, day_of_week=4, start_time=datetime.time(14, 0), end_time=datetime.time(15, 30), defaults={"location": "A106"})
        MeetingTime.objects.get_or_create(section=section7, day_of_week=5, start_time=datetime.time(9, 0), end_time=datetime.time(10, 30), defaults={"location": "A201"})
        MeetingTime.objects.get_or_create(section=section8, day_of_week=5, start_time=datetime.time(10, 40), end_time=datetime.time(12, 10), defaults={"location": "A201"})
        MeetingTime.objects.get_or_create(section=section9, day_of_week=2, start_time=datetime.time(14, 0), end_time=datetime.time(15, 30), defaults={"location": "B101"})
        MeetingTime.objects.get_or_create(section=section10, day_of_week=1, start_time=datetime.time(18, 30), end_time=datetime.time(20, 0), defaults={"location": "C501"})

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
        Enrollment.objects.get_or_create(
            student=charlie_profile,
            section=section5,
            defaults={"status": "enrolling"},
        )
        Enrollment.objects.get_or_create(
            student=charlie_profile,
            section=section7,
            defaults={"status": "enrolling"},
        )
        Enrollment.objects.get_or_create(
            student=diana_profile,
            section=section2,
            defaults={"status": "enrolling"},
        )
        Enrollment.objects.get_or_create(
            student=diana_profile,
            section=section6,
            defaults={"status": "enrolling"},
        )
        Enrollment.objects.get_or_create(
            student=eric_profile,
            section=section3,
            defaults={"status": "enrolling"},
        )
        Enrollment.objects.get_or_create(
            student=eric_profile,
            section=section8,
            defaults={"status": "enrolling"},
        )
        Enrollment.objects.get_or_create(
            student=fiona_profile,
            section=section9,
            defaults={"status": "enrolling"},
        )
        Enrollment.objects.get_or_create(
            student=grace_profile,
            section=section10,
            defaults={"status": "enrolling"},
        )

        self.stdout.write(self.style.SUCCESS("Demo data ready. Log into /admin with admin/admin123"))
