# processor/Dockerfile
FROM python:3.13-slim

WORKDIR /processor

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY processor /processor/processor


ENV PYTHONPATH=/processor

# default entrypoint runs the CLI
ENTRYPOINT ["python", "-m", "processor.processor"]
