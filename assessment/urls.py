from django.urls import path

from . import views

app_name = "assessment"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("student/", views.student_panel, name="student_panel"),
    path("instructor/", views.instructor_panel, name="instructor_panel"),
    path("instructor/grades/", views.grade_upload, name="grade_upload"),
    path("instructor/grades/preview/", views.grade_preview, name="grade_preview"),
    path("instructor/grades/template/", views.grade_template_download, name="grade_template_download"),
    path("dean/", views.dean_panel, name="dean_panel"),
    path("analytics/", views.analytics_panel, name="analytics"),
    path("planner/", views.course_planner, name="course_planner"),
    path("schema/", views.schema_overview, name="schema_overview"),
]
