from django.test.client import Client
from django.db.models import Model
from django.contrib.auth.models import Group

from core.models.user import User
from core.constants import Groups

from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


client = Client()
requests_methods = {
    "GET": client.get,
    "POST": client.post,
    "DELETE": client.delete,
    "HEAD": client.head,
}


def check_permissions(user: User, permissions: List[str], obj: Optional[Model] = None) -> bool:
    if obj is not None:
        has_perm = all([user.has_permission_on_object(perm, obj) for perm in permissions])
    else:
        has_perm = all([user.has_perm(perm)] for perm in permissions)

    return has_perm


def check_response_status(url: str, user: User, permissions: List[str], obj: Optional[Model] = None, method: str = "GET") -> None:
    assert client.login(username=user.username, password='test-user'), "Login failed"
    try:
        response = requests_methods[method](url)
        has_perm = check_permissions(user, permissions, obj) if permissions else True
        if has_perm:
            assert response.status_code != 403
        else:
            assert response.status_code == 403

    except KeyError as e:
        if method not in requests_methods:
            raise ValueError(f"Received unexpected request method {method}")
        else:
            raise e

    finally:
        client.logout()


def check_datasteward_restricted_url(url, user):

    assert client.login(username=user.username, password='test-user'), "Login Failed"
    try:
        response = client.get(url)
        if user.is_part_of(Group.objects.get(name=Groups.DATA_STEWARD.value)):
            assert response.status_code != 403
        else:
            assert response.status_code == 403
    finally:
        client.logout()