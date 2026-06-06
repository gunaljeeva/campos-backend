def test_list_classes_requires_auth(client):
    # No Authorization header -> HTTPBearer rejects with 403
    resp = client.get("/classes", params={"school_id": "00000000-0000-0000-0000-000000000000"})
    assert resp.status_code == 403


def test_create_class_requires_auth(client):
    resp = client.post("/classes", json={
        "school_id": "00000000-0000-0000-0000-000000000000",
        "grade": "7", "section": "A",
    })
    assert resp.status_code == 403
