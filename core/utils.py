"""
Module that regroup some utilities.
"""
import logging


class DaisyLogger:
    def __init__(self, logger_name):
        self.logger = logging.getLogger('daisy.%s' % logger_name)
        self.logger.setLevel(logging.NOTSET)

    def __getattr__(self, attr):
        """
        Calling this will return the logger function
        and will wraps it with function that will take all args & kwargs of it to
        construct a nice message to log.
        """
        fn = getattr(self.logger, attr)
        def wrap(*args, **kwargs):
            message = ' '.join((str(a) for a in args))
            message += ' '
            message += ' '.join(('%s=%s' % (str(k), str(v)) for k, v in kwargs.items()))
            return fn(message)
        return wrap
