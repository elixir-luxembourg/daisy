import pytest

@pytest.fixture
def client_user_normal(client, user_normal):
    client.login(username=user_normal.username, password=user_normal.password)
    return client

@pytest.fixture
def client_user_vip(client, user_vip):
    client.login(username=user_vip.username, password=user_vip.password)
    return client