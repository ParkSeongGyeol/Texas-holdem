import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

print(f"CWD: {os.getcwd()}")
print(f"PYTHONPATH: {sys.path}")

try:
    from src.web.app import app
    print("Successfully imported app")
except Exception as e:
    print(f"Failed to import app: {e}")
    import traceback
    traceback.print_exc()
