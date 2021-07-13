import pytest

@pytest.fixture
def client_user_normal(client, user_normal):
    client.login(username=user_normal.username, password=user_normal.password)
    return client

@pytest.fixture
def client_user_vip(client, user_vip):
    client.login(username=user_vip.username, password=user_vip.password)
    return client

@pytest.fixture
def client_user_admin(client, user_admin):
    client.login(username=user_admin.username, password="password") #TODO: the password is hardcoded since user_admin.password returns just hash
    return client