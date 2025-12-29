from collections import defaultdict
from datetime import datetime
import io
from pathlib import Path
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import Avg, Count, Max
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.http import require_POST

from .models import (
    AssessmentComponent,
    Course,
    CoursePOHeatmap,
    Enrollment,
    LearningOutcome,
    LearningOutcomeContribution,
    LearningOutcomeProgramOutcome,
    ProgramOutcome,
    Student,
    StudentAssessment,
)
from .forms import (
    AssessmentComponentForm,
    CourseForm,
    EnrollmentForm,
    LearningOutcomeContributionForm,
    LearningOutcomeForm,
    LearningOutcomeProgramOutcomeForm,
    ProgramOutcomeForm,
    StudentForm,
)


def bootstrap_demo_data():
    """Create richer demo data: 6 ders, ortak ÖÇ/PO haritası, bileşenler ve notlar."""
    if Course.objects.exists():
        return

    po_map = {
        "PO1": ProgramOutcome.objects.create(code="PO1", title="Analitik Problem Çözme"),
        "PO2": ProgramOutcome.objects.create(code="PO2", title="İletişim ve Sunum"),
        "PO3": ProgramOutcome.objects.create(code="PO3", title="Takım Çalışması ve Liderlik"),
        "PO4": ProgramOutcome.objects.create(code="PO4", title="Etik ve Mesleki Sorumluluk"),
    }

    courses_data = [
        {
            "code": "BLG101",
            "name": "Girişimci Yazılım",
            "term": "Güz",
            "los": [
                ("LO1", "Temel yazılım kavramlarını açıklar."),
                ("LO2", "Basit bir web uygulamasını tasarlar."),
                ("LO3", "Takım içinde planlama ve iletişim yürütür."),
            ],
            "lo_po": [("LO1", "PO1", 4), ("LO2", "PO1", 5), ("LO2", "PO2", 3), ("LO3", "PO3", 4), ("LO3", "PO2", 2)],
            "assessments": [("Vize", 40), ("Proje", 60)],
            "lo_contrib": [("Vize", "LO1", 60), ("Vize", "LO2", 40), ("Proje", "LO2", 60), ("Proje", "LO3", 40)],
        },
        {
            "code": "BLG201",
            "name": "Veri Yapıları",
            "term": "Güz",
            "los": [
                ("LO1", "Liste, yığın ve kuyruk veri yapılarını uygular."),
                ("LO2", "Ağaç ve grafik algoritmalarını uygular."),
                ("LO3", "Karmaşıklık analizi yapar."),
            ],
            "lo_po": [("LO1", "PO1", 5), ("LO2", "PO1", 4), ("LO2", "PO2", 2), ("LO3", "PO1", 3), ("LO3", "PO3", 3)],
            "assessments": [("Vize", 40), ("Proje", 40), ("Final", 20)],
            "lo_contrib": [
                ("Vize", "LO1", 60),
                ("Vize", "LO3", 40),
                ("Proje", "LO2", 60),
                ("Proje", "LO3", 40),
                ("Final", "LO1", 30),
                ("Final", "LO2", 40),
                ("Final", "LO3", 30),
            ],
        },
        {
            "code": "BLG205",
            "name": "Veritabanı Sistemleri",
            "term": "Bahar",
            "los": [
                ("LO1", "İlişkisel veri modelini kurar."),
                ("LO2", "SQL ile veri işlemleri yapar."),
                ("LO3", "Performans ve bütünlük kontrollerini uygular."),
            ],
            "lo_po": [("LO1", "PO1", 4), ("LO2", "PO1", 4), ("LO2", "PO2", 3), ("LO3", "PO4", 3)],
            "assessments": [("Vize", 40), ("Lab", 30), ("Proje", 30)],
            "lo_contrib": [
                ("Vize", "LO1", 50),
                ("Vize", "LO2", 50),
                ("Lab", "LO2", 60),
                ("Lab", "LO3", 40),
                ("Proje", "LO1", 30),
                ("Proje", "LO3", 70),
            ],
        },
        {
            "code": "BLG301",
            "name": "Yazılım Mühendisliği",
            "term": "Bahar",
            "los": [
                ("LO1", "Süreç modellerini uygular."),
                ("LO2", "Gereksinim ve tasarım dokümantasyonu yazar."),
                ("LO3", "Çevik ortamda takım çalışması yürütür."),
            ],
            "lo_po": [("LO1", "PO1", 3), ("LO2", "PO2", 4), ("LO3", "PO3", 5), ("LO3", "PO2", 3)],
            "assessments": [("Proje", 50), ("Ara Rapor", 20), ("Sunum", 30)],
            "lo_contrib": [
                ("Proje", "LO1", 30),
                ("Proje", "LO2", 40),
                ("Proje", "LO3", 30),
                ("Ara Rapor", "LO2", 60),
                ("Ara Rapor", "LO3", 40),
                ("Sunum", "LO2", 40),
                ("Sunum", "LO3", 60),
            ],
        },
        {
            "code": "BLG310",
            "name": "Web Teknolojileri",
            "term": "Bahar",
            "los": [
                ("LO1", "Ön yüz bileşenlerini kodlar."),
                ("LO2", "Arka uç servisleri yazar."),
                ("LO3", "Güvenli dağıtım ve test süreçlerini uygular."),
            ],
            "lo_po": [("LO1", "PO1", 3), ("LO1", "PO2", 3), ("LO2", "PO1", 4), ("LO3", "PO4", 4)],
            "assessments": [("Vize", 30), ("Lab", 30), ("Proje", 40)],
            "lo_contrib": [
                ("Vize", "LO1", 50),
                ("Vize", "LO2", 50),
                ("Lab", "LO1", 40),
                ("Lab", "LO2", 40),
                ("Lab", "LO3", 20),
                ("Proje", "LO2", 50),
                ("Proje", "LO3", 50),
            ],
        },
        {
            "code": "IST210",
            "name": "Veri Bilimi Giriş",
            "term": "Güz",
            "los": [
                ("LO1", "Python ile veri hazırlama ve görselleştirme yapar."),
                ("LO2", "Basit makine öğrenmesi modelleri kurar."),
                ("LO3", "Etik ve veri gizliliği konularını gözetir."),
            ],
            "lo_po": [("LO1", "PO1", 3), ("LO2", "PO1", 4), ("LO2", "PO2", 2), ("LO3", "PO4", 5)],
            "assessments": [("Vize", 30), ("Lab", 30), ("Proje", 40)],
            "lo_contrib": [
                ("Vize", "LO1", 60),
                ("Vize", "LO2", 40),
                ("Lab", "LO1", 50),
                ("Lab", "LO2", 30),
                ("Lab", "LO3", 20),
                ("Proje", "LO2", 60),
                ("Proje", "LO3", 40),
            ],
        },
    ]

    courses = []
    lo_lookup = {}
    comp_lookup = {}

    for data in courses_data:
        course = Course.objects.create(code=data["code"], name=data["name"], term=data["term"])
        courses.append(course)
        for code, desc in data["los"]:
            lo = LearningOutcome.objects.create(course=course, code=code, description=desc)
            lo_lookup[(course.code, code)] = lo
        for name, weight in data["assessments"]:
            comp = AssessmentComponent.objects.create(course=course, name=name, weight_percent=weight)
            comp_lookup[(course.code, name)] = comp

    for data in courses_data:
        course = next(c for c in courses if c.code == data["code"])
        LearningOutcomeProgramOutcome.objects.bulk_create(
            [
                LearningOutcomeProgramOutcome(
                    learning_outcome=lo_lookup[(course.code, lo_code)],
                    program_outcome=po_map[po_code],
                    weight=weight,
                )
                for lo_code, po_code, weight in data["lo_po"]
            ]
        )
        LearningOutcomeContribution.objects.bulk_create(
            [
                LearningOutcomeContribution(
                    assessment_component=comp_lookup[(course.code, comp_name)],
                    learning_outcome=lo_lookup[(course.code, lo_code)],
                    contribution_percent=percent,
                )
                for comp_name, lo_code, percent in data["lo_contrib"]
            ]
        )

    ayse = Student.objects.create(full_name="Ayşe Demir", student_number="20231234")
    ali = Student.objects.create(full_name="Ali Can", student_number="20231235")

    enrollments = []
    for student in (ayse, ali):
        for course in courses:
            enrollments.append(Enrollment(student=student, course=course, year=2023))
    Enrollment.objects.bulk_create(enrollments)

    default_scores = {"Vize": 78, "Proje": 85, "Final": 82, "Lab": 80, "Quiz": 75, "Ara Rapor": 83, "Sunum": 86}
    student_assessments = []
    for enrollment in Enrollment.objects.all().select_related("course"):
        for comp in AssessmentComponent.objects.filter(course=enrollment.course):
            score = default_scores.get(comp.name, 80)
            # Ayşe biraz yüksek, Ali biraz daha düşük not alsın.
            if enrollment.student.full_name.startswith("Ali"):
                score = max(0, score - 8)
            student_assessments.append(
                StudentAssessment(enrollment=enrollment, assessment_component=comp, score=score)
            )
    StudentAssessment.objects.bulk_create(student_assessments)


