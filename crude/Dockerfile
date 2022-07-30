FROM python:3.10-alpine
COPY requirements.txt requirements.txt

RUN apk add --no-cache build-base && \
    python3 -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del build-base && \
    adduser -D worker && \
    mkdir -p /home/worker/files && \
    chown worker:worker /home/worker/files

USER worker
WORKDIR /home/worker
ENV PATH="/home/worker/.local/bin:${PATH}"
CMD ["uwsgi", "--http", "0.0.0.0:2000", "--master", "-p", "4", "-w", "app:app"]
EXPOSE 2000/tcp

COPY --chown=worker:worker . .

