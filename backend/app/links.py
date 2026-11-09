import secrets
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from google.api_core.exceptions import Conflict
from google.cloud.firestore_v1.base_query import FieldFilter

from .errors import invalid, not_found
from .staff import staff_exists
from .validation import boolean, http_url, is_doc_id, read_changes, read_fields, text

links_bp = Blueprint("links", __name__)

# Leaves out characters that are easy to confuse, like l and 1, or o and 0.
CODE_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"
CODE_LENGTH = 7
MAX_CODE_ATTEMPTS = 5

CREATE_CHECKERS = {"staff_id": text, "title": text, "destination_url": http_url}
EDIT_CHECKERS = {"title": text, "destination_url": http_url, "active": boolean}


def _links():
    return current_app.config["DB"].collection("links")


def _to_json(code, data):
    return {"code": code, **data, "created_at": data["created_at"].isoformat()}


def _new_code():
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


@links_bp.get("/links")
def list_links():
    query = _links()
    staff_id = request.args.get("staff_id")
    if staff_id:
        query = query.where(filter=FieldFilter("staff_id", "==", staff_id))

    # Sorting here avoids needing a composite index in Firestore.
    docs = sorted(query.stream(), key=lambda doc: doc.to_dict()["created_at"], reverse=True)
    return jsonify([_to_json(doc.id, doc.to_dict()) for doc in docs])


@links_bp.post("/links")
def create_link():
    fields = read_fields(CREATE_CHECKERS, required=list(CREATE_CHECKERS))
    if not staff_exists(fields["staff_id"]):
        raise invalid("staff_id does not match a staff member")

    record = {
        **fields,
        "click_count": 0,
        "active": True,
        "created_at": datetime.now(timezone.utc),
    }

    # create() refuses to overwrite, so a taken code just means trying another.
    for _ in range(MAX_CODE_ATTEMPTS):
        code = _new_code()
        try:
            _links().document(code).create(record)
        except Conflict:
            continue
        return jsonify(_to_json(code, record)), 201

    raise RuntimeError("Could not generate an unused short code")


@links_bp.patch("/links/<code>")
def edit_link(code):
    changes = read_changes(EDIT_CHECKERS)

    if not is_doc_id(code):
        raise not_found("Link not found")
    doc = _links().document(code)
    current = doc.get()
    if not current.exists:
        raise not_found("Link not found")

    doc.update(changes)
    return jsonify(_to_json(code, {**current.to_dict(), **changes}))
