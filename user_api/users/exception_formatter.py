from drf_standardized_errors.formatter import ExceptionFormatter
from drf_standardized_errors.types import ErrorResponse


class CustomExceptionFormatter(ExceptionFormatter):
    def format_error_response(self, error_response: ErrorResponse):
        error = error_response.errors[0]

        return {
            "type": error_response.type,
            "errors": [
                {
                    "code": error.code,
                    "message": error.detail,
                    "field": error.attr,
                },
            ],
        }
