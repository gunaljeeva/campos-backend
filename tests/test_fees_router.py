def test_invoice_model_has_paid_columns():
    from app.models.finance import Invoice
    cols = Invoice.__table__.columns.keys()
    assert "paid_at" in cols
    assert "payment_ref" in cols


def test_payment_model_matches_db_columns():
    from app.models.finance import Payment
    cols = Payment.__table__.columns.keys()
    assert "reference_no" in cols
    assert "razorpay_order_id" in cols
    assert "paid_by" in cols
    assert "reference" not in cols


def test_mark_paid_requires_auth(client):
    resp = client.patch("/fees/invoices/00000000-0000-0000-0000-000000000000/mark-paid", json={})
    assert resp.status_code == 403


def test_update_structure_requires_auth(client):
    resp = client.patch("/fees/structures/00000000-0000-0000-0000-000000000000", json={"amount": 100})
    assert resp.status_code == 403


def test_list_payments_requires_auth(client):
    resp = client.get("/fees/payments", params={"school_id": "00000000-0000-0000-0000-000000000000"})
    assert resp.status_code == 403


def test_invoice_with_student_schema_has_fields():
    from app.schemas.finance import InvoiceWithStudentOut
    f = InvoiceWithStudentOut.model_fields
    assert "students" in f and "paid_at" in f and "payment_ref" in f
