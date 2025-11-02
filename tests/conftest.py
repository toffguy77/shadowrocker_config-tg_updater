import os
import sys

# Ensure project root is importable as package (so `import bot` works in tests)
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
