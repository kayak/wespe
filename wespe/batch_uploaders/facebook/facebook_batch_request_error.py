import logging

from facebook_business.api import (
    FacebookRequest,
)
from facebook_business.exceptions import FacebookRequestError
from ..requests import (
    BaseRequestError,
)

logger = logging.getLogger(__name__)


class FacebookBatchRequestError(BaseRequestError):
    def __init__(self, request: FacebookRequest, request_error: FacebookRequestError):
        super().__init__(
            description=request_error.api_error_message(),
            # Generally 500 responses have no is_transient field in payload, even though they are transient
            # in nature.
            is_transient=request_error.api_transient_error() or request_error.http_status() == 500,
            data=request_error.body(),
        )

        self.request = request
        self.request_error = request_error

    def __repr__(self):
        return "FacebookRequestError:{}\nWhen using params: {}.".format(
            self.request_error, self.request.get_params()
        )