def calculate_learning_outcome_scores(enrollment: Enrollment):
    """Aggregate öğrenci ÖÇ puanlarını hesapla."""
    scores = {}
    contributions = (
        LearningOutcomeContribution.objects.select_related("assessment_component", "learning_outcome")
        .filter(assessment_component__course=enrollment.course)
        .all()
    )

    for contribution in contributions:
        try:
            student_score = StudentAssessment.objects.get(
                enrollment=enrollment, assessment_component=contribution.assessment_component
            ).score
        except StudentAssessment.DoesNotExist:
            continue

        comp_weight = contribution.assessment_component.weight_percent / 100
        lo_weight = contribution.contribution_percent / 100
        total = scores.get(contribution.learning_outcome_id, 0)
        scores[contribution.learning_outcome_id] = total + student_score * comp_weight * lo_weight

    return scores


def calculate_po_performance(lo_scores):
    """PO performansını, ÖÇ ağırlıklarıyla normalize ederek hesaplar."""
    po_scores = defaultdict(lambda: {"total": 0.0, "weight": 0.0, "po": None})
    mappings = LearningOutcomeProgramOutcome.objects.select_related("program_outcome", "learning_outcome")
    for mapping in mappings:
        score = lo_scores.get(mapping.learning_outcome_id)
        if score is None:
            continue
        po_scores[mapping.program_outcome_id]["total"] += score * mapping.weight
        po_scores[mapping.program_outcome_id]["weight"] += mapping.weight
        po_scores[mapping.program_outcome_id]["po"] = mapping.program_outcome

    results = []
    for item in po_scores.values():
        normalized = item["total"] / item["weight"] if item["weight"] else 0
        results.append({"program_outcome": item["po"], "score": round(normalized, 1)})
    return sorted(results, key=lambda x: x["program_outcome"].code)


def final_score(enrollment: Enrollment):
    """Genel ders puanı: bileşen notu x bileşen ağırlığı."""
    total = 0
    for comp in AssessmentComponent.objects.filter(course=enrollment.course):
        sa = StudentAssessment.objects.filter(enrollment=enrollment, assessment_component=comp).first()
        if not sa:
            continue
        total += sa.score * (comp.weight_percent / 100)
    return round(total, 1) if total else 0


def enrollment_assessment_breakdown(enrollment: Enrollment):
    course_assessments = (
        AssessmentComponent.objects.filter(course=enrollment.course)
        .annotate(class_avg=Avg("student_assessments__score"))
        .all()
    )
    assessments = []
    for comp in course_assessments:
        student_score = StudentAssessment.objects.filter(
            enrollment=enrollment, assessment_component=comp
        ).first()
        assessments.append(
            {
                "name": comp.name,
                "weight": comp.weight_percent,
                "score": round(student_score.score, 1) if student_score else None,
                "class_avg": round(comp.class_avg, 1) if comp.class_avg else None,
            }
        )
    return assessments


