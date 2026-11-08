from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SearchForm
from .models import NameSuggestion, SearchRequest
from .services import numerology
from .services.pipeline import run_search


def home(request):
    form = SearchForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        keywords = [k.strip() for k in data["keywords"].split(",") if k.strip()]
        profile, results = run_search(
            data["dob"], data["industry"], keywords, data["tone"], settings.NAME_SUGGESTER
        )
        req = SearchRequest.objects.create(
            dob=data["dob"],
            industry=data["industry"],
            keywords=data["keywords"],
            tone=data["tone"],
            moolank=profile.moolank,
            bhagyank=profile.bhagyank,
            sun_sign=profile.sun_sign,
        )
        NameSuggestion.objects.bulk_create(
            NameSuggestion(
                request=req,
                name=r.name,
                name_number=r.name_number,
                compound_number=r.compound_number,
                domain_status=r.domain_status,
                score=r.score,
            )
            for r in results
        )
        return redirect("result", pk=req.pk)
    return render(request, "suggester/home.html", {"form": form})


def result(request, pk):
    req = get_object_or_404(SearchRequest, pk=pk)
    profile = numerology.build_profile(req.dob)
    tlds = settings.NAME_SUGGESTER["TLDS"]
    rows = []
    for s in req.suggestions.all():
        rows.append(
            {
                "name": s.name,
                "name_number": s.name_number,
                "compound_number": s.compound_number,
                "score": s.score,
                "primary_status": s.domain_status.get(tlds[0], "unknown"),
                "domains": [(f"{s.name.lower()}.{t}", s.domain_status.get(t, "unknown")) for t in tlds],
            }
        )
    return render(
        request,
        "suggester/result.html",
        {"req": req, "profile": profile, "rows": rows},
    )
