import logging
from functools import partial
from typing import (
    Generator,
    List,
    Tuple,
    Union,
)

from facebook_business.api import (
    FacebookAdsApi,
    FacebookRequest,
    FacebookResponse,
)
from facebook_business.exceptions import FacebookRequestError
from tenacity import (
    RetryError,
    retry,
    retry_if_result,
    stop_after_attempt,
    wait_exponential,
)

from wespe.exceptions import (
    BatchExecutionError,
    InvalidValueError,
    NoFacebookRequestProvidedError,
    TooManyRequestsPerBatchError,
)
from .requests import (
    BaseRequestError,
    BaseResponse,
)
from .retries import should_retry_facebook_batch

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


class FacebookBatch:
    # Batch retrying parameters for transient errors
    MAX_ATTEMPTS = 5  # The max number of attempts a batch execution should retry
    WAIT_EXPONENTIAL_MULTIPLIER = 1  # The exponential multiplier
    WAIT_EXPONENTIAL_MIN_IN_SECONDS = (
        1  # The minimum waiting time derived from the exponential multiplier
    )
    WAIT_EXPONENTIAL_MAX_IN_SECONDS = (
        10  # The maximum waiting time derived from the exponential multiplier
    )

    def __init__(self, requests: List[FacebookRequest], api: FacebookAdsApi):
        if not requests:
            raise NoFacebookRequestProvidedError(
                "At least one facebook request must be provided"
            )

        num_requests = len(requests)

        if num_requests > 50:
            # See more on https://developers.facebook.com/docs/graph-api/making-multiple-requests
            raise TooManyRequestsPerBatchError(
                "A maximum of 50 requests per batch is supported"
            )

        self._api = api
        self._batch = None
        self._requests = requests
        self._responses = [None] * num_requests
        self._errors = [None] * num_requests

    @property
    def requests(self) -> List[FacebookRequest]:
        """
        Returns all FacebookRequest instances.

        :return: a list of FacebookRequest instances.
        """
        return self._requests

    @property
    def responses(self) -> List[Union[None, FacebookBatchResponse]]:
        """
        Returns the responses for the executed FacebookRequest instances. The amount and order of elements will
        be the same as of FacebookRequest instances. FacebookRequest with errors will have None as their value
        in the respective index.

        :return: a list of FacebookBatchResponse instance and/or None.
        """
        return self._responses

    @property
    def errors(self) -> List[Union[None, FacebookBatchRequestError]]:
        """
        Returns the errors for the executed FacebookRequest instances. The amount and order of elements will
        be the same as of FacebookRequest instances. FacebookRequest without errors will have None as their value
        in the respective index.

        :return: a list of FacebookBatchRequestError instances and/or None.
        """
        return self._errors

    @retry()
    def execute(self) -> 'FacebookBatch':
        """
        Execute all requests. This method will be retried for any failed transient errors. For such we employ an
        exponential backoff approach.

        The exponential back off defaults to wait 2^x * 1 seconds between each retry, up to 10 seconds, then 10
        seconds afterwards for a maximum of 5 attempts. Those values can be tweaked by playing with MAX_ATTEMPTS,
        WAIT_EXPONENTIAL_MULTIPLIER, WAIT_EXPONENTIAL_MIN_IN_SECONDS, and WAIT_EXPONENTIAL_MAX_IN_SECONDS static
        variables.

        :raises: RetryError: when retries failed for MAX_ATTEMPTS.
        :return: self.
        """
        # We set the retry settings during runtime, so don't worry about this method never finishing
        self._initialize_execution_retrial_conditions()

        self._batch = self._api.new_batch()

        for request_index, request in enumerate(self._requests):
            response = self.responses[request_index]
            error = self.errors[request_index]

            if (response is None and error is None) or (error and error.is_transient):
                self._batch.add_request(
                    request,
                    success=partial(
                        self._default_success_callback, request_index=request_index
                    ),
                    failure=partial(
                        self._default_failure_callback, request_index=request_index
                    ),
                )

        self._batch.execute()

        return self

    def _initialize_execution_retrial_conditions(self):
        """
        This will re-initialize, during runtime, the arguments of the retry decorator wrapping the execute method
        with class-level retry settings. Those are MAX_ATTEMPTS, WAIT_EXPONENTIAL_MULTIPLIER,
        WAIT_EXPONENTIAL_MIN_IN_SECONDS, and WAIT_EXPONENTIAL_MAX_IN_SECONDS.

        :return:
        """
        retry_settings = self.execute.retry
        retry_settings.retry = retry_if_result(should_retry_facebook_batch)
        retry_settings.stop = stop_after_attempt(self.MAX_ATTEMPTS)
        retry_settings.wait = wait_exponential(
            multiplier=self.WAIT_EXPONENTIAL_MULTIPLIER,
            min=self.WAIT_EXPONENTIAL_MIN_IN_SECONDS,
            max=self.WAIT_EXPONENTIAL_MAX_IN_SECONDS,
        )

    def _default_failure_callback(
        self, response: FacebookResponse, request_index: int, object_id: int = None
    ):
        """
        A method that can be used to raise exceptions when the batch object is used for bulk operations.
        This callback raises a custom FacebookAPIError.

        This is intended to be used as a default callback to fallback to in case a user does not provide one.

        :param response: Facebook response object.
        :param request_index: The index of the request in the whole batch.
        :param object_id: (Optional) The ID of the object being updated.
        """
        request = self._requests[request_index]
        batch__error = FacebookBatchRequestError(
            request=request, request_error=response.error()
        )
        self._responses[request_index] = None
        self._errors[request_index] = batch__error

        error_msg = ["#{} -".format(request_index)]

        if object_id:
            error_msg.append("Error updating object with id [{}].".format(object_id))

        error_msg.append(str(batch__error))

        logger.error(" ".join(error_msg))

    def _default_success_callback(
        self, response: FacebookResponse, request_index: int, object_id: int = None
    ):
        """
        A method that can be used to log when the batch object has completed successfully.

        This is intended to be used as a default callback to fallback to in case a user does not provide one.

        :param response: Facebook response object.
        :param request_index: The index of the request in the whole batch.
        :param object_id: The ID of the object being updated.
        """
        request = self._requests[request_index]
        batch_response = FacebookBatchResponse(request=request, response=response)
        self._responses[request_index] = batch_response
        self._errors[request_index] = None

        if object_id is None:
            object_id = response.json().get("id")

        logger.debug(
            "Request #{}: Object with id [{}] updated successfully!".format(
                request_index, str(object_id)
            )
        )


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
