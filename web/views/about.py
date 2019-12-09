from django.shortcuts import render
import pkg_resources
from stronghold.decorators import public

@public
def about(request):

    context = {
        "app_version": pkg_resources.require("elixir-daisy")[0].version

    }
    return render(
        request,
        'about.html', context
    )
