def test_list_students_requires_auth(client):
    resp = client.get("/students", params={"school_id": "00000000-0000-0000-0000-000000000000"})
    assert resp.status_code == 403


def test_student_with_class_schema_has_classes_field():
    from app.schemas.academic import StudentWithClassOut
    assert "classes" in StudentWithClassOut.model_fields
