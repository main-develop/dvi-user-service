FROM python:3.12-slim-bookworm AS builder
WORKDIR /app
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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

ENTRYPOINT ["./entrypoint.sh"]
EXPOSE 8000
