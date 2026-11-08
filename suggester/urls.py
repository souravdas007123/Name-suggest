from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("result/<str:token>/", views.result, name="result"),
    path("result/<str:token>/conflicts/<slug:slug>/", views.conflicts, name="conflicts"),
]
