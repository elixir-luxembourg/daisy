from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from core.lcsb.oidc import KeycloakBackend, get_keycloak_config_from_settings
from core.models import Contact, User
from web.views.utils import is_superuser

CONTACT_OWNS_THE_ACCOUNT = (
    "This Keycloak account belongs to a contact in DAISY. Their access records must move "
    "to a user account first, please ask an administrator."
)


def serialize_user(user):
    return {
        "id": str(user.pk),
        "text": f"{user.get_full_name()} ({user.email})",
        "oidc_id": user.oidc_id or "",
        "is_active": user.is_active,
    }


@login_required
@user_passes_test(is_superuser)
@require_GET
def keycloak_candidates(request, pk):
    """
    List the Keycloak accounts of the email of one DAISY user, so that an administrator can pick
    the identity to bind. A user that has an oidc_id already is immutable, see User.save().
    """
    user = get_object_or_404(User, pk=pk)
    if user.oidc_id:
        return JsonResponse({"error": "This user already has an OIDC ID."}, status=409)

    email = (user.email or "").strip().lower()
    if not email:
        return JsonResponse({"error": "This user has no email."}, status=400)

    backend = KeycloakBackend(get_keycloak_config_from_settings())
    results = []
    for account in backend.get_users_by_email(email):
        provider = account.identity_provider or account.username or "Keycloak"
        results.append(
            {
                "id": account.id,
                "text": f"{account.first_name} {account.last_name} ({account.email}; {provider})",
            }
        )
    return JsonResponse({"results": results})


@login_required
@user_passes_test(is_superuser)
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
    account = backend.get_external_user_info(oidc_id)
    account_email = (account.email or "").strip().lower()

    with transaction.atomic():
        user = get_object_or_404(User.objects.select_for_update(), pk=pk)
        if user.oidc_id:
            return JsonResponse(
                {"error": "This user already has an OIDC ID."}, status=409
            )
        if account_email != (user.email or "").strip().lower():
            return JsonResponse(
                {"error": "This Keycloak account has another email."}, status=409
            )
        if Contact.objects.filter(oidc_id=oidc_id).exists():
            return JsonResponse({"error": CONTACT_OWNS_THE_ACCOUNT}, status=409)
        if User.objects.filter(oidc_id=oidc_id).exists():
            return JsonResponse(
                {"error": "This Keycloak account is already used by another user."},
                status=409,
            )

        user.oidc_id = oidc_id
        user.save(update_fields=["oidc_id"])

    return JsonResponse({"user": serialize_user(user)})
