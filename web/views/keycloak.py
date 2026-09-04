from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from core.lcsb.oidc import (
    KeycloakBackend,
    get_keycloak_config_from_settings,
    parse_oidc_username,
)
from core.models import Access, Contact, User
from web.views.utils import is_data_steward


def serialize_user(user):
    return {
        "id": str(user.pk),
        "text": f"{user.get_full_name()} ({user.email})",
        "is_active": user.is_active,
    }


@login_required
@user_passes_test(is_data_steward)
@require_GET
def keycloak_custodian_lookup(request):
    email = request.GET.get("email", "").strip().lower()
    if not email:
        return JsonResponse({"results": []})

    users = User.objects.filter(email__iexact=email, oidc_id__isnull=False)
    if users.exists():
        return JsonResponse({"results": [serialize_user(user) for user in users]})

    backend = KeycloakBackend(get_keycloak_config_from_settings())
    results = []
    for user in backend.get_users_by_email(email):
        provider = user.identity_provider or "Keycloak"
        results.append(
            {
                "id": f"keycloak:{user.id}",
                "text": f"{user.first_name} {user.last_name} ({user.email}; {provider})",
                "is_active": True,
            }
        )
    return JsonResponse({"results": results})


@login_required
@user_passes_test(is_data_steward)
@require_POST
def provision_keycloak_custodian(request):
    oidc_id = request.POST.get("oidc_id")
    if not oidc_id:
        return JsonResponse({"error": "Keycloak user ID is required."}, status=400)

    backend = KeycloakBackend(get_keycloak_config_from_settings())
    account = backend.get_external_user_info(oidc_id)
    email = (account.get("email") or "").strip().lower()
    if not email:
        return JsonResponse({"error": "Keycloak user has no email."}, status=400)

    with transaction.atomic():
        user = User.objects.select_for_update().filter(oidc_id=oidc_id).first()
        contact = Contact.objects.select_for_update().filter(oidc_id=oidc_id).first()
        if user and contact:
            return JsonResponse(
                {"error": "OIDC ID belongs to both a User and a Contact."}, status=409
            )
        if not user:
            matching_users = list(
                User.objects.select_for_update().filter(email__iexact=email)
            )
            if len(matching_users) > 1:
                return JsonResponse(
                    {"error": "Multiple DAISY users share this email."}, status=409
                )
            if matching_users:
                user = matching_users[0]
                if user.oidc_id and user.oidc_id != oidc_id:
                    return JsonResponse(
                        {"error": "This email is bound to another account."}, status=409
                    )
                user.oidc_id = oidc_id
                user.save(update_fields=["oidc_id"])
            else:
                username, _ = parse_oidc_username(account.get("username"))
                user = User(
                    username=username or email,
                    email=email,
                    first_name=account.get("firstName", ""),
                    last_name=account.get("lastName", ""),
                    oidc_id=oidc_id,
                )
                user.set_unusable_password()
                user.save()

        if not user.is_active:
            return JsonResponse({"error": "This DAISY user is inactive."}, status=409)
        if contact:
            Access.objects.filter(contact=contact).update(contact=None, user=user)
            contact.oidc_id = None
            contact.save(update_fields=["oidc_id"])

    return JsonResponse({"user": serialize_user(user)})
