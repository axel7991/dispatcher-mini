from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from database import save_request

# 1. Define the information shared between nodes
class DispatcherState(TypedDict):
    message: str
    intent: str
    department: str


# 2. Create our first node
def intake_agent(state: DispatcherState):
    print("Intake agent received:", state["message"])
    return state

def classify_agent(state: DispatcherState):
    message = state["message"].lower()

    if "invoice" in message or "refund" in message:
        intent = "billing"
    else:
        intent = "general"

    print("Detected intent:", intent)

    return {"intent": intent}

def routing_agent(state: DispatcherState):
    intent = state["intent"]

    if intent == "billing":
        department = "Billing"
    else:
        department = "Customer Service"

    print("Selected department:", department)

    return {"department": department}

def billing_agent(state: DispatcherState):
    print("Billing Agent is handling the request")
    return {"department": "Billing"}

def customer_service_agent(state: DispatcherState):
    print("Customer Service Agent is handling the request")
    return {"department": "Customer Service"}

def choose_agent(state: DispatcherState):
    if state["intent"] == "billing":
        return "billing"
    else:
        return "customer_service"

# 3. Build the graph
builder = StateGraph(DispatcherState)
builder.add_node("intake", intake_agent)
builder.add_node("classify", classify_agent)
builder.add_node("routing", routing_agent)
builder.add_node("billing", billing_agent)
builder.add_node("customer_service", customer_service_agent)

builder.add_edge(START, "intake")
builder.add_edge("intake", "classify")

builder.add_conditional_edges(
    "classify",
    choose_agent,
    {
        "billing": "billing",
        "customer_service": "customer_service"
    }
)

builder.add_edge("billing", END)
builder.add_edge("customer_service", END)

# 4. Compile the graph
graph = builder.compile()


# 5. Run the graph
result = graph.invoke({
    "message": "What are your opening hours?"
})

print("Final result:", result)

save_request(
    result["message"],
    result["intent"],
    result["department"]
)

print("Request saved to SQLite!")