def dashboard(request):
    bootstrap_demo_data()
    student = Student.objects.first()
    if not student:
        return render(request, "assessment/dashboard.html", {"student": None, "enrollments": []})

    enrollments = (
        Enrollment.objects.filter(student=student)
        .select_related("course")
        .prefetch_related("course__learning_outcomes__program_links__program_outcome")
    )

    enrollment_data = []
    lo_scores = {}
    for enrollment in enrollments:
        lo_score_map = calculate_learning_outcome_scores(enrollment)
        lo_scores.update(lo_score_map)
        outcomes = []
        for lo in enrollment.course.learning_outcomes.all():
            mappings = lo.program_links.select_related("program_outcome")
            outcomes.append(
                {
                    "obj": lo,
                    "mappings": mappings,
                    "score": round(lo_score_map.get(lo.id, 0), 1),
                }
            )

        enrollment_data.append(
            {
                "course": enrollment.course,
                "assessments": enrollment_assessment_breakdown(enrollment),
                "learning_outcomes": outcomes,
            }
        )

    po_performance = calculate_po_performance(lo_scores)
    program_outcomes = ProgramOutcome.objects.all()
    learning_outcome_links = LearningOutcomeProgramOutcome.objects.select_related(
        "learning_outcome", "program_outcome"
    )

    context = {
        "student": student,
        "enrollments": enrollment_data,
        "program_outcomes": program_outcomes,
        "learning_outcome_links": learning_outcome_links,
        "po_performance": po_performance,
        "courses": Course.objects.all(),
    }
    return render(request, "assessment/dashboard.html", context)


def student_panel(request):
    bootstrap_demo_data()
    students = Student.objects.all()
    courses = Course.objects.all()
    selected_student = students.filter(id=request.GET.get("student")).first() or students.first()
    selected_course = courses.filter(id=request.GET.get("course")).first() or courses.first()

    enrollment_data = []
    po_performance = []

    if selected_student and selected_course:
        enrollment = (
            Enrollment.objects.filter(student=selected_student, course=selected_course)
            .select_related("course")
            .prefetch_related("course__learning_outcomes__program_links__program_outcome")
            .first()
        )
        if enrollment:
            lo_score_map = calculate_learning_outcome_scores(enrollment)
            outcomes = []
            for lo in enrollment.course.learning_outcomes.all():
                mappings = lo.program_links.select_related("program_outcome")
                outcomes.append({"obj": lo, "mappings": mappings, "score": round(lo_score_map.get(lo.id, 0), 1)})

            enrollment_data.append(
                {
                    "course": enrollment.course,
                    "assessments": enrollment_assessment_breakdown(enrollment),
                    "learning_outcomes": outcomes,
                }
            )
            po_performance = calculate_po_performance(lo_score_map)

    context = {
        "student": selected_student,
        "students": students,
        "courses": courses,
        "selected_course": selected_course,
        "enrollments": enrollment_data,
        "po_performance": po_performance,
        "learning_outcome_links": LearningOutcomeProgramOutcome.objects.select_related(
            "learning_outcome", "program_outcome"
        ).filter(learning_outcome__course=selected_course)
        if selected_course
        else [],
    }
    return render(request, "assessment/student_panel.html", context)


