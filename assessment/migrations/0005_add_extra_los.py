from django.db import migrations


def add_extra_los(apps, schema_editor):
    Course = apps.get_model("assessment", "Course")
    LearningOutcome = apps.get_model("assessment", "LearningOutcome")
    LearningOutcomeProgramOutcome = apps.get_model("assessment", "LearningOutcomeProgramOutcome")
    AssessmentComponent = apps.get_model("assessment", "AssessmentComponent")
    LearningOutcomeContribution = apps.get_model("assessment", "LearningOutcomeContribution")
    ProgramOutcome = apps.get_model("assessment", "ProgramOutcome")

    po5, _ = ProgramOutcome.objects.get_or_create(code="PO5", defaults={"title": "Araştırma ve Yenilik"})

    for course in Course.objects.all():
        # LO4 ekle
        lo_code = "LO4"
        lo, created_lo = LearningOutcome.objects.get_or_create(
            course=course,
            code=lo_code,
            defaults={"description": f"{course.code} dersi için ileri uygulama/araştırma çıktısı."},
        )
        # LO4 -> PO5 ağırlık 3
        LearningOutcomeProgramOutcome.objects.get_or_create(
            learning_outcome=lo, program_outcome=po5, defaults={"weight": 3}
        )

        # Eğer projeli dersse, projeye %30 katkı ekle
        project = AssessmentComponent.objects.filter(course=course, name__icontains="Proje").first()
        if project:
            LearningOutcomeContribution.objects.get_or_create(
                assessment_component=project,
                learning_outcome=lo,
                defaults={"contribution_percent": 30},
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("assessment", "0004_enrollment_result"),
    ]

    operations = [
        migrations.RunPython(add_extra_los, noop),
    ]
