FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
   PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
   apt-get upgrade -y && \
   apt-get install -y --no-install-recommends gcc python3-dev libssl-dev && \
   rm -rf /var/lib/apt/lists/* && \
   python -m pip install --upgrade pip 'setuptools>=78.1.1' wheel && \
   groupadd -r appgroup && \
   useradd -r -g appgroup appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appgroup /app

USER appuser

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
   CMD python -c "from urllib.request import urlopen; urlopen('http://localhost:8000/health', timeout=5)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]