def instructor_panel(request):
    bootstrap_demo_data()
    courses = Course.objects.all()
    selected_course = courses.filter(id=request.GET.get("course")).first() or courses.first()

    edit_component_id = request.GET.get("edit_component")
    edit_contrib_id = request.GET.get("edit_contrib")
    edit_lopo_id = request.GET.get("edit_lopo")

    component_instance = (
        AssessmentComponent.objects.filter(id=edit_component_id, course=selected_course).first() if selected_course else None
    )
    contrib_instance = (
        LearningOutcomeContribution.objects.filter(id=edit_contrib_id, assessment_component__course=selected_course).first()
        if selected_course
        else None
    )
    lopo_instance = (
        LearningOutcomeProgramOutcome.objects.filter(
            id=edit_lopo_id, learning_outcome__course=selected_course
        ).first()
        if selected_course
        else None
    )

    course_form = CourseForm(prefix="course")
    learning_outcome_form = LearningOutcomeForm(prefix="lo")
    program_outcome_form = ProgramOutcomeForm(prefix="po")
    student_form = StudentForm(prefix="student")
    enrollment_form = EnrollmentForm(prefix="enroll")
    component_form = AssessmentComponentForm(prefix="component", instance=component_instance)
    lo_contribution_form = LearningOutcomeContributionForm(prefix="contrib", instance=contrib_instance)
    lopo_form = LearningOutcomeProgramOutcomeForm(prefix="lopo", instance=lopo_instance)

    def limit_forms(course):
        if not course:
            return
        lo_contribution_form.fields["assessment_component"].queryset = course.assessments.all()
        lo_contribution_form.fields["learning_outcome"].queryset = course.learning_outcomes.all()
        lopo_form.fields["learning_outcome"].queryset = course.learning_outcomes.all()
        enrollment_form.fields["student"].queryset = Student.objects.all()

    limit_forms(selected_course)

    if request.method == "POST" and selected_course:
        form_type = request.POST.get("form_type")

        def parse_id(value):
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        if form_type == "course":
            course_form = CourseForm(request.POST, prefix="course")
            if course_form.is_valid():
                new_course = course_form.save()
                selected_course = new_course
                messages.success(request, f"Ders oluşturuldu: {new_course.code}")
                _backup_database()
            else:
                messages.error(request, "Ders oluşturulamadı.")

        elif form_type == "po":
            program_outcome_form = ProgramOutcomeForm(request.POST, prefix="po")
            if program_outcome_form.is_valid():
                po = program_outcome_form.save()
                messages.success(request, f"PÇ eklendi: {po.code}")
                _backup_database()
            else:
                messages.error(request, "PÇ eklenemedi.")

        elif form_type == "student":
            student_form = StudentForm(request.POST, prefix="student")
            if student_form.is_valid():
                student = student_form.save()
                messages.success(request, f"Öğrenci eklendi: {student.full_name}")
                _backup_database()
            else:
                messages.error(request, "Öğrenci eklenemedi.")

        elif form_type == "student_delete":
            object_id = parse_id(request.POST.get("object_id"))
            student = Student.objects.filter(id=object_id).first()
            if student:
                student.delete()
                messages.success(request, "Öğrenci silindi.")
                _backup_database()
            else:
                messages.error(request, "Öğrenci silinemedi.")

        elif form_type == "enrollment":
            enrollment_form = EnrollmentForm(request.POST, prefix="enroll")
            if enrollment_form.is_valid():
                enrollment = enrollment_form.save(commit=False)
                enrollment.course = selected_course
                try:
                    enrollment.save()
                    messages.success(request, "Öğrenci derse eklendi.")
                    _backup_database()
                except Exception:
                    messages.error(request, "Bu öğrenci zaten bu derse kayıtlı olabilir.")
            else:
                messages.error(request, "Öğrenci derse eklenemedi.")

        elif form_type == "enrollment_delete":
            object_id = parse_id(request.POST.get("object_id"))
            enrollment = Enrollment.objects.filter(id=object_id, course=selected_course).first()
            if enrollment:
                enrollment.delete()
                messages.success(request, "Ders kaydı silindi.")
                _backup_database()
            else:
                messages.error(request, "Ders kaydı silinemedi.")

        elif form_type == "lo":
            learning_outcome_form = LearningOutcomeForm(request.POST, prefix="lo")
            if learning_outcome_form.is_valid():
                lo = learning_outcome_form.save(commit=False)
                lo.course = selected_course
                lo.save()
                messages.success(request, f"LO eklendi: {lo.code}")
                _backup_database()
            else:
                messages.error(request, "LO eklenemedi.")

        elif form_type == "component_delete":
            object_id = parse_id(request.POST.get("object_id"))
            comp = AssessmentComponent.objects.filter(id=object_id, course=selected_course).first()
            if comp:
                comp.delete()
                messages.success(request, f"Bileşen silindi: {comp.name}")
                _backup_database()
            component_form = AssessmentComponentForm(prefix="component")

        elif form_type == "component":
            object_id = parse_id(request.POST.get("object_id"))
            instance = AssessmentComponent.objects.filter(id=object_id, course=selected_course).first()
            component_form = AssessmentComponentForm(request.POST, prefix="component", instance=instance)
            if component_form.is_valid():
                comp = component_form.save(commit=False)
                comp.course = selected_course
                comp.save()
                messages.success(request, f"Bileşen kaydedildi: {comp.name}")
                _backup_database()
            else:
                messages.error(request, "Bileşen eklenemedi/düzenlenemedi, alanları kontrol edin.")

        elif form_type == "contrib_delete":
            object_id = parse_id(request.POST.get("object_id"))
            contrib = LearningOutcomeContribution.objects.filter(
                id=object_id, assessment_component__course=selected_course
            ).first()
            if contrib:
                contrib.delete()
                messages.success(request, "ÖÇ katkısı silindi.")
                _backup_database()
            lo_contribution_form = LearningOutcomeContributionForm(prefix="contrib")

        elif form_type == "contrib":
            object_id = parse_id(request.POST.get("object_id"))
            instance = LearningOutcomeContribution.objects.filter(
                id=object_id, assessment_component__course=selected_course
            ).first()
            lo_contribution_form = LearningOutcomeContributionForm(request.POST, prefix="contrib", instance=instance)
            lo_contribution_form.fields["assessment_component"].queryset = selected_course.assessments.all()
            lo_contribution_form.fields["learning_outcome"].queryset = selected_course.learning_outcomes.all()
            if lo_contribution_form.is_valid():
                lo_contribution_form.save()
                messages.success(request, "ÖÇ katkısı kaydedildi.")
                _backup_database()
            else:
                messages.error(request, "ÖÇ katkısı kaydedilemedi.")

        elif form_type == "lopo_delete":
            object_id = parse_id(request.POST.get("object_id"))
            link = LearningOutcomeProgramOutcome.objects.filter(
                id=object_id, learning_outcome__course=selected_course
            ).first()
            if link:
                link.delete()
                messages.success(request, "LO–PO ağırlığı silindi.")
                _backup_database()
            lopo_form = LearningOutcomeProgramOutcomeForm(prefix="lopo")

        elif form_type == "lopo":
            object_id = parse_id(request.POST.get("object_id"))
            instance = LearningOutcomeProgramOutcome.objects.filter(
                id=object_id, learning_outcome__course=selected_course
            ).first()
            lopo_form = LearningOutcomeProgramOutcomeForm(request.POST, prefix="lopo", instance=instance)
            lopo_form.fields["learning_outcome"].queryset = selected_course.learning_outcomes.all()
            if lopo_form.is_valid():
                lopo_form.save()
                messages.success(request, "LO–PO ağırlığı kaydedildi.")
                _backup_database()
            else:
                messages.error(request, "LO–PO ağırlığı kaydedilemedi.")

        limit_forms(selected_course)
        _update_po_heatmap()
        cache.delete("analytics_panel_v1")

        return render(
            request,
            "assessment/instructor_panel.html",
            _instructor_context(
                selected_course,
                courses,
                course_form,
                learning_outcome_form,
                program_outcome_form,
                student_form,
                enrollment_form,
                component_form,
                lo_contribution_form,
                lopo_form,
                edit_component_id,
                edit_contrib_id,
                edit_lopo_id,
            ),
        )

    return render(
        request,
        "assessment/instructor_panel.html",
        _instructor_context(
            selected_course,
            courses,
            course_form,
            learning_outcome_form,
            program_outcome_form,
            student_form,
            enrollment_form,
            component_form,
            lo_contribution_form,
            lopo_form,
            edit_component_id,
            edit_contrib_id,
            edit_lopo_id,
        ),
    )


