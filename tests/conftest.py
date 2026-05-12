import pytest
from database import init_db


@pytest.fixture(autouse=True, scope="session")
def setup_db():
    """Ensure DB tables exist before any test runs."""
    init_db()
