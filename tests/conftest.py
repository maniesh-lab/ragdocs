"""Shared test setup.

The app loads heavy things the moment it's imported: a sentence-transformers
model (a ~90 MB download), a Chroma database on disk, and a Gemini client that
needs a real API key. None of that is needed to test our own logic, so stand-ins
are put in place *before* the app is imported. The tests then replace the
search and answer functions with fakes where they need them.
"""

import os
import sys
import types
from unittest.mock import MagicMock

os.environ.setdefault("GEMINI_API_KEY", "test-key")

for name in ("sentence_transformers", "chromadb", "chromadb.errors", "google.genai"):
    sys.modules[name] = MagicMock(name=name)

sys.modules["chromadb.errors"].NotFoundError = type("NotFoundError", (Exception,), {})
try:
    import google  # the real namespace package, if installed
except ImportError:
    google = types.ModuleType("google")
google.genai = sys.modules["google.genai"]
sys.modules["google"] = google
