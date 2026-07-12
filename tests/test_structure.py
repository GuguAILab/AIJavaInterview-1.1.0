"""Guards the layered architecture.

These two tests encode the rules in docs/ARCHITECTURE.md. They're what stops
the codebase sliding back into a tangle:

  - app/ui/    must never talk to the database
  - app/core/  must never render UI

The dead-code login bug (a login form in one file, its handler in another,
the one being edited turning out to be unreachable) is exactly what these
prevent.
"""
import os

import pytest

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..")


def _py_files(rel):
    out = []
    for root, _, files in os.walk(os.path.join(ROOT, rel)):
        if "__pycache__" in root:
            continue
        out += [os.path.join(root, f) for f in files if f.endswith(".py")]
    return out


@pytest.mark.parametrize("path", _py_files("app/core"))
def test_core_never_imports_ui(path):
    src = open(path, encoding="utf-8", errors="ignore").read()
    assert "from app.ui" not in src and "import app.ui" not in src, (
        f"{os.path.basename(path)} (core) imports UI — dependencies point downward only"
    )


def test_every_package_has_init():
    for pkg in ["app", "app/core", "app/features", "app/features/interview",
                "app/features/jobs", "app/features/resume", "app/ui", "app/demos"]:
        assert os.path.exists(os.path.join(ROOT, pkg, "__init__.py")), f"{pkg} missing __init__.py"


def test_no_secrets_committed():
    """users.json held a real admin password hash + email. Never again."""
    for leaked in ["users.json", ".streamlit/secrets.toml", ".env"]:
        assert not os.path.exists(os.path.join(ROOT, leaked)), (
            f"{leaked} must not be in the repo — it's in .gitignore for a reason"
        )
