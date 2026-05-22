FROM python:3.11-slim

RUN useradd -m -s /bin/bash sandbox \
    && mkdir -p /app /tmp/sandbox-work \
    && chown -R sandbox:sandbox /app /tmp/sandbox-work

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY executor_api.py .

USER sandbox

ENV PYTHONUNBUFFERED=1 \
    SANDBOX_WORK_DIR=/tmp/sandbox-work

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')" || exit 1

CMD ["python", "executor_api.py"]
