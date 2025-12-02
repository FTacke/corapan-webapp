# CO.RA.PAN – Server- und Deployment-Setup (marele.online.uni-marburg.de)

## 1. Server / Host

- Hostname (intern): `vhrz2184.HRZ.uni-marburg.de`
- Alias (extern): `marele.online.uni-marburg.de`
- Öffentliche URL der App: `https://corapan.online.uni-marburg.de`
- RAM/CPU: 1 vCPU, 1 GB RAM, 20 GB Disk

## 2. Verzeichnisstruktur

Root für Webapps:

- `/srv/webapps/corapan/`

Unterordner:

- `/srv/webapps/corapan/app`    – Git-Checkout der neuen corapan-webapp (Repo: https://github.com/FTacke/corapan-webapp)
- `/srv/webapps/corapan/data`   – Daten (nicht in Git, per rsync vom Laptop)
- `/srv/webapps/corapan/media`  – Medien (nicht in Git, per rsync vom Laptop)
- `/srv/webapps/corapan/config` – Config-Files (z. B. `passwords.env`, Keys)
- `/srv/webapps/corapan/logs`   – optionale App-Logs

Alte Struktur:

- `/root/corapan` – alte App + Medien; wird nach Migration gelöscht.

## 3. Git / Branch-Policy / Runner

- Repo: `https://github.com/FTacke/corapan-webapp`
- Prod-Branch: `main`
- Deployment-Trigger: `push` auf `main`
- GitHub self-hosted Runner:
  - läuft auf `marele`-Server als User: `<tbd>` (z. B. `corapan`)
  - Working-Directory des Runners: `<tbd>` (Standard `_work`-Pfad)
  - Rechte:
    - RW auf `/srv/webapps/corapan/app`, `/srv/webapps/corapan/data`, `/srv/webapps/corapan/media`, `/srv/webapps/corapan/config`

## 4. Docker-Setup für die App

Docker-Image:

- wird aus `/srv/webapps/corapan/app` gebaut (`Dockerfile` im Repo).
- Image-Tag: `corapan-app` (oder `corapan-app:latest`).

Container-Start (Beispiel):

```bash
docker run -d --name corapan-container \
  --restart unless-stopped \
  -p 6000:5000 \
  -v /srv/webapps/corapan/media/mp3-full:/app/media/mp3-full:ro \
  -v /srv/webapps/corapan/media/mp3-split:/app/media/mp3-split:ro \
  -v /srv/webapps/corapan/media/mp3-temp:/app/media/mp3-temp \
  -v /srv/webapps/corapan/media/transcripts:/app/media/transcripts:ro \
  -v /srv/webapps/corapan/config/passwords.env:/app/passwords.env:ro \
  -v /srv/webapps/corapan/config/keys:/app/config/keys:ro \
  -v /srv/webapps/corapan/data/db:/app/data/db:ro \
  -v /srv/webapps/corapan/data/counters:/app/data/counters \
  corapan-app

5. Datenbank (Postgres)

    Modus: native Postgres-Installation auf dem Host.

    Host: localhost

    Port: 5432

    DB-Name: corapan_auth

    DB-User: corapan_app

    Passwort: <tbd>

    ENV in der App:
    DATABASE_URL=postgresql://corapan_app:<PASS>@localhost:5432/corapan_auth

Prod-Setup-Script:

    führt Migrationen aus

    legt initialen Admin an, falls keiner existiert:

        ADMIN_USERNAME=admin

        ADMIN_EMAIL=<tbd>

        ADMIN_PASSWORD=change-me

6. Daten / Media

Host-Verzeichnisse:

    /srv/webapps/corapan/data

    /srv/webapps/corapan/media

Befüllung:

    nicht über Git

    per rsync vom Entwicklungsrechner/Datenspeicher auf den Server (über SSH/VPN)

rsync-Regeln:

    Alle Unterordner werden synchronisiert, außer:

        data/stats_temp

        data/counters

        media/mp3-temp

Diese Verzeichnisse werden vom rsync ausgeschlossen, weil sie laufzeit-/temp-orientiert sind.
7. Reverse Proxy & TLS

    Reverse Proxy: <nginx oder apache, tbd>

    Konfigurationsdatei(en):

        <tbd> (z. B. /etc/nginx/sites-available/corapan.conf)

    Backend-Ziel:

        http://127.0.0.1:6000

    TLS-Zertifikate:

        <tbd> (z. B. Let’s Encrypt unter /etc/letsencrypt/live/corapan.online.uni-marburg.de/)

8. Deployment-Ablauf (Runner)

Workflow deploy.yml (vereinfacht):

    Trigger: push auf main.

    Job läuft auf self-hosted Runner.

    scripts/deploy_prod.sh führt aus:

        git fetch / reset --hard origin/main im /srv/webapps/corapan/app

        docker build -t corapan-app .

        alten Container stoppen/entfernen

        neuen Container mit obigen Volumes starten

        (optional) DB-Setup-Script aufrufen

data/media werden hier nicht angefasst.
9. Manuelles Daten-Deployment

Vom Entwicklungsrechner:

# Daten
rsync -av \
  --exclude 'stats_temp/' \
  --exclude 'counters/' \
  marele_local_data/ marele@marele.online.uni-marburg.de:/srv/webapps/corapan/data/

# Medien
rsync -av \
  --exclude 'mp3-temp/' \
  marele_local_media/ marele@marele.online.uni-marburg.de:/srv/webapps/corapan/media/


Die `<tbd>`-Stellen füllt man dann mit den Infos aus dem Server (Usernamen, exakte Pfade, Proxy-Typ).

