import json
import requests
from typing import Tuple, Optional, TYPE_CHECKING

from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.edit import FormMixin
from sequences import get_next_value

from core.models import Contact, User
from core.constants import Groups

if TYPE_CHECKING:
    from django.http import HttpRequest


def is_ajax_request(request: "HttpRequest") -> bool:
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def is_data_steward(user):
    if user.is_part_of(Group.objects.get(name=Groups.DATA_STEWARD.value)):
        return True
    else:
        raise PermissionDenied


def can_publish(user):
    if user.can_publish():
        return True
    else:
        raise PermissionDenied


class AjaxViewMixin(SingleObjectTemplateResponseMixin, FormMixin):
    template_name_ajax = "_includes/forms.html"

    def get_template_names(self):
        if is_ajax_request(self.request):
            return [self.template_name_ajax]
        return super().get_template_names()

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if is_ajax_request(self.request):
            return JsonResponse(form.errors, status=400)
        return response

    def form_valid(self, form):
        response = super().form_valid(form)
        if is_ajax_request(self.request):
            data = {"pk": self.object.pk, "label": str(self.object)}
            return JsonResponse(data)
        return response


def get_client_ip(request):
    ip_from_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if ip_from_forwarded_for:
        return ip_from_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


def generate_elu_accession(_=None):
    elu_accession = "ELU_I_" + str(get_next_value("elu_accession", initial_value=100))
    return elu_accession


def get_user_or_contact_by_oidc_id(
    user_oidc_id,
) -> Tuple[bool, bool, Optional[User], Optional[Contact]]:
    user, contact = None, None

    try:
        user = User.objects.get(oidc_id=user_oidc_id)
        user_found = True
    except User.DoesNotExist as e:
        user_found = False

    try:
        contact = Contact.objects.get(oidc_id=user_oidc_id)
        contact_found = True
    except Contact.DoesNotExist as e:
        contact_found = False

    return user_found, contact_found, user, contact


def get_rems_forms(form_id=None):
    headers = {
        "x-rems-api-key": getattr(settings, "REMS_API_KEY"),
        "x-rems-user-id": getattr(settings, "REMS_API_USER"),
    }

    request_url = getattr(settings, "REMS_URL") + "api/forms"
    if form_id is not None:
        request_url = request_url + "/" + str(form_id)

    rems_forms_response = requests.get(
        request_url, headers=headers, verify=getattr(settings, "REMS_VERIFY_SSL")
    )
    return json.loads(rems_forms_response.text)
