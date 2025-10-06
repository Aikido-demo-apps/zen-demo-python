FROM python:3.13.2 AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app


RUN python -m venv .venv

COPY requirements.txt ./
RUN .venv/bin/pip install -r requirements.txt

FROM python:3.13.2-slim
WORKDIR /app
RUN apt update && apt install -y gdb procps
COPY --from=builder /app/.venv .venv/
COPY . .
ENV AIKIDO_BLOCK="1"
CMD ["/app/.venv/bin/gunicorn", "--bind=[::]:8080", "--access-logfile=-", "--workers=4", "wsgi:app"]
