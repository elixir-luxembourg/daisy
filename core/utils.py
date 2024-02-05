"""
Module that regroup some utilities.
"""
import logging

from django.conf import settings
from django.utils.module_loading import import_string


class DaisyLogger:
    def __init__(self, logger_name):
        self.logger = logging.getLogger("daisy.%s" % logger_name)
        self.logger.setLevel(logging.NOTSET)

    def __getattr__(self, attr):
        """
        Calling this will return the logger function
        and will wraps it with function that will take all args & kwargs of it to
        construct a nice message to log.
        """
        fn = getattr(self.logger, attr)

        def wrap(*args, **kwargs):
            message = " ".join((str(a) for a in args))
            message += " "
            message += " ".join(("%s=%s" % (str(k), str(v)) for k, v in kwargs.items()))
            return fn(message)

        return wrap


class BootstrapChecker:
    """
    This is a small helper class to find any problems with missing values
    in Django configuration.
    """

    def __init__(self) -> None:
        pass

    def _check_idservice(self):
        # TODO: check ID service endpoint connectivity
        # i.e.: make http GET request

        # idservice_endpoint = getattr(settings, "IDSERVICE_ENDPOINT", None)

        # Checks if the function can be importable
        idservice_function = getattr(settings, "IDSERVICE_FUNCTION", None)
        import_string(idservice_function)

    def run(self):
        self._check_idservice()
