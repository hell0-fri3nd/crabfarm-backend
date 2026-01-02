FROM python:3.12-slim

EXPOSE 4572

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY .env .env

COPY . .

# Non-root user (optional but good practice)
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser /app
USER appuser

CMD ["uvicorn", "App:app", "--host", "0.0.0.0", "--port", "4572"]
