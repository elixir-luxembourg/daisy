from django.shortcuts import render
import pkg_resources
from stronghold.decorators import public
from django.conf import settings

@public
def about(request):

    context = {
        "app_version": pkg_resources.require("elixir-daisy")[0].version,
        "demo_mode":settings.DEMO_MODE


    }
    return render(
        request,
        'about.html', context
    )
