from io import StringIO

import pytest
from django.core.management import call_command

from test.factories import UserFactory


def run_command(*args):
    output = StringIO()
    call_command("set_unusable_passwords", *args, stdout=output)
    return output.getvalue().splitlines()


@pytest.mark.django_db
def test_command_makes_the_password_of_a_keycloak_user_unusable():
    user = UserFactory(oidc_id="keycloak-id")

    output = run_command()

    user.refresh_from_db()
    assert not user.has_usable_password()
    assert output == ["Set an unusable password for 1 user(s)."]


@pytest.mark.django_db
def test_command_keeps_the_password_of_a_user_without_an_oidc_id():
    user = UserFactory(oidc_id=None)

    output = run_command()

    user.refresh_from_db()
    assert user.has_usable_password()
    assert output == ["Set an unusable password for 0 user(s)."]


@pytest.mark.django_db
def test_command_keeps_the_password_of_a_superuser():
    superuser = UserFactory(oidc_id="keycloak-id", is_superuser=True)

    output = run_command()

    superuser.refresh_from_db()
    assert superuser.has_usable_password()
    assert output == ["Set an unusable password for 0 user(s)."]


@pytest.mark.django_db
def test_command_ignores_a_user_that_has_no_usable_password():
    user = UserFactory(oidc_id="keycloak-id")
    user.set_unusable_password()
    user.save(update_fields=["password"])

    output = run_command()

    assert output == ["Set an unusable password for 0 user(s)."]


@pytest.mark.django_db
def test_command_dry_run_reports_without_saving():
    user = UserFactory(oidc_id="keycloak-id")

    output = run_command("--dry-run")

    user.refresh_from_db()
    assert user.has_usable_password()
    assert output == ["Would set an unusable password for 1 user(s)."]
