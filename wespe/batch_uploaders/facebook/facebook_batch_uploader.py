import logging
from typing import (
    Generator,
    List,
    Tuple,
    Union,
)

from facebook_business.api import (
    FacebookAdsApi,
    FacebookRequest,
)
from tenacity import (
    RetryError,
)

from wespe.exceptions import (
    BatchExecutionError,
    InvalidValueError,
)
from .facebook_batch import FacebookBatch
from .facebook_batch_request_error import FacebookBatchRequestError
from .facebook_batch_response import FacebookBatchResponse

logger = logging.getLogger(__name__)


class FacebookBatchUploader:
    def __init__(self, requests: List[FacebookRequest], api: FacebookAdsApi = None):
        self.api = api or FacebookAdsApi.get_default_api()

        self._requests = requests
        self._batches = []

    def execute(self, chunk_size: int = 50) -> 'FacebookBatchUploader':
        """
        Execute all requests in batches of chunk_size amount.

        :param chunk_size:
            (Optional) The amount of requests per chunk. Keep in mind this value should be between 1 and 50, otherwise
            an exception will be raised. Defaults to 50.
        :raises: BatchExecutionError: when one or more requests failed.
        :return: self.
        """
        num_requests = len(self.requests)

        if chunk_size < 1 or chunk_size > 50:
            raise InvalidValueError("Chunk size must be between 1 and 50")

        for i in range(0, num_requests, chunk_size):
            batch = FacebookBatch(self.requests[i : i + chunk_size], api=self.api)
            self._batches.append(batch)

            try:
                batch.execute()
            except RetryError:
                pass

        errors = list(self.errors)

        if any(errors):
            exception_msg = "{} requests failed out of {}\n\n{}".format(
                len(errors), num_requests, errors
            )
            raise BatchExecutionError(exception_msg)

        return self

    @property
    def requests(self) -> List[FacebookRequest]:
        """
        Returns all FacebookRequest instances.

        :return: a list of FacebookRequest instances.
        """
        return self._requests

    @property
    def responses(self) -> Generator[Union[None, FacebookBatchResponse], None, None]:
        """
        Returns the responses for the executed FacebookRequest instances. The amount and order of elements will
        be the same as of FacebookRequest instances. FacebookRequest with errors will have None as their value
        in the respective index.

        :return: a list of FacebookBatchResponse instance and/or None.
        """
        for batch in self._batches:
            for response in batch.responses:
                yield response

    @property
    def errors(self) -> Generator[Union[None, FacebookBatchRequestError], None, None]:
        """
        Returns the errors for the executed FacebookRequest instances. The amount and order of elements will
        be the same as of FacebookRequest instances. FacebookRequest without errors will have None as their value
        in the respective index.

        :return: a generator of FacebookBatchRequestError instances and/or None.
        """
        for batch in self._batches:
            for response in batch.errors:
                yield response

    @property
    def items(
        self,
    ) -> Generator[
        Tuple[
            FacebookRequest,
            Union[None, FacebookBatchResponse],
            Union[None, FacebookBatchRequestError],
        ],
        None,
        None,
    ]:
        """
        Returns a list of tuples shaped as FacebookRequest instance and its respective response/error.

        :return: a list of tuples shaped as (request, FacebookBatchResponse or None, FacebookBatchRequestError
                 instance or None).
        """
        for request, response, error in zip(self.requests, self.responses, self.errors):
            yield request, response, error
