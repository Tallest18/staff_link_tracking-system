from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify

from .errors import not_found
from .validation import boolean, email, is_doc_id, optional_text, read_changes, read_fields, text

staff_bp = Blueprint("staff", __name__)

CHECKERS = {
    "name": text,
    "email": email,
    "department": optional_text,
    "active": boolean,
}


def _staff():
    return current_app.config["DB"].collection("staff")


def _to_json(staff_id, data):
    return {"id": staff_id, **data, "created_at": data["created_at"].isoformat()}


def staff_exists(staff_id):
    return is_doc_id(staff_id) and _staff().document(staff_id).get().exists


@staff_bp.get("/staff")
def list_staff():
    docs = sorted(_staff().stream(), key=lambda doc: doc.to_dict()["name"].lower())
    return jsonify([_to_json(doc.id, doc.to_dict()) for doc in docs])


@staff_bp.post("/staff")
def add_staff():
    fields = read_fields(CHECKERS, required=["name", "email"])
    record = {
        "department": "",
        "active": True,
        **fields,
        "created_at": datetime.now(timezone.utc),
    }

    doc = _staff().document()  # no ID given, so Firestore generates one
    doc.set(record)
    return jsonify(_to_json(doc.id, record)), 201


@staff_bp.patch("/staff/<staff_id>")
def edit_staff(staff_id):
    changes = read_changes(CHECKERS)

    if not is_doc_id(staff_id):
        raise not_found("Staff member not found")
    doc = _staff().document(staff_id)
    current = doc.get()
    if not current.exists:
        raise not_found("Staff member not found")

    doc.update(changes)
    return jsonify(_to_json(staff_id, {**current.to_dict(), **changes}))
