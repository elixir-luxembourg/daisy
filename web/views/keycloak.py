from functools import wraps

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from core.lcsb.oidc import (
    KeycloakBackend,
    get_keycloak_config_from_settings,
    provider_label,
)
from core.models import User
from core.synchronizers import ExternalUserNotFoundException, get_contact
from core.utils import DaisyLogger, normalized_email
from web.views.utils import is_superuser

logger = DaisyLogger(__name__)


def keycloak_required(view):
    """An instance without the integration has no Keycloak to ask, and asking raises."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not getattr(settings, "KEYCLOAK_INTEGRATION", False):
            return JsonResponse(
                {"error": "The Keycloak integration is not enabled."}, status=503
            )
        return view(request, *args, **kwargs)

    return wrapper


@login_required
@user_passes_test(is_superuser)
@keycloak_required
@require_GET
def keycloak_candidates(request, pk):
    """
    List the Keycloak accounts of the email of one DAISY user, so that an administrator can pick
    the identity to bind. A user that has an oidc_id already is immutable, see User.save().
    """
    user = get_object_or_404(User, pk=pk)
    if user.oidc_id:
        return JsonResponse({"error": "This user already has an OIDC ID."}, status=409)

    email = normalized_email(user.email)
    if not email:
        return JsonResponse({"error": "This user has no email."}, status=400)

    backend = KeycloakBackend(get_keycloak_config_from_settings())
    results = []
    for account in backend.get_users_by_email(email):
        results.append(
            {
                "id": account.id,
                "text": (
                    f"{account.first_name} {account.last_name} "
                    f"({account.email}; {provider_label(account)})"
                ),
            }
        )
    return JsonResponse({"results": results})


@login_required
@user_passes_test(is_superuser)
@keycloak_required
@require_POST
def bind_keycloak_identity(request, pk):
    """
    Store the oidc_id of the selected Keycloak account on one DAISY user.
    It never creates a user and it never touches the access records.
    """
    oidc_id = request.POST.get("oidc_id")
    if not oidc_id:
        return JsonResponse({"error": "Keycloak user ID is required."}, status=400)

    backend = KeycloakBackend(get_keycloak_config_from_settings())
    try:
        # ExternalUserNotVerifiedException is one of these
        account = backend.get_external_user_info(oidc_id)
    except ExternalUserNotFoundException:
        return JsonResponse(
            {"error": "Keycloak has no verified account with this ID."}, status=404
        )
    account_email = normalized_email(account.email)

    with transaction.atomic():
        user = get_object_or_404(User.objects.select_for_update(), pk=pk)
        if user.oidc_id:
            return JsonResponse(
                {"error": "This user already has an OIDC ID."}, status=409
            )
        if account_email != normalized_email(user.email):
            return JsonResponse(
                {"error": "This Keycloak account has another email."}, status=409
            )
        contact = get_contact(oidc_id)
        if contact:
            # a contact never blocks a user, but its access rows need a migration
            logger.warning(
                f"Contact {contact.pk} holds the Keycloak subject {oidc_id}, "
                f"the binding leaves its access records behind"
            )
        if User.objects.filter(oidc_id=oidc_id).exists():
            return JsonResponse(
                {"error": "This Keycloak account is already used by another user."},
                status=409,
            )

        user.oidc_id = oidc_id
        user.save(update_fields=["oidc_id"])

    return JsonResponse({"user": {"oidc_id": user.oidc_id}})
