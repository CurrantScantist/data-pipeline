class RemoteRepoNotFoundError(Exception):
    """
    Custom error for when a remote repository is not found on github.com
    """

    def __init__(self, message):
        self.message = message
        super().__init__(message)


class HTTPError(Exception):
    """
    Custom error for when a request returns an unexpected status code
    """

    def __init__(self, status_code):
        self.status_code = status_code
        self.message = f"Error with status code: {status_code}"
        super().__init__(self.message)


class InvalidArgumentError(Exception):
    """
    Custom error for when an argument to a function is not within an expected range
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)