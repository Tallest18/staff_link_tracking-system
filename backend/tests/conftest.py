import pytest
from fake_firestore import FakeFirestore

from app import create_app


@pytest.fixture
def client():
    """A test client backed by a fresh, empty fake database."""
    return create_app(db=FakeFirestore()).test_client()
