class StandardResponse:
    """
    Standard response format for API responses.
    """
    message: str
    data: dict = None


class ErrorResponse:
    """
    Standard error response format for API errors.
    """
    error: str
    details: dict = None
