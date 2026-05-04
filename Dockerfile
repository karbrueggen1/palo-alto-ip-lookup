FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY app.py .
COPY templates/ ./templates/

RUN useradd -r -u 1001 appuser
USER appuser

EXPOSE 5000

CMD ["python", "app.py"]
