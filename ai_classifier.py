from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def create_classifier():
    return ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0
    )

def classify_message(message: str) -> str:
    model = create_classifier()

    response = model.invoke([
        (
            "system",
            "You classify customer service messages. "
            "Return exactly one word: billing or general. "
            "Use billing for payments, invoices, refunds, "
            "charges, or subscription payment problems. "
            "Use general for all other requests. "
            "Do not include explanations."
        ),
        ("human", message)
    ])

    intent = response.content.strip().lower()

    if intent not in ("billing", "general"):
        raise ValueError(f"Unexpected AI classification: {intent}")

    return intent