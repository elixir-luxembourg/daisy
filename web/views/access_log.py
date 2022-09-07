from django.shortcuts import render
from core.models.access import Access
from core.permissions import permission_required, Permissions


def access_history_list(request, pk):
    access = Access.objects.filter(pk=pk).first()
    logs = access.history.all()
    print("List of logs: {}".format(logs))
    return render(request, "accesses/access_logs.html", {"logs": logs})
