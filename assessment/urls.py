from django.urls import path

from . import views

app_name = "assessment"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("student/", views.student_panel, name="student_panel"),
    path("instructor/", views.instructor_panel, name="instructor_panel"),
    path("analytics/", views.analytics_panel, name="analytics"),
    path("planner/", views.course_planner, name="course_planner"),
    path("schema/", views.schema_overview, name="schema_overview"),
]
