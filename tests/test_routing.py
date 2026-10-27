from main import choose_agent


def test_billing_routing():
    state = {
        "message": "I was charged twice",
        "intent": "billing",
        "department": "",
        "response": ""
    }

    result = choose_agent(state)

    assert result == "billing"

def test_customer_service_routing():
    state = {
        "message": "What are your opening hours?",
        "intent": "general",
        "department": "",
        "response": ""
    }

    result = choose_agent(state)

    assert result == "customer_service"