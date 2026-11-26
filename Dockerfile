FROM python:3.12-slim AS build
WORKDIR /wheels
# instagrapi pulls in Pillow and curl_cffi, which need a compiler on slim.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip3 wheel -r requirements.txt


FROM python:3.12-slim
WORKDIR /home/osintig
RUN useradd --create-home --shell /usr/sbin/nologin osintig

COPY --from=build /wheels /wheels
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt -f /wheels \
  && rm -rf /wheels requirements.txt

COPY --chown=osintig:osintig osint_ig/ /home/osintig/osint_ig
COPY --chown=osintig:osintig frontend/ /home/osintig/frontend
COPY --chown=osintig:osintig pyproject.toml /home/osintig/pyproject.toml

# config/, cache/ and dossier/ are mounted at run time (see docker-compose.yml):
# they hold your local session and collected data outside the image.
RUN mkdir -p config cache dossier && chown -R osintig:osintig /home/osintig
USER osintig

EXPOSE 8000
ENTRYPOINT ["uvicorn", "osint_ig.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
