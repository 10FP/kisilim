from django.contrib import admin

from .models import (
    AssessmentComponent,
    Course,
    Enrollment,
    LearningOutcome,
    LearningOutcomeContribution,
    LearningOutcomeProgramOutcome,
    ProgramOutcome,
    Student,
    StudentAssessment,
)


@admin.register(ProgramOutcome)
class ProgramOutcomeAdmin(admin.ModelAdmin):
    list_display = ("code", "title")
    search_fields = ("code", "title")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "term")
    search_fields = ("code", "name", "term")


@admin.register(LearningOutcome)
class LearningOutcomeAdmin(admin.ModelAdmin):
    list_display = ("code", "course")
    list_filter = ("course",)
    search_fields = ("code", "description")


@admin.register(LearningOutcomeProgramOutcome)
class LearningOutcomeProgramOutcomeAdmin(admin.ModelAdmin):
    list_display = ("learning_outcome", "program_outcome", "weight")
    list_filter = ("program_outcome",)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "student_number")
    search_fields = ("full_name", "student_number")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "year", "section")
    list_filter = ("year", "course")


@admin.register(AssessmentComponent)
class AssessmentComponentAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "weight_percent")
    list_filter = ("course",)


@admin.register(LearningOutcomeContribution)
class LearningOutcomeContributionAdmin(admin.ModelAdmin):
    list_display = ("assessment_component", "learning_outcome", "contribution_percent")
    list_filter = ("assessment_component__course",)


@admin.register(StudentAssessment)
class StudentAssessmentAdmin(admin.ModelAdmin):
    list_display = ("assessment_component", "enrollment", "score")
    list_filter = ("assessment_component__course",)
