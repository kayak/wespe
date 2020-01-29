# coding: utf8
from itertools import chain
from unittest import TestCase
from unittest.mock import (
    ANY,
    MagicMock,
    PropertyMock,
    call,
    patch,
)

from facebook_business import FacebookAdsApi
from tenacity import RetryError

from wespe.batch_uploaders import FacebookBatchUploader
from wespe.batch_uploaders.facebook import (
    FacebookBatch,
    FacebookBatchRequestError,
    FacebookBatchResponse,
)
from wespe.exceptions import (
    BatchExecutionError,
    InvalidValueError,
    NoFacebookRequestProvidedError,
    TooManyRequestsPerBatchError,
)

# We don't want to lose time waiting during tests
FacebookBatch.WAIT_EXPONENTIAL_MULTIPLIER = 0
FacebookBatch.WAIT_EXPONENTIAL_MIN_IN_SECONDS = 0
FacebookBatch.WAIT_EXPONENTIAL_MAX_IN_SECONDS = 0


class TestFacebookBatch(TestCase):
    def setUp(self):
        self.requests = [MagicMock()] * 10
        self.api = MagicMock()
        self.batch = FacebookBatch(requests=self.requests, api=self.api)

    def test_constructor_raises_NoFacebookRequestProvidedError_when_request_list_is_empty(
        self,
    ):
        with self.assertRaises(NoFacebookRequestProvidedError):
            FacebookBatch(requests=[], api=self.api)

    def test_constructor_does_not_raise_TooManyRequestsPerBatchError_when_exactly_50_requests_were_provided(
        self,
    ):
        FacebookBatch(requests=[MagicMock()] * 50, api=self.api)

    def test_constructor_raises_TooManyRequestsPerBatchError_when_more_than_50_requests_were_provided(
        self,
    ):
        with self.assertRaises(TooManyRequestsPerBatchError):
            FacebookBatch(requests=[MagicMock()] * 51, api=self.api)

    def test_constructor_initialiazes_batch_as_None(self):
        self.assertIsNone(self.batch._batch)

    def test_constructor_initialiazes_a_list_of_None_for_errors_prior_to_execution(
        self,
    ):
        self.assertListEqual(self.batch._errors, [None] * len(self.requests))

    def test_constructor_initialiazes_a_list_of_None_for_responses_prior_to_execution(
        self,
    ):
        self.assertListEqual(self.batch._responses, [None] * len(self.requests))

    def test_WAIT_EXPONENTIAL_MULTIPLIER_is_0_for_this_test_case(self):
        # This ensures our tests are never initiliazed with a waiting time between retries
        self.assertEqual(self.batch.WAIT_EXPONENTIAL_MULTIPLIER, 0)

    def test_WAIT_EXPONENTIAL_MIN_IN_SECONDS_is_0_for_this_test_case(self):
        # This ensures our tests are never initiliazed with a waiting time between retries
        self.assertEqual(self.batch.WAIT_EXPONENTIAL_MIN_IN_SECONDS, 0)

    def test_WAIT_EXPONENTIAL_MAX_IN_SECONDS_is_0_for_this_test_case(self):
        # This ensures our tests are never initiliazed with a waiting time between retries
        self.assertEqual(self.batch.WAIT_EXPONENTIAL_MAX_IN_SECONDS, 0)

    def test_default_failure_callback_sets_the_error_in_error_list(self):
        request_index = 3
        response = MagicMock()
        self.batch._default_failure_callback(
            response=response, request_index=request_index
        )

        self.assertEqual(
            self.batch._errors[request_index],
            FacebookBatchRequestError(
                request=response.request(), request_error=response.error()
            ),
        )

    def test_default_success_callback_sets_the_response_in_response_list(self):
        request_index = 3
        response = MagicMock()
        self.batch._default_success_callback(
            response=response, request_index=request_index
        )

        self.assertEqual(
            self.batch._responses[request_index],
            FacebookBatchResponse(request=response.request(), response=response),
        )

    @patch.object(FacebookBatch, "_initialize_execution_retrial_conditions")
    def test_execute_calls_initialize_execution_retrial_conditions(
        self, mock_initialize_execution_retrial_conditions
    ):
        self.batch.execute()
        mock_initialize_execution_retrial_conditions.assert_called_once_with()

    def test_execute_calls_add_request_on_batch_as_many_times_as_requests_exist(self):
        self.batch.execute()
        self.batch._batch.add_request.assert_has_calls(
            [
                call(request, success=ANY, failure=ANY)
                for request_index, request in enumerate(self.requests)
            ]
        )

    def test_execute_calls_add_request_on_batch_ignores_requests_that_have_a_response_set_already(
        self,
    ):
        for request_index, _ in enumerate(self.requests[:-1]):
            self.batch._responses[request_index] = MagicMock()

        self.batch.execute()
        self.batch._batch.add_request.assert_has_calls(
            [call(self.requests[-1], success=ANY, failure=ANY)]
        )

    @patch(
        "wespe.batch_uploaders.facebook.should_retry_facebook_batch", return_value=True
    )
    def test_execute_raises_RetryError_when_should_retry_is_True_for_all_attempts(
        self, mock_should_retry
    ):
        with self.assertRaises(RetryError):
            self.batch.execute()

    @patch(
        "wespe.batch_uploaders.facebook.should_retry_facebook_batch", return_value=True
    )
    def test_execute_retries_for_max_attempts_when_should_retry_is_True_for_all_of_them(
        self, mock_should_retry
    ):
        try:
            self.batch.execute()
        except RetryError:
            pass

        self.assertEqual(
            self.batch.execute.retry.statistics.get("attempt_number"),
            FacebookBatch.MAX_ATTEMPTS,
        )

    @patch(
        "wespe.batch_uploaders.facebook.should_retry_facebook_batch", return_value=False
    )
    def test_execute_does_not_retry_when_should_retry_is_False(self, mock_should_retry):
        self.batch.execute()
        self.assertEqual(self.batch.execute.retry.statistics.get("attempt_number"), 1)

    def test_initialize_execution_retrial_conditions_sets_the_right_retrial_arguments_for_execution(
        self,
    ):
        self.batch.MAX_ATTEMPTS = MagicMock()
        self.batch.WAIT_EXPONENTIAL_MULTIPLIER = MagicMock()
        self.batch.WAIT_EXPONENTIAL_MIN_IN_SECONDS = MagicMock()
        self.batch.WAIT_EXPONENTIAL_MAX_IN_SECONDS = MagicMock()

        self.batch._initialize_execution_retrial_conditions()

        retry_settings = self.batch.execute.retry

        with self.subTest("sets the maximum number of attempts"):
            self.assertEqual(
                retry_settings.stop.max_attempt_number, self.batch.MAX_ATTEMPTS
            )

        with self.subTest("sets the exponential multiplier"):
            self.assertEqual(
                retry_settings.wait.multiplier, self.batch.WAIT_EXPONENTIAL_MULTIPLIER
            )

        with self.subTest("sets the exponential minimum threshold"):
            self.assertEqual(
                retry_settings.wait.min, self.batch.WAIT_EXPONENTIAL_MIN_IN_SECONDS
            )

        with self.subTest("sets the exponential maximum threshold"):
            self.assertEqual(
                retry_settings.wait.max, self.batch.WAIT_EXPONENTIAL_MAX_IN_SECONDS
            )


