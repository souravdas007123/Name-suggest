from django.contrib import admin

from .models import NameSuggestion, SearchRequest


class NameSuggestionInline(admin.TabularInline):
    model = NameSuggestion
    extra = 0


@admin.register(SearchRequest)
class SearchRequestAdmin(admin.ModelAdmin):
    list_display = ("industry", "dob", "moolank", "bhagyank", "created_at")
    inlines = [NameSuggestionInline]
