class BaseException(Exception):
    """
    All errors specific to to this library will be subclassed from BaseException.
    """

    pass


class BatchExecutionError(IOError, BaseException):
    pass


class InvalidValueError(ValueError, BaseException):
    pass


class NoFacebookRequestProvidedError(InvalidValueError):
    pass


class TooManyRequestsPerBatchError(InvalidValueError):
    pass
