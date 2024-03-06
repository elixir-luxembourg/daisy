from django.shortcuts import render
from stronghold.decorators import public
from django.conf import settings


@public
def about(request):
    context = {"demo_mode": getattr(settings, "DEMO_MODE", False)}

    return render(request, "about.html", context)
