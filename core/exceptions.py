class DaisyError(Exception):
    """Base error class for the module."""

    default_message = "Unspecified DAISY error"

    def __init__(self, msg=None):
        self._msg = msg or self.default_message
        super().__init__()

    def __str__(self):
        msg = self._msg.format(**self.__dict__)
        return msg

    def __repr__(self):
        msg = self._msg.format(**self.__dict__)
        return "{}({!r})".format(self.__class__.__name__, msg)




class DatasetImportError(DaisyError):
    """Error when importing dataset into daisy."""

    default_message = "Error when importing dataset:' {data}'"

    def __init__(self, data, msg=None):
        self.data = data
        super().__init__(msg=msg)



class FixtureImportError(DaisyError):
    """Error when importing initial definition data into daisy."""

    default_message = "Error when importing fixtures:' {data}'"

    def __init__(self, data, msg=None):
        self.data = data
        super().__init__(msg=msg)


class JSONSchemaValidationError(DaisyError):
    """Error when validating data to be imported."""

    default_message = "Error when validating data against JSON schema:' {data}'"

    def __init__(self, data, msg=None):
        self.data = data
        super().__init__(msg=msg)