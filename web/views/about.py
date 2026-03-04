from django.shortcuts import render
from django.contrib.auth.decorators import login_not_required
from django.conf import settings


@login_not_required
def about(request):
    context = {"demo_mode": getattr(settings, "DEMO_MODE", False)}

    return render(request, "about.html", context)
