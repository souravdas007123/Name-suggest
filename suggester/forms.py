from datetime import date

from django import forms

TONES = [
    ("", "Any"),
    ("modern", "Modern"),
    ("traditional", "Traditional"),
    ("premium", "Premium"),
    ("playful", "Playful"),
]


class SearchForm(forms.Form):
    dob = forms.DateField(
        label="Date of birth",
        widget=forms.DateInput(attrs={"type": "date", "class": "input", "required": True}),
    )
    industry = forms.CharField(
        label="Industry",
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "input", "placeholder": "e.g. food", "autocomplete": "off", "required": True}
        ),
    )
    keywords = forms.CharField(
        label="Words you like (optional)",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "ganga, fresh", "autocomplete": "off"}),
    )
    tone = forms.ChoiceField(
        label="Name style",
        choices=TONES,
        required=False,
        initial="",
        widget=forms.RadioSelect,
    )

    def clean_dob(self):
        dob = self.cleaned_data["dob"]
        if dob > date.today() or dob.year < 1900:
            raise forms.ValidationError("Enter a valid date of birth.")
        return dob

    def clean_keywords(self):
        raw = self.cleaned_data.get("keywords", "")
        return ", ".join(k.strip() for k in raw.split(",") if k.strip())
