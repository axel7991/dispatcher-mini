
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py database.py ./

RUN python database.py

CMD ["python", "main.py"]
