import os
from functools import cache
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

DEFAULT_KEY_PATH = Path(__file__).resolve().parent.parent / "firebase-service-account.json"


@cache
def connect_firestore():
    """Log in to Firebase once and return the Firestore client."""
    key_path = Path(os.environ.get("FIREBASE_KEY_PATH", DEFAULT_KEY_PATH))
    if not key_path.is_file():
        raise RuntimeError(
            f"Firebase key not found at {key_path}. Download one from Firebase "
            "console > Project settings > Service accounts."
        )

    firebase_admin.initialize_app(credentials.Certificate(str(key_path)))
    return firestore.client()