def _instructor_context(
    selected_course,
    courses,
    course_form,
    learning_outcome_form,
    program_outcome_form,
    student_form,
    enrollment_form,
    component_form,
    lo_contribution_form,
    lopo_form,
    edit_component_id=None,
    edit_contrib_id=None,
    edit_lopo_id=None,
):
    return {
        "selected_course": selected_course,
        "courses": courses,
        "students": Student.objects.all(),
        "enrollments": Enrollment.objects.filter(course=selected_course).select_related("student")
        if selected_course
        else [],
        "course_form": course_form,
        "learning_outcome_form": learning_outcome_form,
        "program_outcome_form": program_outcome_form,
        "student_form": student_form,
        "enrollment_form": enrollment_form,
        "component_form": component_form,
        "lo_contribution_form": lo_contribution_form,
        "lopo_form": lopo_form,
        "edit_component_id": edit_component_id,
        "edit_contrib_id": edit_contrib_id,
        "edit_lopo_id": edit_lopo_id,
        "assessments": AssessmentComponent.objects.filter(course=selected_course) if selected_course else [],
        "lo_contributions": LearningOutcomeContribution.objects.select_related(
            "assessment_component", "learning_outcome"
        ).filter(assessment_component__course=selected_course)
        if selected_course
        else [],
        "lo_links": LearningOutcomeProgramOutcome.objects.select_related("learning_outcome", "program_outcome").filter(
            learning_outcome__course=selected_course
        )
        if selected_course
        else [],
    }


def _read_xlsx_preview_from_zip(zfile, max_rows=None):
    sheet_names = [name for name in zfile.namelist() if name.startswith("xl/worksheets/sheet")]
    if not sheet_names:
        return []
    sheet = sheet_names[0]
    shared = []
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    if "xl/sharedStrings.xml" in zfile.namelist():
        root = ET.fromstring(zfile.read("xl/sharedStrings.xml"))
        for item in root.findall("a:si", ns):
            texts = [node.text or "" for node in item.findall(".//a:t", ns)]
            shared.append("".join(texts))
    root = ET.fromstring(zfile.read(sheet))
    rows = root.findall("a:sheetData/a:row", ns)
    preview = []
    row_block = rows if max_rows is None else rows[:max_rows]
    for row in row_block:
        values = []
        for cell in row.findall("a:c", ns):
            value = cell.find("a:v", ns)
            if value is None:
                values.append("")
                continue
            if cell.get("t") == "s":
                index = int(value.text)
                values.append(shared[index] if index < len(shared) else "")
            else:
                values.append(value.text)
        preview.append(values)
    return preview


def _read_xlsx_preview(path: Path, max_rows=None):
    try:
        with zipfile.ZipFile(path) as zfile:
            return _read_xlsx_preview_from_zip(zfile, max_rows=max_rows)
    except Exception:
        return []


def _read_xlsx_preview_from_bytes(data, max_rows=None):
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zfile:
            return _read_xlsx_preview_from_zip(zfile, max_rows=max_rows)
    except Exception:
        return []


def _normalize_header(header):
    if not header:
        return ""
    return header.split("_")[0].strip()


def _component_columns(headers):
    columns = {}
    pattern = re.compile(r"^(?P<name>.+)\(%(?P<weight>\d+)\)$")
    for index, header in enumerate(headers):
        clean = _normalize_header(header)
        match = pattern.match(clean)
        if not match:
            continue
        weight = int(match.group("weight"))
        if weight < 0 or weight > 100:
            continue
        columns[index] = {"name": match.group("name").strip(), "weight": weight}
    return columns


def _find_header_index(header_map, candidates):
    for candidate in candidates:
        if candidate in header_map:
            return header_map[candidate]
    return None


def _backup_database():
    db_path = Path(settings.DATABASES["default"]["NAME"])
    if not db_path.exists():
        return
    backup_dir = Path(settings.BASE_DIR) / "db_backups"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"db_{timestamp}.sqlite3"
    shutil.copy2(db_path, backup_path)


def _update_po_heatmap(courses=None, program_outcomes=None):
    courses = courses or list(Course.objects.all())
    program_outcomes = program_outcomes or list(ProgramOutcome.objects.all())
    links = list(
        LearningOutcomeProgramOutcome.objects.select_related(
            "learning_outcome", "program_outcome", "learning_outcome__course"
        ).all()
    )
    for course in courses:
        for po in program_outcomes:
            weights = [
                link.weight
                for link in links
                if link.learning_outcome.course_id == course.id and link.program_outcome_id == po.id
            ]
            avg_weight = round(sum(weights) / len(weights), 2) if weights else 0
            percent = int((avg_weight / 5) * 100) if avg_weight else 0
            CoursePOHeatmap.objects.update_or_create(
                course=course,
                program_outcome=po,
                defaults={"avg_weight": avg_weight, "percent": percent},
            )


def _split_name(full_name):
    if not full_name:
        return "", ""
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], ""
    return " ".join(parts[:-1]), parts[-1]


def _build_course_grade_table(course):
    if not course:
        return [], [], []
    assessments = list(AssessmentComponent.objects.filter(course=course).order_by("name"))
    enrollments = list(
        Enrollment.objects.filter(course=course)
        .select_related("student")
        .order_by("student__student_number", "student__full_name")
    )
    if not enrollments and not assessments:
        return [], [], []

    headers = ["No", "Öğrenci No", "Adı", "Soyadı", "Snf", "Girme Durum"]
    headers += [f"{comp.name}(%{comp.weight_percent})" for comp in assessments]
    headers.append("Harf Notu")

    numeric_columns = list(range(6, 6 + len(assessments)))
    score_map = {}
    if enrollments and assessments:
        score_map = {
            (sa.enrollment_id, sa.assessment_component_id): sa.score
            for sa in StudentAssessment.objects.filter(
                enrollment__in=enrollments, assessment_component__in=assessments
            )
        }

    rows = []
    for index, enrollment in enumerate(enrollments, start=1):
        student = enrollment.student
        first, last = _split_name(student.full_name)
        row = [
            str(index),
            student.student_number or "",
            first,
            last,
            str(enrollment.class_level) if enrollment.class_level is not None else "",
            enrollment.entry_status or "",
        ]
        for comp in assessments:
            score = score_map.get((enrollment.id, comp.id))
            row.append("" if score is None else str(score))
        row.append(enrollment.letter_grade or "")
        rows.append(row)
    return headers, rows, numeric_columns


