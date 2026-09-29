from test.factories import ContactFactory, UserFactory


def test_user_email_is_lowercase_on_save():
    user = UserFactory.create(email="User@Example.org")

    assert user.email == "user@example.org"


def test_contact_email_is_lowercase_on_save():
    contact = ContactFactory.create(email="Contact@Example.org")

    assert contact.email == "contact@example.org"
