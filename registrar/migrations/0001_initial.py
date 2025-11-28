# Generated manually for initial Django models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Department",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True, verbose_name="院系代码")),
                ("name", models.CharField(max_length=255, verbose_name="院系名称")),
            ],
            options={
                "verbose_name": "院系",
                "verbose_name_plural": "院系",
                "ordering": ["code"],
            },
        ),
        migrations.CreateModel(
            name="Semester",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True, verbose_name="学期代码")),
                ("name", models.CharField(max_length=255, verbose_name="学期名称")),
                ("start_date", models.DateField(verbose_name="开始日期")),
                ("end_date", models.DateField(verbose_name="结束日期")),
            ],
            options={
                "verbose_name": "学期",
                "verbose_name_plural": "学期",
                "ordering": ["-start_date"],
            },
        ),
        migrations.CreateModel(
            name="Course",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True, verbose_name="课程代码")),
                ("name", models.CharField(max_length=255, verbose_name="课程名称")),
                ("credits", models.DecimalField(decimal_places=1, max_digits=4, verbose_name="学分")),
                (
                    "course_type",
                    models.CharField(
                        choices=[
                            ("general_required", "通识必修"),
                            ("major_required", "专业必修"),
                            ("major_elective", "专业选修"),
                            ("university_elective", "校级选修"),
                            ("practical", "实践/实验"),
                        ],
                        max_length=50,
                        verbose_name="课程类别",
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="课程简介")),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="courses",
                        to="registrar.department",
                        verbose_name="开课院系",
                    ),
                ),
            ],
            options={
                "verbose_name": "课程",
                "verbose_name_plural": "课程",
                "ordering": ["code"],
            },
        ),
        migrations.CreateModel(
            name="InstructorProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, max_length=100, verbose_name="职称")),
                ("office_phone", models.CharField(blank=True, max_length=50, verbose_name="办公电话")),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="instructors",
                        to="registrar.department",
                        verbose_name="所属院系",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="instructor_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="账号",
                    ),
                ),
            ],
            options={
                "verbose_name": "教师",
                "verbose_name_plural": "教师",
                "ordering": ["user__username"],
            },
        ),
        migrations.CreateModel(
            name="StudentProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "gender",
                    models.CharField(
                        blank=True,
                        choices=[("male", "男"), ("female", "女"), ("other", "其他")],
                        max_length=10,
                        verbose_name="性别",
                    ),
                ),
                ("date_of_birth", models.DateField(blank=True, null=True, verbose_name="出生日期")),
                ("contact_email", models.EmailField(blank=True, max_length=254, verbose_name="联系邮箱")),
                ("contact_phone", models.CharField(blank=True, max_length=50, verbose_name="联系电话")),
                ("college", models.CharField(max_length=255, verbose_name="学院")),
                ("major", models.CharField(max_length=255, verbose_name="专业")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="student_profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="账号",
                    ),
                ),
            ],
            options={
                "verbose_name": "学生",
                "verbose_name_plural": "学生",
                "ordering": ["user__username"],
            },
        ),
        migrations.CreateModel(
            name="CourseSection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("section_number", models.PositiveSmallIntegerField(default=1, verbose_name="教学班号")),
                ("capacity", models.PositiveIntegerField(default=60, verbose_name="容量")),
                ("notes", models.TextField(blank=True, verbose_name="备注")),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sections",
                        to="registrar.course",
                        verbose_name="课程",
                    ),
                ),
                (
                    "instructor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sections",
                        to="registrar.instructorprofile",
                        verbose_name="教师",
                    ),
                ),
                (
                    "semester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sections",
                        to="registrar.semester",
                        verbose_name="学期",
                    ),
                ),
            ],
            options={
                "verbose_name": "教学班",
                "verbose_name_plural": "教学班",
                "ordering": ["course__code", "section_number"],
                "unique_together": {("course", "semester", "section_number")},
            },
        ),
        migrations.CreateModel(
            name="MeetingTime",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "day_of_week",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "周一"),
                            (2, "周二"),
                            (3, "周三"),
                            (4, "周四"),
                            (5, "周五"),
                            (6, "周六"),
                            (7, "周日"),
                        ],
                        verbose_name="周次",
                    ),
                ),
                ("start_time", models.TimeField(verbose_name="开始时间")),
                ("end_time", models.TimeField(verbose_name="结束时间")),
                ("location", models.CharField(max_length=255, verbose_name="上课地点")),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="meeting_times",
                        to="registrar.coursesection",
                        verbose_name="教学班",
                    ),
                ),
            ],
            options={
                "verbose_name": "上课时间",
                "verbose_name_plural": "上课时间",
                "ordering": ["day_of_week", "start_time"],
            },
            constraints=[
                models.CheckConstraint(
                    check=models.Q(("end_time__gt", django.db.models.expressions.F("start_time"))),
                    name="meetingtime_end_after_start",
                )
            ],
        ),
        migrations.CreateModel(
            name="CoursePrerequisite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "min_grade",
                    models.CharField(
                        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("F", "F")],
                        default="C",
                        max_length=2,
                        verbose_name="最低成绩",
                    ),
                ),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="prerequisites",
                        to="registrar.course",
                        verbose_name="课程",
                    ),
                ),
                (
                    "prerequisite",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="required_for",
                        to="registrar.course",
                        verbose_name="先修课",
                    ),
                ),
            ],
            options={
                "verbose_name": "先修要求",
                "verbose_name_plural": "先修要求",
                "ordering": ["course__code", "prerequisite__code"],
                "unique_together": {("course", "prerequisite")},
            },
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("enrolling", "选课中"),
                            ("waitlisted", "候补"),
                            ("dropped", "已退课"),
                            ("passed", "已通过"),
                            ("failed", "未通过"),
                        ],
                        default="enrolling",
                        max_length=20,
                        verbose_name="状态",
                    ),
                ),
                (
                    "final_grade",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("A", "A"),
                            ("B", "B"),
                            ("C", "C"),
                            ("D", "D"),
                            ("F", "F"),
                            ("P", "P"),
                            ("NP", "NP"),
                        ],
                        max_length=2,
                        verbose_name="最终成绩",
                    ),
                ),
                ("grade_points", models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True, verbose_name="绩点")),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="registrar.coursesection",
                        verbose_name="教学班",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="registrar.studentprofile",
                        verbose_name="学生",
                    ),
                ),
            ],
            options={
                "verbose_name": "选课记录",
                "verbose_name_plural": "选课记录",
                "ordering": ["section__semester__start_date", "student__user__username"],
                "unique_together": {("student", "section")},
            },
        ),
    ]
