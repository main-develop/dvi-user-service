# =========================================
# Stage 1: Dependencies Installation Stage
# =========================================

FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# =========================================
# Stage 2: Run DRF application
# =========================================

FROM python:3.12-slim-bookworm

RUN adduser --disabled-password --gecos '' drfuser

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN chown -R drfuser:drfuser /app
RUN chmod +x ./entrypoint.sh

USER drfuser
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]