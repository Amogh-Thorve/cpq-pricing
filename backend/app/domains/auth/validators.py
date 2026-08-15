import re
from backend.app.domains.auth.utils import password_policy
from backend.app.domains.auth.exceptions import WeakPassword, InvalidRegistrationData

def validate_password_complexity(password: str) -> None:
    """
    Validates a password against the configured enterprise password policy.
    Raises WeakPassword if validation fails.
    """
    if len(password) < password_policy.min_length:
        raise WeakPassword(
            f"Password must be at least {password_policy.min_length} characters long."
        )
    
    if password_policy.require_uppercase and not re.search(r"[A-Z]", password):
        raise WeakPassword("Password must contain at least one uppercase letter.")
        
    if password_policy.require_lowercase and not re.search(r"[a-z]", password):
        raise WeakPassword("Password must contain at least one lowercase letter.")
        
    if password_policy.require_numbers and not re.search(r"\d", password):
        raise WeakPassword("Password must contain at least one number.")
        
    if password_policy.require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise WeakPassword("Password must contain at least one special character.")

def validate_email_format(email: str) -> None:
    """
    Standard email verification.
    Raises InvalidRegistrationData if email format is invalid.
    """
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        raise InvalidRegistrationData("Invalid email address format.")
