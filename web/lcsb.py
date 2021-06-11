import json
import logging

from typing import Dict

from core.utils import DaisyLogger


logger = DaisyLogger(__name__)

def handle_rems_callback(request):
    logger.debug('Handling the data from REMS:')
    body_unicode = request.body.decode('utf-8')
    logger.debug(body_unicode)

    request_post_data = json.loads(body_unicode)
    
    user = request_post_data.get('user')
    application = request_post_data.get('application')
    resource = request_post_data.get('resource')
    email = request_post_data.get('email')
    
    logger.debug(user)
    logger.debug(application)
    logger.debug(resource)
    logger.debug(email)
    raise NotImplementedError("REMS endpoint is not fully implemented; but the received data has been saved to daisy.log")
    # TODO
    return True
