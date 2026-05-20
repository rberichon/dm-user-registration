from http import HTTPStatus


class ServiceError(Exception):
    status_code: int
    detail: str


class EmailConflict(ServiceError):
    status_code = HTTPStatus.CONFLICT
    detail = "This email address is already in use."


class UserNotFound(ServiceError):
    status_code = HTTPStatus.NOT_FOUND
    detail = "User not found."


class AlreadyActive(ServiceError):
    status_code = HTTPStatus.BAD_REQUEST
    detail = "This account is already active."


class InvalidCode(ServiceError):
    status_code = HTTPStatus.BAD_REQUEST
    detail = "Invalid code."


class ExpiredCode(ServiceError):
    status_code = HTTPStatus.BAD_REQUEST
    detail = "Expired code. A new code has been sent to your email account."
