from typing import Any, Dict, Optional
from fastapi import status
from backend.app.core.exceptions import CPQException, UnauthorizedError

class AuthenticationError(UnauthorizedError):
    """
    Base exception for all authentication failure cases.
    """
    def __init__(self, detail: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, details=details)

class InvalidTokenError(AuthenticationError):
    """
    Raised when a token (JWT, verification, reset, etc.) is invalid, malformed, or signature checks fail.
    """
    def __init__(self, detail: str = "Invalid token", details: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, details=details)
        self.error_code = "INVALID_TOKEN"

class TokenExpiredError(AuthenticationError):
    """
    Raised when a token (JWT, session, verification, reset) is expired.
    """
    def __init__(self, detail: str = "Token has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, details=details)
        self.error_code = "TOKEN_EXPIRED"

class AccountLockedError(AuthenticationError):
    """
    Raised when a user account is locked due to too many failed login attempts.
    """
    def __init__(self, detail: str = "Account is locked", details: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, details=details)
        self.error_code = "ACCOUNT_LOCKED"
        self.status_code = status.HTTP_403_FORBIDDEN

class InactiveAccountError(AuthenticationError):
    """
    Raised when a user tries to authenticate with an inactive account.
    """
    def __init__(self, detail: str = "Account is inactive", details: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, details=details)
        self.error_code = "ACCOUNT_INACTIVE"
        self.status_code = status.HTTP_403_FORBIDDEN

class InsufficientPermissionsError(CPQException):
    """
    Raised when an authenticated user attempts an operation for which they lack RBAC privileges.
    """
    def __init__(self, detail: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            error_code="INSUFFICIENT_PERMISSIONS",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )

class UserAlreadyExists(CPQException):
    """
    Raised when registering a user with an email or username that is already taken.
    """
    def __init__(self, detail: str = "User already exists", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            error_code="USER_ALREADY_EXISTS",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

class WeakPassword(CPQException):
    """
    Raised when a password fails policy complexity checks.
    """
    def __init__(self, detail: str = "Weak password", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            error_code="WEAK_PASSWORD",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

class InvalidRegistrationData(CPQException):
    """
    Raised when registration validation rules fail (e.g. mismatched passwords).
    """
    def __init__(self, detail: str = "Invalid registration data", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            error_code="INVALID_REGISTRATION_DATA",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

class InvalidCredentials(AuthenticationError):
    """
    Raised when invalid login credentials are provided.
    """
    def __init__(self, detail: str = "Invalid email or password", details: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, details=details)
        self.error_code = "INVALID_CREDENTIALS"

class InvalidRefreshToken(AuthenticationError):
    """
    Raised when an invalid refresh token is used.
    """
    def __init__(self, detail: str = "Invalid refresh token", details: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, details=details)
        self.error_code = "INVALID_REFRESH_TOKEN"

class ExpiredRefreshToken(AuthenticationError):
    """
    Raised when an expired refresh token is used.
    """
    def __init__(self, detail: str = "Refresh token has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, details=details)
        self.error_code = "EXPIRED_REFRESH_TOKEN"

class RevokedRefreshToken(AuthenticationError):
    """
    Raised when a revoked refresh token is used.
    """
    def __init__(self, detail: str = "Refresh token has been revoked", details: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, details=details)
        self.error_code = "REVOKED_REFRESH_TOKEN"

class SessionExpired(AuthenticationError):
    """
    Raised when the session is expired.
    """
    def __init__(self, detail: str = "Session has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, details=details)
        self.error_code = "SESSION_EXPIRED"

class UnauthorizedSession(AuthenticationError):
    """
    Raised when session is invalid or unauthorized.
    """
    def __init__(self, detail: str = "Unauthorized or invalid session", details: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, details=details)
        self.error_code = "UNAUTHORIZED_SESSION"

class PermissionDenied(InsufficientPermissionsError):
    """
    Raised when an action is denied due to lack of permissions.
    """
    pass

class RoleNotFound(CPQException):
    """
    Raised when a role is not found in the database.
    """
    def __init__(self, detail: str = "Role not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            error_code="ROLE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )

class PermissionNotFound(CPQException):
    """
    Raised when a permission is not found in the database.
    """
    def __init__(self, detail: str = "Permission not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            error_code="PERMISSION_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )

class UnauthorizedRoleAssignment(CPQException):
    """
    Raised when assigning a role that is invalid or not allowed.
    """
    def __init__(self, detail: str = "Unauthorized role assignment", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            error_code="UNAUTHORIZED_ROLE_ASSIGNMENT",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

class UnauthorizedPermissionAssignment(CPQException):
    """
    Raised when assigning a permission that is invalid or not allowed.
    """
    def __init__(self, detail: str = "Unauthorized permission assignment", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            detail=detail,
            error_code="UNAUTHORIZED_PERMISSION_ASSIGNMENT",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

class InvalidResetToken(AuthenticationError):
    """
    Raised when an invalid password reset token is used.
    """
    def __init__(self, detail: str = "Invalid reset token", details: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, details=details)
        self.error_code = "INVALID_RESET_TOKEN"

class ExpiredResetToken(AuthenticationError):
    """
    Raised when an expired password reset token is used.
    """
    def __init__(self, detail: str = "Password reset token has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, details=details)
        self.error_code = "EXPIRED_RESET_TOKEN"

class ResetTokenAlreadyUsed(AuthenticationError):
    """
    Raised when a password reset token has already been used.
    """
    def __init__(self, detail: str = "Password reset token has already been used", details: Optional[Dict[str, Any]] = None):
        super().__init__(detail=detail, details=details)
        self.error_code = "RESET_TOKEN_ALREADY_USED"
