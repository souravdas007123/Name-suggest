from django.db import models


class SearchRequest(models.Model):
    dob = models.DateField()
    industry = models.CharField(max_length=100)
    keywords = models.CharField(max_length=200, blank=True)
    tone = models.CharField(max_length=30, blank=True)
    moolank = models.PositiveSmallIntegerField(null=True)
    bhagyank = models.PositiveSmallIntegerField(null=True)
    sun_sign = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.industry} ({self.dob})"


class NameSuggestion(models.Model):
    request = models.ForeignKey(SearchRequest, related_name="suggestions", on_delete=models.CASCADE)
    name = models.CharField(max_length=40)
    name_number = models.PositiveSmallIntegerField()
    compound_number = models.PositiveSmallIntegerField()
    domain_status = models.JSONField(default=dict)  # {"com": "available", "in": "taken"}
    score = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-score", "name"]

    def __str__(self):
        return self.name
