from django.shortcuts import render
from stronghold.decorators import public

@public
def about(request):
    return render(
        request,
        'about.html'
    )