def grade_template_download(request):
    template_name = "Sample Excel Format from OBS.xlsx"
    template_path = Path(settings.BASE_DIR) / template_name
    if not template_path.exists():
        raise Http404("Şablon dosyası bulunamadı.")
    return FileResponse(
        template_path.open("rb"),
        as_attachment=True,
        filename=template_name,
    )


@require_POST
def grade_preview(request):
    uploaded = request.FILES.get("grades_file")
    if not uploaded:
        return JsonResponse({"error": "Excel dosyası bulunamadı."}, status=400)

    preview = _read_xlsx_preview_from_bytes(uploaded.read())
    if not preview:
        return JsonResponse({"error": "Excel dosyası okunamadı. Lütfen .xlsx formatı kullanın."}, status=400)

    raw_headers = preview[0]
    headers = [_normalize_header(header) for header in raw_headers]
    header_len = len(headers)
    rows = []
    for row in preview[1:]:
        if len(row) < header_len:
            row = row + [""] * (header_len - len(row))
        rows.append(row[:header_len])

    numeric_columns = sorted(_component_columns(headers).keys())
    return JsonResponse(
        {
            "filename": uploaded.name,
            "headers": headers,
            "rows": rows,
            "numeric_columns": numeric_columns,
        }
    )


def grade_upload(request):
    bootstrap_demo_data()
    courses = Course.objects.all()
    selected_course = courses.filter(id=request.GET.get("course")).first() or courses.first()

    uploaded_filename = None
    use_db_table = False

    template_name = "Sample Excel Format from OBS.xlsx"
    template_path = Path(settings.BASE_DIR) / template_name
    template_available = template_path.exists()
    table_headers = []
    table_rows = []
    numeric_columns = []

    if request.method == "POST":
        selected_course = courses.filter(id=request.POST.get("course")).first() or selected_course
        form_type = request.POST.get("form_type")
        if form_type == "upload":
            uploaded = request.FILES.get("grades_file")
            if uploaded:
                uploaded_filename = uploaded.name
                messages.success(request, f"Dosya alındı: {uploaded.name} (işleme alınmadı).")
            else:
                messages.error(request, "Lütfen bir Excel dosyası seçin.")
        elif form_type == "save_grades" and selected_course:
            try:
                row_count = int(request.POST.get("row_count", 0))
                col_count = int(request.POST.get("col_count", len(table_headers)))
            except ValueError:
                row_count = 0
                col_count = len(table_headers)
            if not table_headers and col_count:
                table_headers = [request.POST.get(f"header_{idx}", "") for idx in range(col_count)]

            table_rows = []
            for row_index in range(row_count):
                row = []
                for col_index in range(col_count):
                    row.append(request.POST.get(f"cell_{row_index}_{col_index}", "").strip())
                table_rows.append(row)

            if not table_headers:
                messages.error(request, "Tablo başlıkları bulunamadı; kayıt yapılamadı.")
            else:
                with transaction.atomic():
                    component_columns = _component_columns(table_headers)
                    numeric_columns = sorted(component_columns.keys())
                    if component_columns:
                        expected_names = {info["name"] for info in component_columns.values()}
                        removed_qs = AssessmentComponent.objects.filter(course=selected_course).exclude(
                            name__in=expected_names
                        )
                        removed_count = removed_qs.count()
                        if removed_count:
                            removed_qs.delete()
                            messages.info(request, f"Excel'de olmayan {removed_count} bileşen kaldırıldı.")
                    component_map = {}
                    for col_index, info in component_columns.items():
                        component, _ = AssessmentComponent.objects.get_or_create(
                            course=selected_course, name=info["name"]
                        )
                        if component.weight_percent != info["weight"]:
                            component.weight_percent = info["weight"]
                            component.save(update_fields=["weight_percent"])
                        component_map[col_index] = component

                    header_map = {_normalize_header(header): idx for idx, header in enumerate(table_headers)}
                    student_no_idx = _find_header_index(
                        header_map, ["Öğrenci No", "Ogrenci No", "Student No"]
                    )
                    name_idx = _find_header_index(header_map, ["Adı", "Adi", "Name"])
                    surname_idx = _find_header_index(header_map, ["Soyadı", "Soyadi", "Surname"])
                    class_idx = _find_header_index(header_map, ["Snf", "Sınıf", "Sinif", "Class"])
                    entry_idx = _find_header_index(
                        header_map, ["Girme Durum", "Girme Durumu", "Entry Status"]
                    )
                    letter_idx = _find_header_index(
                        header_map, ["Harf Notu", "Harf Not", "Letter Grade"]
                    )

                    if student_no_idx is None:
                        messages.error(request, "Öğrenci No sütunu bulunamadı; kayıt yapılamadı.")
                    else:
                        updated = 0
                        for row in table_rows:
                            if student_no_idx >= len(row):
                                continue
                            student_number = row[student_no_idx].strip()
                            if not student_number:
                                continue

                            first = row[name_idx].strip() if name_idx is not None and name_idx < len(row) else ""
                            last = row[surname_idx].strip() if surname_idx is not None and surname_idx < len(row) else ""
                            full_name = f"{first} {last}".strip()

                            student, _ = Student.objects.get_or_create(
                                student_number=student_number,
                                defaults={"full_name": full_name or student_number},
                            )
                            if full_name and student.full_name != full_name:
                                student.full_name = full_name
                                student.save(update_fields=["full_name"])

                            enrollment = Enrollment.objects.filter(
                                student=student, course=selected_course
                            ).first()
                            if not enrollment:
                                enrollment = Enrollment.objects.create(
                                    student=student, course=selected_course, year=2023
                                )

                            if class_idx is not None and class_idx < len(row):
                                class_val = row[class_idx].strip()
                                enrollment.class_level = int(class_val) if class_val.isdigit() else None
                            if entry_idx is not None and entry_idx < len(row):
                                enrollment.entry_status = row[entry_idx].strip()
                            if letter_idx is not None and letter_idx < len(row):
                                enrollment.letter_grade = row[letter_idx].strip()
                            enrollment.save()

                            for col_index, component in component_map.items():
                                if col_index >= len(row):
                                    continue
                                raw_score = row[col_index].strip()
                                if not raw_score:
                                    continue
                                try:
                                    score = float(raw_score.replace(",", "."))
                                except ValueError:
                                    continue
                                assessment, _ = StudentAssessment.objects.get_or_create(
                                    enrollment=enrollment, assessment_component=component
                                )
                                if assessment.score != score:
                                    assessment.score = score
                                    assessment.save(update_fields=["score"])
                            updated += 1
                        messages.success(
                            request,
                            f"Notlar kaydedildi. Güncellenen öğrenci sayısı: {updated}",
                        )
                        _backup_database()
                use_db_table = True
                cache.delete("analytics_panel_v1")

    if selected_course:
        has_grade_data = StudentAssessment.objects.filter(enrollment__course=selected_course).exists()
        if use_db_table or has_grade_data:
            db_headers, db_rows, db_numeric = _build_course_grade_table(selected_course)
            if db_headers:
                table_headers = db_headers
                table_rows = db_rows
                numeric_columns = db_numeric

    if not table_headers and template_available:
        raw_rows = _read_xlsx_preview(template_path)
        if raw_rows:
            table_headers = [_normalize_header(header) for header in raw_rows[0]]
            header_len = len(table_headers)
            for row in raw_rows[1:]:
                if len(row) < header_len:
                    row = row + [""] * (header_len - len(row))
                table_rows.append(row[:header_len])
            numeric_columns = sorted(_component_columns(table_headers).keys())

    context = {
        "courses": courses,
        "selected_course": selected_course,
        "uploaded_filename": uploaded_filename,
        "template_available": template_available,
        "template_name": template_name,
        "table_headers": table_headers,
        "table_rows": table_rows,
        "numeric_columns": numeric_columns,
        "row_count": len(table_rows),
        "col_count": len(table_headers),
    }
    return render(request, "assessment/grade_upload.html", context)


