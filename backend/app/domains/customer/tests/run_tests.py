import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))

from backend.app.domains.customer.tests.test_customer_foundation import (
    test_customer_schemas,
    test_contact_schemas,
    test_address_schemas,
    run_async_integration_tests
)

if __name__ == "__main__":
    print("Running Customer Management module tests...")
    try:
        # Sync validation tests
        test_customer_schemas()
        print("OK: test_customer_schemas passed")

        test_contact_schemas()
        print("OK: test_contact_schemas passed")

        test_address_schemas()
        print("OK: test_address_schemas passed")

        # Async integration tests
        asyncio.run(run_async_integration_tests())

        print("\nALL CUSTOMER MANAGEMENT TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    except Exception as e:
        import traceback
        print("\nTEST RUNNER FAILED:")
        traceback.print_exc()
        sys.exit(1)
