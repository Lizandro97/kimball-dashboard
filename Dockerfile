FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

ENV PYTHONPATH=/app/src:/app
RUN chmod +x scripts/startup.sh

EXPOSE 8000

CMD ["scripts/startup.sh"]