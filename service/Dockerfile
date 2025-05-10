# service/Dockerfile
FROM python:3.13-slim


WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service/app /app/service/app

ENV PYTHONPATH=/app

EXPOSE 80
CMD ["uvicorn", "service.app.main:app", "--host", "0.0.0.0", "--port", "80"]
