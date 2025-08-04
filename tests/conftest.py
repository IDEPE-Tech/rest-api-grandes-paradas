"""Ensure project root is on sys.path so that `import app` works when tests are
executed from any directory or by CI runners.
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
