from django import forms

from .models import (
    AssessmentComponent,
    Course,
    LearningOutcome,
    LearningOutcomeContribution,
    LearningOutcomeProgramOutcome,
    Enrollment,
    ProgramOutcome,
    Student,
)


class AssessmentComponentForm(forms.ModelForm):
    class Meta:
        model = AssessmentComponent
        fields = ("name", "weight_percent")
        labels = {"name": "Bileşen adı", "weight_percent": "Ağırlık (%)"}
        help_texts = {"weight_percent": "Ders notundaki yüzdesi. Toplam %100'ü geçmesin."}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Vize / Proje / Lab", "class": "input"}),
            "weight_percent": forms.NumberInput(attrs={"placeholder": "Örn: 40", "class": "input"}),
        }


class LearningOutcomeContributionForm(forms.ModelForm):
    class Meta:
        model = LearningOutcomeContribution
        fields = ("assessment_component", "learning_outcome", "contribution_percent")
        labels = {
            "assessment_component": "Not bileşeni",
            "learning_outcome": "Öğrenme çıktısı",
            "contribution_percent": "Katkı (%)",
        }
        help_texts = {"contribution_percent": "Bu bileşenin hangi ÖÇ'ye ne kadar hizmet ettiğini yazın (0-100)."}
        widgets = {
            "contribution_percent": forms.NumberInput(attrs={"placeholder": "Örn: 60", "class": "input"}),
        }


class LearningOutcomeProgramOutcomeForm(forms.ModelForm):
    class Meta:
        model = LearningOutcomeProgramOutcome
        fields = ("learning_outcome", "program_outcome", "weight")
        labels = {
            "learning_outcome": "Öğrenme çıktısı",
            "program_outcome": "Program çıktısı",
            "weight": "Ağırlık (1-5)",
        }
        help_texts = {"weight": "1: düşük katkı, 5: güçlü katkı. Aynı LO için birden fazla PÇ olabilir."}
        widgets = {
            "weight": forms.NumberInput(attrs={"placeholder": "1-5", "class": "input"}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ("code", "name", "term")
        labels = {"code": "Ders kodu", "name": "Ders adı", "term": "Dönem"}
        widgets = {
            "code": forms.TextInput(attrs={"placeholder": "BLG101", "class": "input"}),
            "name": forms.TextInput(attrs={"placeholder": "Ders adı", "class": "input"}),
            "term": forms.TextInput(attrs={"placeholder": "Güz/Bahar", "class": "input"}),
        }


class LearningOutcomeForm(forms.ModelForm):
    class Meta:
        model = LearningOutcome
        fields = ("code", "description")
        labels = {"code": "LO kodu", "description": "Açıklama"}
        widgets = {
            "code": forms.TextInput(attrs={"placeholder": "LO1", "class": "input"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Öğrenme çıktısı açıklaması", "class": "input"}),
        }


class ProgramOutcomeForm(forms.ModelForm):
    class Meta:
        model = ProgramOutcome
        fields = ("code", "title", "description")
        labels = {"code": "PÇ kodu", "title": "Başlık", "description": "Açıklama"}
        widgets = {
            "code": forms.TextInput(attrs={"placeholder": "PO5", "class": "input"}),
            "title": forms.TextInput(attrs={"placeholder": "Program çıktısı başlığı", "class": "input"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "İsteğe bağlı açıklama", "class": "input"}),
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ("full_name", "student_number")
        labels = {"full_name": "Ad Soyad", "student_number": "Öğrenci No"}
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "Örn: Ayşe Demir", "class": "input"}),
            "student_number": forms.TextInput(attrs={"placeholder": "20231234", "class": "input"}),
        }


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ("student", "year", "section", "result")
        labels = {
            "student": "Öğrenci",
            "year": "Yıl",
            "section": "Şube",
            "result": "Durum",
        }
        widgets = {
            "year": forms.NumberInput(attrs={"placeholder": "2023", "class": "input"}),
            "section": forms.TextInput(attrs={"placeholder": "A/B", "class": "input"}),
            "result": forms.Select(attrs={"class": "input"}),
        }
