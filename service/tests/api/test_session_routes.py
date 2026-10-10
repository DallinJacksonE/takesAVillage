def test_consent_sets_session_cookie_and_verify_session_accepts_it(api_context):
    client, _database = api_context

    consent = client.post("/api/consent")

    assert consent.status_code == 200
    user_id = consent.json()["userId"]
    assert consent.json()["message"] == "Consent logged"
    assert consent.cookies.get("user_session") == user_id

    verified = client.get("/api/verifySession")

    assert verified.status_code == 200
    assert verified.json() == {"userId": user_id, "message": "Session valid"}


def test_verify_session_rejects_missing_cookie(api_context):
    client, _database = api_context

    response = client.get("/api/verifySession")

    assert response.status_code == 401
    assert response.json()["detail"] == "No valid session"
