class BaseResponse:
    def __init__(self, data: dict):
        self._data = data

    @property
    def data(self) -> dict:
        """
        Returns the entire payload response.

        :return: a dictionary.
        """
        return self._data

    def __eq__(self, other):
        return self._data == other._data

    def __str__(self):
        return self.data


class BaseRequestError:
    def __init__(self, description: str, is_transient: bool, data: dict):
        self._is_transient = is_transient
        self._description = description
        self._data = data

    @property
    def is_transient(self) -> bool:
        """
        Returns True when the error is likely to be caused by a temporary issue (e.g. network issue). This should
        be used as a way to identify which requests can be retried without further modifications.

        :return: a boolean.
        """
        return self._is_transient

    @property
    def description(self) -> str:
        """
        Returns an error description.

        :return: a string.
        """
        return self._description

    @property
    def data(self) -> dict:
        """
        Returns the entire error payload response.

        :return: a dictionary.
        """
        return self._data

    def __eq__(self, other):
        return self._data == other._data

    def __str__(self):
        return self.data
