import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

print(f"Project root: {project_root}")

try:
    print("Attempting to import src.main...")
    import src.main
    print("✅ Successfully imported src.main")
except Exception as e:
    print(f"❌ Failed to import src.main: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("Attempting to import src.web.web_server...")
    import src.web.web_server
    print("✅ Successfully imported src.web.web_server")
except Exception as e:
    print(f"❌ Failed to import src.web.web_server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("All imports verified successfully!")
