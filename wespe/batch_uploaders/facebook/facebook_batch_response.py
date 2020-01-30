import logging

from facebook_business.api import (
    FacebookRequest,
    FacebookResponse,
)
from ..requests import (
    BaseResponse,
)

logger = logging.getLogger(__name__)


class FacebookBatchResponse(BaseResponse):
    def __init__(self, request: FacebookRequest, response: FacebookResponse):
        super().__init__(data=response.json())

        self.request = request
        self.response = response

    def __repr__(self):
        return "FacebookResponse:\n\n{}\n\nWhen using params: {}.".format(
            self.data, self.request.get_params()
        )
