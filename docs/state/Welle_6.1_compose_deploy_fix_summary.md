# Welle 6.1 Compose Deploy Fix Summary

Datum: 2026-03-20
Umgebung: Production deploy path, read-only live verification plus local script hardening
Scope: minimale Absicherung des produktiven Compose-Aufrufs ohne Aenderung an Daten, Mounts, Datenbanken oder BlackLab

## Root Cause

Der produktive Deploy laeuft nicht remote von GitHub in einen Zielhost hinein, sondern lokal auf dem Zielserver ueber einen self-hosted GitHub Actions Runner.

Belegte Ausfuehrungskette:

- `.github/workflows/deploy.yml` startet den Job auf `runs-on: self-hosted`
- der Job fuehrt lokal auf dem Server aus:
  - `cd /srv/webapps/corapan/app`
  - `bash scripts/deploy_prod.sh`
- auf dem Zielserver war zum Pruefzeitpunkt verfuegbar:
  - `docker compose`: nicht vorhanden
  - `docker-compose`: vorhanden als `1.29.2`
  - `docker`: `28.2.2`

Damit ist der wahrscheinliche Fehlerpfad serverseitig und nicht runner-external. Die kritische Kombination ist:

- serverlokaler Deploy ueber `scripts/deploy_prod.sh`
- harter Aufruf von `docker-compose`
- nur Compose v1 verfuegbar
- moderner Docker-Stand auf dem Host

Diese Kombination ist die wahrscheinlichste Ursache fuer `KeyError: 'ContainerConfig'` im produktiven Deploy.

## Was geaendert wurde

- `scripts/deploy_prod.sh`
  - fuehrt jetzt eine explizite Compose-Erkennung auf dem Zielhost aus
  - bevorzugt `docker compose` als Compose-V2-Plugin
  - akzeptiert `docker-compose` nur dann, wenn dessen Version als Compose V2 erkennbar ist
  - bricht hart ab, wenn nur `docker-compose` v1 verfuegbar ist
  - loggt Host, Benutzer, Runner-Kontext, Compose-Kommando, Compose-Version und Docker-Version vor dem eigentlichen Deploy-Aufruf
- `docs/changes/2026-03-20-wave6.1-compose-deploy-fix.md`
  - dokumentiert die Verhaltensaenderung und den serverseitigen Root Cause
- `docs/state/instance-structure-unification-plan.md`
  - erweitert um Lessons Learned aus diesem Run

## Exakte Verhaltensaenderung

Neues Auswahlverhalten im Deploy:

1. Wenn `docker compose` verfuegbar ist:
   - dieser Befehl wird verwendet
2. Wenn `docker compose` fehlt, aber `docker-compose` vorhanden ist:
   - nur bei als V2 erkennbarer Version wird dieser Befehl akzeptiert
3. Wenn nur `docker-compose` v1 vorhanden ist:
   - harter Abbruch mit klarer Fehlermeldung
4. Wenn gar kein geeignetes Compose vorhanden ist:
   - harter Abbruch mit klarer Fehlermeldung

Es gibt bewusst keinen stillen Rueckfall mehr auf Compose v1.

## Was bewusst NICHT geaendert wurde

- keine Aenderungen an produktiven Daten
- keine Migrationen
- keine Aenderungen an PostgreSQL/Auth
- keine Aenderungen an Analytics
- keine Aenderungen an BlackLab
- keine Aenderungen an produktiven Mounts oder Pfaden
- keine Container-Loeschungen ausser dem bereits bestehenden Legacy-Container-Handling im Skript
- keine Image-Loeschungen
- keine pauschalen Cleanup-Befehle
- keine Workflow-Aenderung, weil der belegte Fehlerpfad bereits serverlokal im Deploy-Skript liegt

## Verifikation

Read-only live verifiziert:

- Zielserver hat einen laufenden GitHub Actions Runner-Service fuer CORAPAN
- `deploy.yml` fuehrt `bash scripts/deploy_prod.sh` lokal auf dem Server aus
- Zielserver-Compose-Situation zum Checkzeitpunkt:
  - `docker compose`: nicht vorhanden
  - `docker-compose version 1.29.2`
  - `docker version 28.2.2|28.2.2`

Statische Repo-Verifikation nach dem Fix:

- `scripts/deploy_prod.sh` verwendet nicht mehr hart `docker-compose`
- das Skript macht den effektiven Compose-Pfad und die Version vor dem Deploy sichtbar
- Compose-v1 wird jetzt explizit erkannt und verhindert statt still verwendet

## Warum das den Fehler voraussichtlich verhindert

Der beobachtete Fehler entsteht sehr wahrscheinlich im alten serverseitigen Compose-v1-Pfad.

Nach diesem Fix gilt:

- ein moderner Compose-V2-Pfad wird bevorzugt, sobald er auf dem Server vorhanden ist
- der problematische Compose-v1-Pfad wird nicht mehr still benutzt
- der Deploy-Log zeigt kuenftig eindeutig, auf welchem Host und mit welchem Compose-Kommando der Stack gestartet werden soll

Damit wird aus einem spaeten, intransparenten Compose-Fehler ein frueher, eindeutiger und sicherer Abbruch mit klarer Operator-Handlung.