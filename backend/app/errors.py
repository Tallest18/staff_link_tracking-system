from flask import jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Raise this from any route to send the standard error response."""

    def __init__(self, status, code, message):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def invalid(message):
    return ApiError(400, "invalid_input", message)


def not_found(message):
    return ApiError(404, "not_found", message)


def _error_response(status, code, message):
    return jsonify(error={"code": code, "message": message}), status


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return _error_response(error.status, error.code, error.message)

    # Flask's own errors, such as an unknown URL, get the same JSON shape.
    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        code = error.name.lower().replace(" ", "_")
        return _error_response(error.code, code, error.description)
