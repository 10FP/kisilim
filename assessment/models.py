from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class ProgramOutcome(models.Model):
    code = models.CharField(max_length=10)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.title}"


class Course(models.Model):
    code = models.CharField(max_length=15)
    name = models.CharField(max_length=255)
    term = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} {self.name}"


class LearningOutcome(models.Model):
    course = models.ForeignKey(Course, related_name="learning_outcomes", on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    description = models.TextField()

    class Meta:
        ordering = ["course__code", "code"]
        unique_together = ("course", "code")

    def __str__(self):
        return f"{self.course.code} {self.code}"


class LearningOutcomeProgramOutcome(models.Model):
    learning_outcome = models.ForeignKey(LearningOutcome, related_name="program_links", on_delete=models.CASCADE)
    program_outcome = models.ForeignKey(ProgramOutcome, related_name="learning_links", on_delete=models.CASCADE)
    weight = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1-5 arası katkı ağırlığı",
    )

    class Meta:
        unique_together = ("learning_outcome", "program_outcome")
        verbose_name = "ÖÇ - PÇ ilişkisi"
        verbose_name_plural = "ÖÇ - PÇ ilişkileri"

    def __str__(self):
        return f"{self.learning_outcome} -> {self.program_outcome} ({self.weight})"


class Student(models.Model):
    full_name = models.CharField(max_length=255)
    student_number = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name


class Enrollment(models.Model):
    student = models.ForeignKey(Student, related_name="enrollments", on_delete=models.CASCADE)
    course = models.ForeignKey(Course, related_name="enrollments", on_delete=models.CASCADE)
    year = models.PositiveSmallIntegerField(default=2023)
    section = models.CharField(max_length=10, blank=True)
    RESULT_CHOICES = (
        ("in_progress", "Devam"),
        ("passed", "Geçti"),
        ("failed", "Kaldı"),
    )
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default="in_progress")

    class Meta:
        unique_together = ("student", "course", "year", "section")

    def __str__(self):
        return f"{self.student} - {self.course}"


class AssessmentComponent(models.Model):
    course = models.ForeignKey(Course, related_name="assessments", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    weight_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Ders içi ağırlık (%)",
    )

    class Meta:
        ordering = ["course", "name"]

    def __str__(self):
        return f"{self.course.code} - {self.name}"


class LearningOutcomeContribution(models.Model):
    assessment_component = models.ForeignKey(
        AssessmentComponent, related_name="learning_outcome_contributions", on_delete=models.CASCADE
    )
    learning_outcome = models.ForeignKey(
        LearningOutcome, related_name="assessment_contributions", on_delete=models.CASCADE
    )
    contribution_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="Bileşenin ÖÇ'ye katkısı (%)"
    )

    class Meta:
        unique_together = ("assessment_component", "learning_outcome")

    def __str__(self):
        return f"{self.assessment_component} -> {self.learning_outcome} ({self.contribution_percent}%)"


class StudentAssessment(models.Model):
    enrollment = models.ForeignKey(Enrollment, related_name="assessments", on_delete=models.CASCADE)
    assessment_component = models.ForeignKey(
        AssessmentComponent, related_name="student_assessments", on_delete=models.CASCADE
    )
    score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)

    class Meta:
        unique_together = ("enrollment", "assessment_component")

    def __str__(self):
        return f"{self.enrollment} - {self.assessment_component}: {self.score}"
