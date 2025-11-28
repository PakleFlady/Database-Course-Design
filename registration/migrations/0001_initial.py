from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="College",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(max_length=255)),
            ],
            options={
                "verbose_name": "学院",
                "verbose_name_plural": "学院",
            },
        ),
        migrations.CreateModel(
            name="Department",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(max_length=255)),
                (
                    "college",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="departments", to="registration.college"),
                ),
            ],
            options={
                "verbose_name": "院系",
                "verbose_name_plural": "院系",
            },
        ),
        migrations.CreateModel(
            name="Major",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(max_length=255)),
                (
                    "department",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="majors", to="registration.department"),
                ),
            ],
            options={
                "verbose_name": "专业",
                "verbose_name_plural": "专业",
            },
        ),
        migrations.CreateModel(
            name="Instructor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("employee_id", models.CharField(max_length=20, unique=True)),
                ("full_name", models.CharField(max_length=255)),
                ("gender", models.CharField(choices=[("M", "男"), ("F", "女"), ("O", "其他")], max_length=10)),
                ("email", models.EmailField(max_length=254)),
                (
                    "department",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="instructors", to="registration.department"),
                ),
            ],
            options={
                "verbose_name": "教师",
                "verbose_name_plural": "教师",
            },
        ),
        migrations.CreateModel(
            name="Semester",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=30, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
            ],
            options={
                "verbose_name": "学期",
                "verbose_name_plural": "学期",
            },
        ),
        migrations.CreateModel(
            name="Student",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("student_id", models.CharField(max_length=20, unique=True)),
                ("full_name", models.CharField(max_length=255)),
                ("gender", models.CharField(choices=[("M", "男"), ("F", "女"), ("O", "其他")], max_length=10)),
                ("date_of_birth", models.DateField()),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(max_length=50)),
                (
                    "college",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="students", to="registration.college"),
                ),
                (
                    "major",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="students", to="registration.major"),
                ),
            ],
            options={
                "verbose_name": "学生",
                "verbose_name_plural": "学生",
            },
        ),
        migrations.CreateModel(
            name="Course",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("course_code", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("credits", models.DecimalField(decimal_places=1, max_digits=4)),
                (
                    "course_type",
                    models.CharField(
                        choices=[
                            ("GENERAL_REQUIRED", "公共必修"),
                            ("MAJOR_REQUIRED", "专业必修"),
                            ("MAJOR_ELECTIVE", "专业选修"),
                            ("UNIVERSITY_ELECTIVE", "全校选修"),
                            ("PRACTICE", "实践课程"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "department",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="courses", to="registration.department"),
                ),
            ],
            options={
                "verbose_name": "课程",
                "verbose_name_plural": "课程",
            },
        ),
        migrations.CreateModel(
            name="CourseSection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("section_code", models.CharField(max_length=20)),
                ("capacity", models.PositiveIntegerField(default=30)),
                ("location", models.CharField(max_length=255)),
                ("weekday", models.PositiveSmallIntegerField(help_text="1=周一, ... 7=周日")),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("schedule_notes", models.CharField(blank=True, max_length=255)),
                (
                    "course",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sections", to="registration.course"),
                ),
                (
                    "instructor",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sections", to="registration.instructor"),
                ),
                (
                    "semester",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sections", to="registration.semester"),
                ),
            ],
            options={
                "verbose_name": "课程班",
                "verbose_name_plural": "课程班",
                "unique_together": {("semester", "section_code")},
            },
        ),
        migrations.CreateModel(
            name="CoursePrerequisite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("min_grade", models.DecimalField(decimal_places=1, default=60, max_digits=4)),
                (
                    "course",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="prerequisites", to="registration.course"),
                ),
                (
                    "prerequisite",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="required_for", to="registration.course"),
                ),
            ],
            options={
                "verbose_name": "课程先修要求",
                "verbose_name_plural": "课程先修要求",
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
                            ("ENROLLED", "已选课"),
                            ("DROPPED", "退课"),
                            ("PASSED", "通过"),
                            ("FAILED", "未通过"),
                            ("RETAKE", "重修申请"),
                        ],
                        default="ENROLLED",
                        max_length=20,
                    ),
                ),
                ("final_grade", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("grade_letter", models.CharField(blank=True, max_length=5)),
                ("grade_points", models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                (
                    "section",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="registration.coursesection"),
                ),
                (
                    "student",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="enrollments", to="registration.student"),
                ),
            ],
            options={
                "verbose_name": "选课记录",
                "verbose_name_plural": "选课记录",
                "unique_together": {("student", "section")},
            },
        ),
    ]
