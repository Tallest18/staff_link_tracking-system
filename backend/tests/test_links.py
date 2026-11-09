import pytest


def add_staff(client, name="Ada"):
    response = client.post("/api/staff", json={"name": name, "email": "a@example.com"})
    return response.get_json()["id"]


def add_link(client, staff_id, **overrides):
    body = {
        "staff_id": staff_id,
        "title": "Spring campaign",
        "destination_url": "https://example.com/offer",
        **overrides,
    }
    return client.post("/api/links", json=body)


def test_create_link_generates_a_code_and_starts_at_zero_clicks(client):
    staff_id = add_staff(client)

    response = add_link(client, staff_id)

    assert response.status_code == 201
    body = response.get_json()
    assert len(body["code"]) == 7
    assert body["staff_id"] == staff_id
    assert body["click_count"] == 0
    assert body["active"] is True


def test_create_link_tries_again_when_a_code_is_taken(client, monkeypatch):
    codes = iter(["aaaaaaa", "aaaaaaa", "bbbbbbb"])
    monkeypatch.setattr("app.links._new_code", lambda: next(codes))
    staff_id = add_staff(client)

    first = add_link(client, staff_id).get_json()
    second = add_link(client, staff_id).get_json()

    assert first["code"] == "aaaaaaa"
    assert second["code"] == "bbbbbbb"


@pytest.mark.parametrize("staff_id", ["missing", "a/b/c", "__reserved__"])
def test_create_link_needs_a_real_staff_member(client, staff_id):
    response = add_link(client, staff_id)

    assert response.status_code == 400
    assert response.get_json()["error"]["message"] == "staff_id does not match a staff member"


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "ftp://example.com",
        "https://",
        "example.com",
        "https://exa mple.com",
        "https://example.com/\nX-Evil: 1",
        "http://[broken",
        42,
    ],
)
def test_create_link_rejects_unsafe_destinations(client, url):
    response = add_link(client, add_staff(client), destination_url=url)

    assert response.status_code == 400
    assert "destination_url" in response.get_json()["error"]["message"]


def test_list_links_can_filter_by_staff_member(client):
    ada = add_staff(client, "Ada")
    ben = add_staff(client, "Ben")
    add_link(client, ada, title="Ada's link")
    add_link(client, ben, title="Ben's link")

    everything = client.get("/api/links").get_json()
    only_ben = client.get(f"/api/links?staff_id={ben}").get_json()

    assert len(everything) == 2
    assert [link["title"] for link in only_ben] == ["Ben's link"]


def test_edit_link_can_deactivate_it(client):
    code = add_link(client, add_staff(client)).get_json()["code"]

    response = client.patch(f"/api/links/{code}", json={"active": False})

    assert response.status_code == 200
    assert response.get_json()["active"] is False
    assert client.get("/api/links").get_json()[0]["active"] is False


@pytest.mark.parametrize("field, value", [("click_count", 999), ("staff_id", "someone-else")])
def test_edit_link_cannot_change_protected_fields(client, field, value):
    code = add_link(client, add_staff(client)).get_json()["code"]

    response = client.patch(f"/api/links/{code}", json={field: value})

    assert response.status_code == 400
    assert response.get_json()["error"]["message"] == f"Unknown field: {field}"


@pytest.mark.parametrize("code", ["missing", "__reserved__"])
def test_edit_unknown_link_returns_404(client, code):
    response = client.patch(f"/api/links/{code}", json={"active": False})

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"
