from django.db import migrations


def load_demo_data(apps, schema_editor):
    Course = apps.get_model("assessment", "Course")
    ProgramOutcome = apps.get_model("assessment", "ProgramOutcome")
    LearningOutcome = apps.get_model("assessment", "LearningOutcome")
    LearningOutcomeProgramOutcome = apps.get_model("assessment", "LearningOutcomeProgramOutcome")
    AssessmentComponent = apps.get_model("assessment", "AssessmentComponent")
    LearningOutcomeContribution = apps.get_model("assessment", "LearningOutcomeContribution")
    Student = apps.get_model("assessment", "Student")
    Enrollment = apps.get_model("assessment", "Enrollment")
    StudentAssessment = apps.get_model("assessment", "StudentAssessment")

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
            if enrollment.student.full_name.startswith("Ali"):
                score = max(0, score - 8)
            student_assessments.append(
                StudentAssessment(enrollment=enrollment, assessment_component=comp, score=score)
            )
    StudentAssessment.objects.bulk_create(student_assessments)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("assessment", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_demo_data, noop),
    ]
