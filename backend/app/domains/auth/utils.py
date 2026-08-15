import os
from pydantic import BaseModel

class PasswordPolicy(BaseModel):
    """
    Configurable password policy rules for enterprise compliance.
    """
    min_length: int = int(os.getenv("AUTH_PASSWORD_MIN_LENGTH", "8"))
    require_uppercase: bool = os.getenv("AUTH_PASSWORD_REQUIRE_UPPER", "true").lower() == "true"
    require_lowercase: bool = os.getenv("AUTH_PASSWORD_REQUIRE_LOWER", "true").lower() == "true"
    require_numbers: bool = os.getenv("AUTH_PASSWORD_REQUIRE_NUMBERS", "true").lower() == "true"
    require_special: bool = os.getenv("AUTH_PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"
    max_failed_attempts: int = int(os.getenv("AUTH_MAX_FAILED_ATTEMPTS", "5"))
    lockout_duration_minutes: int = int(os.getenv("AUTH_LOCKOUT_DURATION_MINUTES", "15"))

# Singleton instance of password policy
password_policy = PasswordPolicy()
