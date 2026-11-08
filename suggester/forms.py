from datetime import date

from django import forms

TONES = [
    ("", "Koi bhi"),
    ("modern", "Modern"),
    ("traditional", "Traditional"),
    ("premium", "Premium"),
    ("playful", "Playful"),
]


class SearchForm(forms.Form):
    dob = forms.DateField(
        label="Janm tarikh",
        widget=forms.DateInput(attrs={"type": "date", "class": "input", "required": True}),
    )
    industry = forms.CharField(
        label="Business ka kshetra",
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "input", "placeholder": "jaise food", "autocomplete": "off", "required": True}
        ),
    )
    keywords = forms.CharField(
        label="Pasand ke shabd (optional)",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "ganga, fresh", "autocomplete": "off"}),
    )
    tone = forms.ChoiceField(
        label="Naam ka andaaz",
        choices=TONES,
        required=False,
        initial="",
        widget=forms.RadioSelect,
    )

    def clean_dob(self):
        dob = self.cleaned_data["dob"]
        if dob > date.today() or dob.year < 1900:
            raise forms.ValidationError("Sahi janm tarikh daalein.")
        return dob

    def clean_keywords(self):
        raw = self.cleaned_data.get("keywords", "")
        return ", ".join(k.strip() for k in raw.split(",") if k.strip())
