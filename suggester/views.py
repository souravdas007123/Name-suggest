from django.conf import settings
from django.core import signing
from django.http import Http404
from django.shortcuts import redirect, render

from .forms import SearchForm
from .models import NameSuggestion, SearchRequest
from .services import numerology
from .services.domains import slugify
from .services.pipeline import run_search

RESULT_SALT = "naamastro-result"


def _token_for(pk: int) -> str:
    # Result URL guess nahi kiya ja sakta (DOB private rehti hai), lekin share kiya ja sakta hai.
    return signing.dumps(pk, salt=RESULT_SALT, compress=False)


def _pk_from(token: str) -> int:
    try:
        return int(signing.loads(token, salt=RESULT_SALT))
    except (signing.BadSignature, ValueError):
        raise Http404("Result nahi mila")


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
                # variations (.com taken hone par) bhi isi JSON mein, "alt" key ke neeche
                domain_status={**r.domain_status, "alt": [list(a) for a in r.alt_domains]},
                score=r.score,
            )
            for r in results
        )
        return redirect("result", token=_token_for(req.pk))
    return render(request, "suggester/home.html", {"form": form})


def result(request, token):
    req = SearchRequest.objects.filter(pk=_pk_from(token)).first()
    if req is None:
        raise Http404("Result nahi mila")

    profile = numerology.build_profile(req.dob)
    tlds = settings.NAME_SUGGESTER["TLDS"]
    primary = tlds[0]

    rows = []
    for s in req.suggestions.all():
        slug = slugify(s.name)
        status = s.domain_status
        rows.append(
            {
                "name": s.name,
                "slug": slug,
                "name_number": s.name_number,
                "compound_number": s.compound_number,
                "score": s.score,
                "strong": s.name_number in profile.strong_numbers,
                "primary_status": status.get(primary, "unknown"),
                "primary_domain": f"{slug}.{primary}",
                # sirf wahi TLDs jo sach mein check hue the
                "domains": [(f"{slug}.{t}", status[t]) for t in tlds if t in status],
                "alt": [tuple(a) for a in status.get("alt", [])],
            }
        )

    share_url = request.build_absolute_uri()
    return render(
        request,
        "suggester/result.html",
        {
            "req": req,
            "profile": profile,
            "rows": rows,
            "share_url": share_url,
            "share_text": f"Mere liye shubh company naam ({req.industry}): {share_url}",
        },
    )
