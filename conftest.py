import sys
from pathlib import Path

# Make `core` and `bots` importable as top-level packages when running
# pytest from the repo root (no setup.py/pyproject needed for this size
# of project).
sys.path.insert(0, str(Path(__file__).resolve().parent))
