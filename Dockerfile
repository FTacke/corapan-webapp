# Verwende ein offizielles Python-Image als Basis
FROM python:3.9.17-slim

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Installiere Systemabhängigkeiten und reinige den Cache
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Kopiere die Anforderungen und installiere sie
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Stelle sicher, dass pyjwt mit Cryptography-Unterstützung installiert wird
RUN pip install --no-cache-dir "pyjwt[crypto]"

# Kopiere den Rest der Anwendung
COPY . .

# Schlüsseldateien werden nicht mehr ins Image kopiert, sondern als Volume gemountet
# COPY keys /app/keys

# Exponiere den Port, auf dem Flask läuft
EXPOSE 5000

# Setze Umgebungsvariablen (optional, aber empfohlen)
ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Führe die Flask-App aus
CMD ["python", "app.py"]

RUN apt-get update && apt-get install -y ffmpeg
