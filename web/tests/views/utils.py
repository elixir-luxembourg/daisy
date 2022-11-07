from django.test.client import Client
import logging

logger = logging.getLogger(__name__)


client = Client()
requests_methods = {
    "GET": client.get,
    "POST": client.post,
    "DELETE": client.delete,
    "HEAD": client.head,
}


def check_response_status(url, user, permissions, obj=None, method="GET"):
    client.login(username=user.username, password='test-user')
    try:
        response = requests_methods[method](url)
        print(response)
        if obj is not None:
            if isinstance(permissions, list):
                has_perm = all([user.has_permission_on_object(perm, obj) for perm in permissions])
            else:
                has_perm = user.has_permission_on_object(permissions, obj)
            if has_perm:
                assert response.status_code != 403
            else:
                assert response.status_code == 403

        else:
            raise ValueError("An object must be given if checking permissions at object scope")

    except KeyError:
        raise ValueError(f"Received unexpected request method {method}")

    finally:
        client.logout()
