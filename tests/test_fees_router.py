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
