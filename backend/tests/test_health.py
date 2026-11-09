from app import create_app


def test_health_returns_ok():
    client = create_app(db=object()).test_client()

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
