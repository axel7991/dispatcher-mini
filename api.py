from fastapi import FastAPI
from pydantic import BaseModel

from main import graph
from database import create_tables, save_request

app = FastAPI(title="Dispatcher Mini API")

create_tables()


class CustomerRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {"message": "Dispatcher Mini is running!"}


@app.post("/dispatch")
def dispatch(request: CustomerRequest):

    result = graph.invoke({
        "message": request.message
    })

    save_request(
        result["message"],
        result["intent"],
        result["department"]
    )

    return {
    "status": "processed",
    "message": result["message"],
    "intent": result["intent"],
    "department": result["department"],
    "response": result.get("response", "")
}