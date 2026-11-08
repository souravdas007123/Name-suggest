from datetime import date

from django import forms

TONES = [
    ("", "Koi bhi"),
    ("modern", "Modern / techy"),
    ("traditional", "Traditional / Indian"),
    ("premium", "Premium / luxury"),
    ("playful", "Playful / friendly"),
]


class SearchForm(forms.Form):
    dob = forms.DateField(
        label="Aapki Date of Birth",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    industry = forms.CharField(
        label="Company kis field mein hai?",
        max_length=100,
        help_text="Jaise: tech, food, education, fashion, finance",
    )
    keywords = forms.CharField(
        label="Koi shabd / idea (optional)",
        max_length=200,
        required=False,
        help_text="Comma se alag karein: jaise 'ganga, fresh'",
    )
    tone = forms.ChoiceField(label="Naam ka style", choices=TONES, required=False)

    def clean_dob(self):
        dob = self.cleaned_data["dob"]
        if dob > date.today() or dob.year < 1900:
            raise forms.ValidationError("Sahi date of birth daaliye.")
        return dob

    def clean_keywords(self):
        raw = self.cleaned_data.get("keywords", "")
        return ", ".join(k.strip() for k in raw.split(",") if k.strip())
