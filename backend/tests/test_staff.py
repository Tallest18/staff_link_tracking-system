import pytest

ADA = {"name": "Ada Obi", "email": "ada@example.com"}


def add_staff(client, **overrides):
    return client.post("/api/staff", json={**ADA, **overrides})


def test_add_staff_returns_the_new_record_with_defaults(client):
    response = add_staff(client)

    assert response.status_code == 201
    body = response.get_json()
    assert body["id"]
    assert body["name"] == "Ada Obi"
    assert body["department"] == ""
    assert body["active"] is True
    assert body["created_at"]


def test_list_staff_is_sorted_by_name(client):
    add_staff(client, name="zara")
    add_staff(client, name="Ben")

    names = [person["name"] for person in client.get("/api/staff").get_json()]

    assert names == ["Ben", "zara"]


@pytest.mark.parametrize(
    "body, expected_message",
    [
        ({"email": "ada@example.com"}, "name is required"),
        ({"name": "Ada"}, "email is required"),
        ({"name": "   ", "email": "ada@example.com"}, "name must be a non-empty string"),
        ({"name": "Ada", "email": "not-an-email"}, "email must be a valid email address"),
        ({**ADA, "created_at": "yesterday"}, "Unknown field: created_at"),
    ],
)
def test_add_staff_rejects_invalid_input(client, body, expected_message):
    response = client.post("/api/staff", json=body)

    assert response.status_code == 400
    assert response.get_json() == {
        "error": {"code": "invalid_input", "message": expected_message}
    }


def test_add_staff_rejects_a_body_that_is_not_json(client):
    response = client.post("/api/staff", data="hello")

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_input"


def test_edit_staff_changes_only_the_fields_sent(client):
    staff_id = add_staff(client, department="Sales").get_json()["id"]

    response = client.patch(f"/api/staff/{staff_id}", json={"active": False})

    assert response.status_code == 200
    body = response.get_json()
    assert body["active"] is False
    assert body["department"] == "Sales"
    assert client.get("/api/staff").get_json()[0]["active"] is False


def test_edit_staff_needs_at_least_one_field(client):
    staff_id = add_staff(client).get_json()["id"]

    assert client.patch(f"/api/staff/{staff_id}", json={}).status_code == 400


@pytest.mark.parametrize("staff_id", ["missing", "__reserved__"])
def test_edit_unknown_staff_returns_404(client, staff_id):
    response = client.patch(f"/api/staff/{staff_id}", json={"active": False})

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"


def test_unknown_url_also_uses_the_error_format(client):
    response = client.get("/api/nope")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"