def analytics_panel(request):
    """LO-PO bağlantılarını grafik/harita görünümünde sunar."""
    bootstrap_demo_data()
    cache_key = "analytics_panel_v2"
    cached_context = cache.get(cache_key)
    if cached_context:
        return render(request, "assessment/analytics.html", cached_context)

    courses = list(Course.objects.all())
    program_outcomes = list(ProgramOutcome.objects.all())
    if not CoursePOHeatmap.objects.exists():
        _update_po_heatmap(courses, program_outcomes)
    heatmap_items = {
        (item.course_id, item.program_outcome_id): item
        for item in CoursePOHeatmap.objects.filter(course__in=courses, program_outcome__in=program_outcomes)
    }

    heatmap = []
    for course in courses:
        row = {"course": course, "values": []}
        for po in program_outcomes:
            item = heatmap_items.get((course.id, po.id))
            avg_weight = item.avg_weight if item else 0
            percent = item.percent if item else 0
            row["values"].append({"po": po, "value": avg_weight, "percent": percent})
        heatmap.append(row)

    # Kenar listesi: LO -> PO bağlantıları
    edges = [
        {
            "course": link.learning_outcome.course,
            "lo": link.learning_outcome,
            "po": link.program_outcome,
            "weight": link.weight,
        }
        for link in LearningOutcomeProgramOutcome.objects.select_related(
            "learning_outcome", "program_outcome", "learning_outcome__course"
        )
    ]

    # Not bileşeni katkıları
    contribs = list(
        LearningOutcomeContribution.objects.select_related(
            "assessment_component", "learning_outcome", "assessment_component__course"
        )
        .order_by("assessment_component__course__code", "assessment_component__name")
        .all()
    )

    context = {
        "courses": courses,
        "program_outcomes": program_outcomes,
        "heatmap": heatmap,
        "edges": edges,
        "contribs": contribs,
    }
    cache.set(cache_key, context, 300)
    return render(request, "assessment/analytics.html", context)


def dean_panel(request):
    """Üst yönetim paneli: tüm ders, öğrenci ve katkı verileri."""
    bootstrap_demo_data()
    courses = (
        Course.objects.annotate(
            lo_count=Count("learning_outcomes", distinct=True),
            assessment_count=Count("assessments", distinct=True),
            enrollment_count=Count("enrollments", distinct=True),
        )
        .order_by("code")
    )
    students = Student.objects.annotate(enrollment_count=Count("enrollments", distinct=True)).order_by("full_name")
    enrollments = Enrollment.objects.select_related("student", "course").order_by(
        "course__code", "student__full_name"
    )
    program_outcomes = ProgramOutcome.objects.order_by("code")
    learning_outcomes = LearningOutcome.objects.select_related("course").order_by("course__code", "code")
    assessments = AssessmentComponent.objects.select_related("course").order_by("course__code", "name")
    lo_po_links = LearningOutcomeProgramOutcome.objects.select_related(
        "learning_outcome", "program_outcome", "learning_outcome__course"
    ).order_by("learning_outcome__course__code", "learning_outcome__code")
    contribs = LearningOutcomeContribution.objects.select_related(
        "assessment_component", "learning_outcome", "assessment_component__course"
    ).order_by("assessment_component__course__code", "assessment_component__name")

    context = {
        "courses": courses,
        "students": students,
        "enrollments": enrollments,
        "program_outcomes": program_outcomes,
        "learning_outcomes": learning_outcomes,
        "assessments": assessments,
        "lo_po_links": lo_po_links,
        "contribs": contribs,
        "totals": {
            "courses": courses.count(),
            "students": students.count(),
            "enrollments": enrollments.count(),
            "program_outcomes": program_outcomes.count(),
            "learning_outcomes": learning_outcomes.count(),
            "assessments": assessments.count(),
        },
    }
    return render(request, "assessment/dean_panel.html", context)


