from django.shortcuts import render

from core.reporting import ReportParametersCollector


def issues(request):
    report_params = ReportParametersCollector.generate_for_user(request.user)
    return render(
        request,
        'issues.html',
        {
            'issues': report_params.issues
        }
    )
