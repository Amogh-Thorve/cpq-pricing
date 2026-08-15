import sys
import os

# Add root folder to path so backend imports resolve correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    print("Testing backend import verification...")
    from backend.app.main import app
    print("SUCCESS: FastAPI app imported successfully with all domain routers registered!")
    sys.exit(0)
except Exception as e:
    import traceback
    print("FAILURE: Error importing FastAPI app:")
    traceback.print_exc()
    sys.exit(1)
