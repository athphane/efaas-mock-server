FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py constants.py crypto.py user_generator.py templates.py ./

EXPOSE 5000

ENV HOST=0.0.0.0
ENV PORT=5000

CMD ["python", "server.py"]
