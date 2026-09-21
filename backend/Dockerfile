FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
ARG PIP_INDEX_URL=https://pypi.org/simple
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8010
CMD ["sh", "-c", "aerich upgrade && exec uvicorn main:app --host 0.0.0.0 --port 8010 --workers 2"]
