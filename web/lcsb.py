from typing import Dict

from typing import Dict


def handle_rems_callback(request_post_data: Dict):
    user = request_post_data.POST.get('user')
    application = request_post_data.POST.get('application')
    resource = request_post_data.get('resource')
    email = request_post_data.get('email')
    raise NotImplemented()
    # TODO
    return True