def schema_overview(request):
    """Veritabanı şemasını alan tipleri ve ilişkilerle birlikte gösterir."""
    models = [
        Course,
        LearningOutcome,
        ProgramOutcome,
        LearningOutcomeProgramOutcome,
        AssessmentComponent,
        LearningOutcomeContribution,
        Student,
        Enrollment,
        StudentAssessment,
    ]
    model_rows = []
    for model in models:
        fields = []
        for field in model._meta.get_fields():
            # Sadece ileri alanları ve concrete alanları göster.
            if field.auto_created and not field.concrete:
                continue
            relation = ""
            if field.is_relation:
                if field.many_to_one or field.one_to_one:
                    relation = f"FK → {field.related_model.__name__}"
                elif field.many_to_many:
                    relation = f"M2M → {field.related_model.__name__}"
            fields.append(
                {
                    "name": field.name,
                    "type": field.get_internal_type(),
                    "relation": relation,
                    "null": getattr(field, "null", False),
                    "blank": getattr(field, "blank", False),
                }
            )
        model_rows.append({"model": model.__name__, "fields": fields})

    return render(request, "assessment/schema.html", {"models": model_rows})


def course_difficulty(course, student=None):
    """Heuristik zorluk tahmini ve gerekçeleri (öğrenci geçmişi varsa ona göre)."""
    class_avg = (
        StudentAssessment.objects.filter(enrollment__course=course).aggregate(avg=Avg("score")).get("avg") or 80
    )
    personal_avg = None
    if student:
        personal_avg = (
            StudentAssessment.objects.filter(enrollment__course=course, enrollment__student=student)
            .aggregate(avg=Avg("score"))
            .get("avg")
        )

    max_weight = (
        AssessmentComponent.objects.filter(course=course).aggregate(m=Max("weight_percent")).get("m") or 0
    )
    lo_po_count = LearningOutcomeProgramOutcome.objects.filter(learning_outcome__course=course).count()

    reasons = []
    score = 0

    if personal_avg is not None:
        if personal_avg < 60:
            score += 2
            reasons.append(f"Daha önce bu dersten kaldın (~{round(personal_avg)}).")
        elif personal_avg < 75:
            score += 1
            reasons.append(f"Önceki notun düşük (~{round(personal_avg)}).")
        else:
            reasons.append(f"Önceki performansın iyi (~{round(personal_avg)}).")
    else:
        if class_avg < 75:
            score += 1
            reasons.append(f"Sınıf ortalaması düşük (~{round(class_avg)}).")
        if class_avg < 65:
            score += 1
            reasons.append("Sınıf ortalaması 65'in altında.")
#test
    if max_weight >= 50:
        score += 1
        reasons.append(f"Bir bileşen ders notunun %{max_weight}'ini belirliyor.")
    if lo_po_count >= 6:
        score += 1
        reasons.append("Çok sayıda LO–PO ilişkisi: geniş kapsam.")

    if score >= 3:
        label = "Zor"
    elif score == 2:
        label = "Orta"
    else:
        label = "Kolay"

    return {
        "label": label,
        "avg_score": round(personal_avg if personal_avg is not None else class_avg, 1),
        "max_weight": max_weight,
        "reasons": reasons or ["Mevcut veriye göre dengeli görünüyor."],
        "personal": personal_avg is not None,
    }


def course_planner(request):
    """Öğrencilerin ders alıp bırakabileceği ve zorluk tahminlerini göreceği sayfa."""
    bootstrap_demo_data()
    students = Student.objects.all()
    selected_student = students.filter(id=request.GET.get("student")).first() or students.first()

    if request.method == "POST" and selected_student:
        action = request.POST.get("action")
        course_id = request.POST.get("course")
        course = Course.objects.filter(id=course_id).first()
        if course:
            if action == "add":
                Enrollment.objects.get_or_create(student=selected_student, course=course, year=2023)
                messages.success(request, f"{course.code} eklendi.")
            elif action == "drop":
                Enrollment.objects.filter(student=selected_student, course=course).delete()
                messages.success(request, f"{course.code} bırakıldı.")
            elif action == "set_result":
                result_val = request.POST.get("result")
                enrollment = Enrollment.objects.filter(student=selected_student, course=course).first()
                if enrollment and result_val in dict(Enrollment.RESULT_CHOICES):
                    enrollment.result = result_val
                    enrollment.save(update_fields=["result"])
                    messages.success(request, f"{course.code} için durum güncellendi: {result_val}")
        return redirect(request.path + f"?student={selected_student.id}")

    enrolled = (
        Enrollment.objects.filter(student=selected_student)
        .select_related("course")
        .order_by("course__code")
        if selected_student
        else []
    )
    enrolled_data = [
        {"enrollment": e, "final": final_score(e)}
        for e in enrolled
    ]
    enrolled_ids = [e.course_id for e in enrolled]
    available_courses = Course.objects.exclude(id__in=enrolled_ids)

    passed_los = LearningOutcome.objects.filter(
        course__enrollments__student=selected_student, course__enrollments__result="passed"
    )
    passed_lo_codes_global = set(passed_los.values_list("code", flat=True))

    def lo_coverage(course, known_codes):
        total = 0
        covered = 0
        for contrib in LearningOutcomeContribution.objects.select_related("assessment_component", "learning_outcome").filter(
            assessment_component__course=course
        ):
            weight = contrib.assessment_component.weight_percent * contrib.contribution_percent / 100
            total += weight
            if contrib.learning_outcome.code in known_codes:
                covered += weight
        return round((covered / total) * 100, 1) if total else 0

    available_data = []
    for course in available_courses:
        diff = course_difficulty(course, selected_student)
        course_los = list(course.learning_outcomes.all())
        known = [lo.code for lo in course_los if lo.code in passed_lo_codes_global]
        missing = [lo.code for lo in course_los if lo.code not in passed_lo_codes_global]
        coverage = lo_coverage(course, passed_lo_codes_global)
        if coverage >= 50:
            if diff["label"] == "Orta":
                diff["label"] = "Kolay"
            diff["reasons"].append(f"Geçtiğin derslerdeki LO'lar bu dersin %{coverage} gereksinimini kapsıyor.")
        elif coverage < 50:
            diff["label"] = "Zor"
            diff["reasons"].append("LO örtüşmesi düşük; konular senin için büyük ölçüde yeni.")

        available_data.append(
            {
                "course": course,
                "diff": diff,
                "known_los": known,
                "new_los": missing,
                "coverage": coverage,
            }
        )

    context = {
        "students": students,
        "student": selected_student,
        "enrolled": enrolled_data,
        "available": available_data,
    }
    return render(request, "assessment/course_planner.html", context)
