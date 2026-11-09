import pytest

from app.db import connect_firestore


def test_missing_key_gives_a_clear_error(monkeypatch, tmp_path):
    monkeypatch.setenv("FIREBASE_KEY_PATH", str(tmp_path / "missing.json"))

    with pytest.raises(RuntimeError, match="Firebase key not found"):
        connect_firestore()
