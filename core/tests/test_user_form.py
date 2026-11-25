import pytest

from core.forms.user import UserForm
from test.factories import UserFactory


def test_the_form_does_not_offer_is_active():
    """A login activates the row again, so the checkbox would promise a block it cannot hold."""
    assert "is_active" not in UserForm().fields


@pytest.mark.django_db
def test_editing_a_user_leaves_is_active_alone():
    user = UserFactory(username="person", email="person@example.org", is_active=False)

    form = UserForm(
        data={
            "first_name": "Person",
            "last_name": "Example",
            "email": "person@example.org",
            "groups": [],
        },
        instance=user,
    )

    assert form.is_valid(), form.errors
    form.save()
    user.refresh_from_db()
    assert not user.is_active
