from django.test.client import Client

client = Client()
requests_methods = {
    "GET": client.get,
    "POST": client.post,
    "DELETE": client.delete,
    "HEAD": client.head,
}


def check_response_status(url, user, perm, obj=None, level="class", method="GET"):
    client.login(username=user.username, password=user.password)

    try:
        response = requests_methods[method](url)
        if level == "class":
            if user.has_perm(perm):
                assert response.status_code != 403
            else:
                assert response.status_code == 403
        if level == "obj" and obj is not None:
            if user.has_permission_on_object(perm, obj):
                assert response.status_code != 403
            else:
                assert response.status_code == 403

    except KeyError:
        raise ValueError(f"Received unexpected request method {method}")

    finally:
        client.logout()
