from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from core.models.access import StatusChoices
from notification.models import Notification, NotificationVerb
from test.factories import (
    AccessFactory,
    DataDeclarationFactory,
    DatasetFactory,
    DataStewardGroup,
    UserFactory,
    VIPGroup,
)


def template_names(response):
    return [t.name for t in response.templates]


@pytest.mark.django_db
def test_dashboard_as_data_steward(client):
    user = UserFactory(groups=[DataStewardGroup()])
    client.force_login(user)

    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert "dashboard.html" in template_names(response)
    # Stewards manage accesses org-wide, so the "needs attention" strip shows.
    assert response.context["can_manage_accesses"] is True
    assert response.context["show_attention"] is True


@pytest.mark.django_db
def test_dashboard_as_normal_user(client):
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert "dashboard.html" in template_names(response)
    # A standard user cannot manage accesses; the attention strip is hidden.
    assert response.context["can_manage_accesses"] is False


@pytest.mark.django_db
def test_dashboard_vip_scoped_attention(client):
    user = UserFactory(groups=[VIPGroup()])
    client.force_login(user)
    today = timezone.localdate()

    dataset = DatasetFactory(local_custodians=[user])
    AccessFactory(
        dataset=dataset,
        status=StatusChoices.active,
        grant_expires_on=today + timedelta(days=10),
    )
    DataDeclarationFactory(
        dataset=dataset, end_of_storage_duration=today - timedelta(days=1)
    )

    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    # VIP manages accesses on custodied data, but is not a steward.
    assert response.context["can_manage_accesses"] is True
    assert response.context["accesses_expiring_count"] == 1
    assert response.context["retention_reached_count"] == 1


@pytest.mark.django_db
def test_dashboard_shows_deadlines(client):
    user = UserFactory()
    client.force_login(user)
    Notification.objects.create(
        recipient=user,
        verb=NotificationVerb.expire,
        content_object=user,
        on=timezone.now(),
    )

    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert response.context["deadlines_count"] == 1
    assert response.context["show_attention"] is True


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    response = client.get(reverse("dashboard"))

    assert response.status_code == 302
    assert reverse("login") in response.url
