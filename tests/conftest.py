import os
from pathlib import Path

# CAD font caches belong to this workspace, including during test collection.
os.environ["XDG_CACHE_HOME"] = str(Path(__file__).resolve().parents[1] / ".tools/cache")
