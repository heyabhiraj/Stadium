FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run uvicorn server on port 8000 (Cloud Run uses 8080 by default, but we can set the port or just use 8000 and let Cloud Run know)
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn stadiummind.main:app --host 0.0.0.0 --port ${PORT}"]
