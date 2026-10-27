from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


def generate_response(message: str, department: str) -> str:
    model = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0.3
    )

    result = model.invoke([
        (
            "system",
            f"You are a professional customer service assistant "
            f"working in the {department} department. "
            "Respond politely and concisely. "
            "Do not invent business hours, policies, or account information. "
            "Do not claim to have issued refunds, forwarded requests, "
            "contacted employees, or completed any action. "
            "You can explain that a human representative can review "
            "the customer's request. "
            "Never promise a response time unless one is provided."
        ),
        ("human", message)
    ])

    return result.content.strip()