class TestFacebookBatchUploader(TestCase):
    def setUp(self):
        self.requests = [MagicMock()] * 49
        self.api = MagicMock()
        self.batch_uploader = FacebookBatchUploader(
            requests=self.requests, api=self.api
        )

    @patch.object(FacebookAdsApi, "get_default_api")
    def test_constructor_will_try_to_use_default_api_if_None_is_provided(
        self, mock_get_default_api
    ):
        batch_uploader = FacebookBatchUploader(requests=self.requests)
        self.assertEqual(batch_uploader.api, mock_get_default_api.return_value)

    def test_constructor_will_try_to_use_the_provided_api_if_provided(self):
        self.assertEqual(self.batch_uploader.api, self.api)

    def test_execute_raises_InvalidValueError_when_chunk_size_is_more_than_50(self):
        with self.assertRaises(InvalidValueError):
            self.batch_uploader.execute(chunk_size=51)

    def test_execute_raises_InvalidValueError_when_chunk_size_is_less_than_1(self):
        with self.assertRaises(InvalidValueError):
            self.batch_uploader.execute(chunk_size=0)

    @patch.object(FacebookBatch, "execute")
    def test_execute_calls_execute_in_FacebookBatch(self, mock_execute):
        self.batch_uploader.execute()
        mock_execute.assert_called_once_with()

    @patch.object(FacebookBatch, "execute", side_effect=RetryError(last_attempt=1))
    def test_execute_ignores_RetryError_exceptions_raised_by_individual_batches(
        self, mock_execute
    ):
        self.batch_uploader.execute()

    @patch.object(FacebookBatch, "execute")
    def test_execute_generates_a_single_batch_for_50_requests_when_using_default_chunk_size(
        self, mock_execute
    ):
        requests = [MagicMock()] * 50
        batch_uploader = FacebookBatchUploader(requests=requests, api=self.api)
        batch_uploader.execute()
        self.assertEqual(len(batch_uploader._batches), round(len(self.requests) / 50))

    @patch.object(FacebookBatch, "execute")
    def test_execute_generates_as_many_batches_as_the_rounded_number_of_requests_per_chunk_size(
        self, mock_execute
    ):
        chunk_size = 5
        self.batch_uploader.execute(chunk_size=chunk_size)
        self.assertEqual(
            len(self.batch_uploader._batches), round(len(self.requests) / chunk_size)
        )

    @patch.object(FacebookBatchUploader, "errors", new_callable=PropertyMock)
    @patch.object(FacebookBatch, "execute")
    def test_execute_raises_BatchExecutionError_when_errors_exist(
        self, mock_execute, mock_errors
    ):
        mock_errors.return_value = [MagicMock()] * len(self.requests)
        with self.assertRaises(BatchExecutionError):
            self.batch_uploader.execute()

    def test_requests_returns_the_same_requests_that_were_provided_to_the_constructor(
        self,
    ):
        self.assertListEqual(self.batch_uploader.requests, self.requests)

    def test_responses_returns_a_list_of_None_when_fetched_before_execution(self):
        self.assertListEqual(list(self.batch_uploader.responses), [])

    def test_errors_returns_an_empty_list_when_fetched_before_execution(self):
        self.assertListEqual(list(self.batch_uploader.errors), [])

    def test_items_returns_an_empty_list_when_fetched_before_execution(self):
        self.assertListEqual(list(self.batch_uploader.items), [])

    def test_errors_returns_errors_when_a_batch_has_any(self):
        facebook_batch = MagicMock()
        facebook_batch._errors = [MagicMock()] * len(self.requests)
        self.batch_uploader._batches = [facebook_batch]

        self.assertListEqual(list(self.batch_uploader.errors), facebook_batch._errors)

    def test_responses_returns_responses_when_a_batch_has_any(self):
        facebook_batch = MagicMock()
        facebook_batch._responses = [MagicMock()] * len(self.requests)
        self.batch_uploader._batches = [facebook_batch]

        self.assertListEqual(
            list(self.batch_uploader.responses), facebook_batch._responses
        )

    def test_items_returns_a_triple_with_requests_and_responses_and_errors(self):
        facebook_batch = MagicMock()
        facebook_batch._responses = [MagicMock()] * len(self.requests)
        facebook_batch._errors = [MagicMock()] * len(self.requests)
        self.batch_uploader._batches = [facebook_batch]

        self.assertListEqual(
            list(self.batch_uploader.items),
            list(
                zip(
                    self.batch_uploader.requests,
                    self.batch_uploader.responses,
                    self.batch_uploader.errors,
                )
            ),
        )

    def test_errors_returns_all_errors_when_multiple_batches_exist(self):
        facebook_batch_1 = MagicMock()
        facebook_batch_1._errors = [MagicMock()] * (len(self.requests) - 1)
        facebook_batch_2 = MagicMock()
        facebook_batch_2._errors = [MagicMock()]
        self.batch_uploader._batches = [facebook_batch_1, facebook_batch_2]

        self.assertListEqual(
            list(self.batch_uploader.errors),
            list(chain(facebook_batch_1._errors, facebook_batch_2._errors)),
        )

    def test_responses_returns_all_responses_when_multiple_batches_exist(self):
        facebook_batch_1 = MagicMock()
        facebook_batch_1._responses = [MagicMock()] * (len(self.requests) - 1)
        facebook_batch_2 = MagicMock()
        facebook_batch_2._responses = [MagicMock()]
        self.batch_uploader._batches = [facebook_batch_1, facebook_batch_2]

        self.assertListEqual(
            list(self.batch_uploader.responses),
            list(chain(facebook_batch_1._responses, facebook_batch_2._responses)),
        )
