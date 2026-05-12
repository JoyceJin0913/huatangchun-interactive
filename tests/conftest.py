import os
import pytest
from database import init_db

# Redirect all tests to an isolated DB, not the dev novel.db
os.environ["DB_PATH"] = "test_novel.db"


@pytest.fixture(autouse=True, scope="session")
def setup_db():
    """Ensure DB tables exist before any test runs. Uses test_novel.db (not novel.db)."""
    init_db()
    yield
    # Cleanup after test session
    if os.path.exists("test_novel.db"):
        os.remove("test_novel.db")
