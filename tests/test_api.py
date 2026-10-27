from fastapi.testclient import TestClient
from unittest.mock import patch
from api import app

client = TestClient(app)


def test_dispatch_billing():
    fake_result = {
        "message": "I was charged twice",
        "intent": "billing",
        "department": "Billing",
        "response": "A billing representative can review your request."
    }

    with patch("api.graph.invoke", return_value=fake_result):
        with patch("api.save_request") as mock_save:
            response = client.post(
                "/dispatch",
                json={"message": "I was charged twice"}
            )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "processed"
    assert data["intent"] == "billing"
    assert data["department"] == "Billing"
    assert data["response"] == fake_result["response"]

    mock_save.assert_called_once_with(
        "I was charged twice",
        "billing",
        "Billing"
    )

def test_dispatch_missing_message():
    response = client.post(
        "/dispatch",
        json={}
    )

    assert response.status_code == 422