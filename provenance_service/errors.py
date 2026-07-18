class ServiceError(Exception):
    status_code = 400
    code = "service_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ConflictError(ServiceError):
    status_code = 409
    code = "conflict"


class NotFoundError(ServiceError):
    status_code = 404
    code = "not_found"


class UnsafePathError(ServiceError):
    status_code = 422
    code = "unsafe_path"
