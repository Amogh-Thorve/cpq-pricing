import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from backend.app.domains.auth.tests.test_auth_foundation import (
    test_user_create_validation,
    test_password_complexity_validator,
    test_email_format_validator,
    run_async_integration_tests
)

if __name__ == "__main__":
    print("Running auth validation and registration tests manually...")
    try:
        # Sync tests
        test_user_create_validation()
        print("OK: test_user_create_validation passed")
        
        test_password_complexity_validator()
        print("OK: test_password_complexity_validator passed")
        
        test_email_format_validator()
        print("OK: test_email_format_validator passed")
        
        # Async integration tests
        asyncio.run(run_async_integration_tests())
        
        print("\nALL REGISTRATION AND VALIDATION TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    except Exception as e:
        import traceback
        print("\nTEST RUNNER FAILED:")
        traceback.print_exc()
        sys.exit(1)
