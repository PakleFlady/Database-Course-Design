from django.db import models


class College(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "学院"
        verbose_name_plural = "学院"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Department(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name="departments")

    class Meta:
        verbose_name = "院系"
        verbose_name_plural = "院系"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Major(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="majors")

    class Meta:
        verbose_name = "专业"
        verbose_name_plural = "专业"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Instructor(models.Model):
    employee_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, choices=[("M", "男"), ("F", "女"), ("O", "其他")])
    email = models.EmailField()
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="instructors")

    class Meta:
        verbose_name = "教师"
        verbose_name_plural = "教师"

    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"


class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, choices=[("M", "男"), ("F", "女"), ("O", "其他")])
    date_of_birth = models.DateField()
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    college = models.ForeignKey(College, on_delete=models.PROTECT, related_name="students")
    major = models.ForeignKey(Major, on_delete=models.PROTECT, related_name="students")

    class Meta:
        verbose_name = "学生"
        verbose_name_plural = "学生"

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"


class Semester(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        verbose_name = "学期"
        verbose_name_plural = "学期"

    def __str__(self):
        return self.name


class Course(models.Model):
    COURSE_TYPE_CHOICES = [
        ("GENERAL_REQUIRED", "公共必修"),
        ("MAJOR_REQUIRED", "专业必修"),
        ("MAJOR_ELECTIVE", "专业选修"),
        ("UNIVERSITY_ELECTIVE", "全校选修"),
        ("PRACTICE", "实践课程"),
    ]

    course_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    credits = models.DecimalField(max_digits=4, decimal_places=1)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="courses")
    course_type = models.CharField(max_length=30, choices=COURSE_TYPE_CHOICES)

    class Meta:
        verbose_name = "课程"
        verbose_name_plural = "课程"

    def __str__(self):
        return f"{self.course_code} - {self.name}"


class CourseSection(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="sections")
    section_code = models.CharField(max_length=20)
    instructor = models.ForeignKey(Instructor, on_delete=models.PROTECT, related_name="sections")
    capacity = models.PositiveIntegerField(default=30)
    location = models.CharField(max_length=255)
    weekday = models.PositiveSmallIntegerField(help_text="1=周一, ... 7=周日")
    start_time = models.TimeField()
    end_time = models.TimeField()
    schedule_notes = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "课程班"
        verbose_name_plural = "课程班"
        unique_together = ["semester", "section_code"]

    def __str__(self):
        return f"{self.course.course_code}-{self.section_code} ({self.semester.code})"


class CoursePrerequisite(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="prerequisites")
    prerequisite = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="required_for")
    min_grade = models.DecimalField(max_digits=4, decimal_places=1, default=60)

    class Meta:
        verbose_name = "课程先修要求"
        verbose_name_plural = "课程先修要求"
        unique_together = ["course", "prerequisite"]

    def __str__(self):
        return f"{self.course.course_code} 先修 {self.prerequisite.course_code}"


class Enrollment(models.Model):
    STATUS_CHOICES = [
        ("ENROLLED", "已选课"),
        ("DROPPED", "退课"),
        ("PASSED", "通过"),
        ("FAILED", "未通过"),
        ("RETAKE", "重修申请"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ENROLLED")
    final_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade_letter = models.CharField(max_length=5, blank=True)
    grade_points = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "选课记录"
        verbose_name_plural = "选课记录"
        unique_together = ["student", "section"]

    def __str__(self):
        return f"{self.student} - {self.section}"
