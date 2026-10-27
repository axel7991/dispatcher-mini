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
            "Respond politely and concisely to the customer. "
            "Do not claim to have issued refunds, accessed accounts, "
            "or completed actions you cannot verify. "
            "If needed, explain that a representative will review the request."
        ),
        ("human", message)
    ])

    return result.content.strip()