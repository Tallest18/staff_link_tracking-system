import re
from urllib.parse import urlsplit

from flask import request

from .errors import invalid

EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
UNSAFE_URL_CHARACTERS = re.compile(r"[\s\x00-\x1f\x7f]")
DOC_ID_PATTERN = re.compile(r"[A-Za-z0-9]{1,64}")


# Each checker receives a field's name and value, and returns the cleaned value.

def text(name, value):
    if not isinstance(value, str) or not value.strip():
        raise invalid(f"{name} must be a non-empty string")
    return value.strip()


def optional_text(name, value):
    if not isinstance(value, str):
        raise invalid(f"{name} must be a string")
    return value.strip()


def email(name, value):
    address = text(name, value)
    if not EMAIL_PATTERN.fullmatch(address):
        raise invalid(f"{name} must be a valid email address")
    return address


def boolean(name, value):
    if not isinstance(value, bool):
        raise invalid(f"{name} must be true or false")
    return value


def http_url(name, value):
    url = text(name, value)
    try:
        parts = urlsplit(url)
    except ValueError:
        parts = None
    if (
        parts is None
        or parts.scheme not in ("http", "https")
        or not parts.hostname
        or UNSAFE_URL_CHARACTERS.search(url)
    ):
        raise invalid(f"{name} must be a full http:// or https:// URL")
    return url


def read_fields(checkers, required=()):
    """Read the JSON body, check every field and return the cleaned values."""
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise invalid("Request body must be a JSON object")

    for name in body:
        if name not in checkers:
            raise invalid(f"Unknown field: {name}")
    for name in required:
        if name not in body:
            raise invalid(f"{name} is required")

    return {name: checkers[name](name, value) for name, value in body.items()}


def read_changes(checkers):
    """Like read_fields, for a PATCH: at least one field must be sent."""
    changes = read_fields(checkers)
    if not changes:
        raise invalid("Send at least one field to change")
    return changes


def is_doc_id(value):
    """Firestore rejects some IDs, so only look up ones shaped like ours."""
    return isinstance(value, str) and DOC_ID_PATTERN.fullmatch(value) is not None
