from pydantic import ValidationError


class AppError(Exception):
    message = "Application error."

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(AppError): ...
class ConflictError(AppError): ...
class ForbiddenError(AppError): ...
class ExternalServiceError(AppError): ...
class UnauthorizedError(AppError): ...


class UserNotFound(NotFoundError):
    message = "User not found."

class NotificationNotFound(NotFoundError):
    message = "Notification not found."

class UsernameAlreadyExists(ConflictError):
    message = "Username already exists."

class NotificationAlreadyExists(ConflictError):
    message = "Notification already exists."

class EmailAlreadyExists(ConflictError):
    message = "Email already exists."

class UserAlreadyExists(ConflictError):
    message = "Username or email already exists."

class NotAuthorized(ForbiddenError):
    message = "Not authorized to perform this action."

class InvalidCredentials(UnauthorizedError):
    message = "Incorrect username or password."

class NotAuthenticated(UnauthorizedError):
    message = "Could not validate credentials."

class InvalidChannelData(ValidationError):
    message = "Invalid channel data."
    message = "Could not validate credentials."

class SmsGatewayUnavailable(ExternalServiceError):
    message = "SMS gateway unavailable."