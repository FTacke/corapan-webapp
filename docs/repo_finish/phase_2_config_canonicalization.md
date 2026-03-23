# Phase 2 - Config Canonicalization

## 1. Kurzurteil

Die Config-Kanonisierung ist in diesem Run in zwei Ebenen getrennt und fachlich festgezogen worden:

1. **Runtime-Config**
   - kanonischer Host-Pfad ab jetzt: `C:\dev\corapan\data\config`
   - dieser Pfad wurde lokal angelegt
   - es gibt derzeit noch keinen belegten lokalen Payload dort; der Pfad ist als Runtime-Ziel vorbereitet

2. **BlackLab-Config**
   - BlackLab-Konfiguration ist **nicht** Teil des Runtime-Datenbaums
   - sie bleibt als versionierte App-Konfiguration getrennt unter dem aktiven App-Repo-Pfad
   - aktuell also unter `C:\dev\corapan\webapp\config\blacklab`
   - nach dem spaeteren Rename entspricht das dem Zielbild `C:\dev\corapan\app\config\blacklab`

Der wichtigste direkte Drift wurde bereinigt:

- die kanonische Root-Dev-Compose zeigt jetzt fuer `/etc/blacklab` auf `C:\dev\corapan\webapp\config\blacklab` statt auf `C:\dev\corapan\config\blacklab`

Damit gilt ab jetzt:

- `data/config` = kanonische Runtime-Config
- `webapp/config/blacklab` = aktive versionierte BlackLab-Konfiguration im aktuellen Zwischenzustand
- `C:\dev\corapan\config` = kein legitimer konkurrierender Runtime-Source-of-Truth mehr

## 2. Aktuelle Config-Realitaet

### 2.1 Vorhandene Config-Verzeichnisse

Beobachtet im Workspace:

- `C:\dev\corapan\config`
  - vorhanden
  - enthaelt `blacklab/` mit 5 Konfigurationsdateien
- `C:\dev\corapan\data\config`
  - vor diesem Run nicht vorhanden
  - in diesem Run als kanonischer Runtime-Pfad angelegt
  - aktuell leer
- `C:\dev\corapan\webapp\config`
  - vorhanden
  - enthaelt `blacklab/` mit 5 Konfigurationsdateien

### 2.2 Tatsaechlich beobachtete Nutzung

**Live Runtime vor den Aenderungen in diesem Run:**

- `corapan_auth_db` lief aus der Root-Compose `C:\dev\corapan\docker-compose.dev-postgres.yml`
- `blacklab-server-v3` lief dagegen aus `C:\dev\corapan\webapp\docker-compose.dev-postgres.yml`
- der laufende BlackLab-Container mountete:
  - `C:\dev\corapan\data\blacklab\index -> /data/index/corapan`
  - `C:\dev\corapan\webapp\config\blacklab -> /etc/blacklab`

**Kanonische Compose nach den Aenderungen dieses Runs:**

- Root-Compose zeigt jetzt ebenfalls auf `C:\dev\corapan\webapp\config\blacklab -> /etc/blacklab`

### 2.3 Inhaltlicher Drift zwischen Root- und Webapp-Config

Hash-Vergleich der Dateien:

- `corapan-json.blf.yaml`, `corapan-tsv.blf.yaml`, `corapan-wpl.blf.yaml`, `json-metadata.blf.yaml`
  - identisch zwischen Root-`config/blacklab` und `webapp/config/blacklab`
- `blacklab-server.yaml`
  - abweichender Hash zwischen beiden Baeumen

Bewertung:

- `C:\dev\corapan\config\blacklab` ist nicht nur eine harmlose Spiegelkopie, sondern bereits inhaltlich driftend.
- Genau deshalb darf dieser Baum nicht laenger als parallele aktive Config-Quelle weiterlaufen.

### 2.4 Klassifikation der aktuellen Config-Orte

| Pfad | Klassifikation | Begruendung |
|---|---|---|
| `C:\dev\corapan\data\config` | **active** | verbindlich gesetzter kanonischer Runtime-Config-Pfad fuer die Finalstruktur; entspricht dem dokumentierten Prod-Ziel `data/config -> /app/config` |
| `C:\dev\corapan\webapp\config\blacklab` | **active** | aktive versionierte BlackLab-Konfiguration des heutigen App-Repos; entspricht dem produktiven Sonderfall `app/config/blacklab` |
| `C:\dev\corapan\config\blacklab` | **redundant / drift** | kein legitimer Runtime-Source-of-Truth mehr; historischer Zwischenbaum mit bereits beginnendem Inhaltsdrift |

## 3. Kanonische Source-of-Truth

### 3.1 Runtime-Config

Ab jetzt verbindlich:

- **Host-Pfad:** `C:\dev\corapan\data\config`
- **Rolle:** kanonische Runtime-Config fuer die kuenftige Finalstruktur
- **Prod-Entsprechung:** `/srv/webapps/corapan/data/config`
- **Container-Zielbild:** `/app/config`

Wichtige Einordnung:

- Dieser Pfad ist fuer Runtime-Konfiguration gedacht, nicht fuer versionierte BlackLab-Server-/BLF-Konfiguration.
- Es gibt aktuell noch keinen belegten lokalen Runtime-Config-Payload unter `data/config`; der Pfad ist in diesem Run bewusst als leerer Zielpfad angelegt worden.

### 3.2 BlackLab-Config-Sonderfall

Ab jetzt verbindlich:

- **Aktueller Pfad:** `C:\dev\corapan\webapp\config\blacklab`
- **Finaler Pfad nach Rename:** `C:\dev\corapan\app\config\blacklab`
- **Prod-Entsprechung:** `/srv/webapps/corapan/app/config/blacklab`
- **Container-Ziel:** `/etc/blacklab`

Begruendung:

- Die dokumentierte Prod-Realitaet trennt BlackLab-Daten und BlackLab-Konfiguration bereits explizit:
  - Daten unter `data/blacklab/*`
  - Konfiguration unter `app/config/blacklab`
- In den BlackLab-Zielarchitektur-Dokumenten ist ausdruecklich festgehalten, dass `app/config/blacklab` **nicht** in den Datenbaum verschoben werden soll.

Konsequenz:

- `data/config` und `app/config/blacklab` sind **keine konkurrierenden Source-of-Truths**, sondern zwei verschiedene Config-Klassen.

### 3.3 Root-`config/`

Festlegung:

- Root-`config/` hat aktuell **keinen** legitim belegten dauerhaften Runtime-Zweck mehr.
- Solange kein separater, explizit dokumentierter Nicht-Runtime-Zweck definiert wird, ist dieser Baum als Drift-/Altlast zu behandeln.

## 4. Compose- und Script-Referenzen

### 4.1 Root Dev Compose

Datei:

- `C:\dev\corapan\docker-compose.dev-postgres.yml`

Vorher:

- `./config/blacklab:/etc/blacklab:ro`

Jetzt:

- `./webapp/config/blacklab:/etc/blacklab:ro`

Bewertung:

- **vorher Drift**
- **jetzt fachlich korrekt** fuer den aktuellen Zwischenzustand

### 4.2 Webapp Dev Compose

Datei:

- `C:\dev\corapan\webapp\docker-compose.dev-postgres.yml`

Vorher:

- `../config/blacklab:/etc/blacklab:ro`

Jetzt:

- `./config/blacklab:/etc/blacklab:ro`

Bewertung:

- **vorher Drift** gegen den beobachteten aktiven BlackLab-Mount und gegen den BlackLab-Sonderfall `app/config/blacklab`
- **jetzt intern konsistent** als Uebergangsdatei

### 4.3 BlackLab Startskript

Datei:

- `C:\dev\corapan\webapp\scripts\blacklab\start_blacklab_docker_v3.ps1`

Vorher:

- `configRoot = workspaceRoot/config`

Jetzt:

- `configRoot = webappRoot/config`

Bewertung:

- **vorher Drift**
- **jetzt fachlich korrekt** fuer die aktuelle versionierte App-Konfiguration

### 4.4 BlackLab Build-Skripte

Dateien:

- `C:\dev\corapan\webapp\scripts\blacklab\build_blacklab_index.ps1`
- `C:\dev\corapan\webapp\scripts\blacklab\build_blacklab_index.sh`

Vorher:

- Nutzung von `workspaceRoot/config/blacklab`

Jetzt:

- Nutzung von `webappRoot/config/blacklab`

Bewertung:

- **vorher Drift**
- **jetzt fachlich korrekt** und in Linie mit dem produktiven Sonderfall `app/config/blacklab`

### 4.5 Prod Compose und Publish-Deploy-Helfer

Beobachtung:

- `C:\dev\corapan\webapp\infra\docker-compose.prod.yml` mountet weiterhin korrekt:
  - `/srv/webapps/corapan/data/config -> /app/config`
- `C:\dev\corapan\webapp\scripts\deploy_sync\publish_blacklab_index.ps1` verwendet weiterhin korrekt:
  - `/srv/webapps/corapan/app/config/blacklab`

Bewertung:

- hier war **kein** direkter Korrekturbedarf noetig
- diese Produktionspfade bestaetigen die nun festgezogene Trennung:
  - Runtime-Config unter `data/config`
  - BlackLab-Config unter `app/config/blacklab`

## 5. BlackLab-Config-Bewertung

### 5.1 Existierende BlackLab-Config-Pfade

- `C:\dev\corapan\config\blacklab`
- `C:\dev\corapan\webapp\config\blacklab`

### 5.2 Lokal tatsaechlich genutzter Pfad

Belegt durch `docker inspect blacklab-server-v3` vor den Aenderungen dieses Runs:

- `C:\dev\corapan\webapp\config\blacklab -> /etc/blacklab`

### 5.3 Final kanonischer Pfad

Fuer den aktuellen Zwischenzustand:

- `C:\dev\corapan\webapp\config\blacklab`

Fuer den finalen Zustand nach Rename:

- `C:\dev\corapan\app\config\blacklab`

### 5.4 Inhaltdrift oder nur Pfaddrift?

Ergebnis:

- ueberwiegend Pfaddrift
- aber nicht nur: `blacklab-server.yaml` unterscheidet sich bereits zwischen Root- und Webapp-Baum

Bewertung:

- Es liegt **echter inhaltlicher Drift** vor, nicht nur eine doppelte Lage derselben Dateien.
- Deshalb war es fachlich begruendet, die Compose-/Script-Source-of-Truth direkt auf den versionierten App-Baum umzustellen.

### 5.5 Was in diesem Run bewusst nicht gemacht wurde

- kein Verschieben von `webapp/config/blacklab` nach `data/config/blacklab`
- kein Loeschen von `C:\dev\corapan\config\blacklab`
- kein Neustart des laufenden BlackLab-Containers

Begruendung:

- BlackLab-Konfiguration gehoert gemaess dokumentiertem Zielbild nicht in den Datenbaum
- das Entfernen der Root-Kopie ist erst sinnvoll, wenn der laufende Container kontrolliert auf die nun korrigierte kanonische Root-Compose umgeschaltet und danach erneut verifiziert wurde

## 6. Durchgefuehrte Aenderungen

In diesem Run direkt umgesetzt:

1. `C:\dev\corapan\data\config` lokal angelegt
2. Root-Dev-Compose auf `./webapp/config/blacklab` umgestellt
3. `webapp/docker-compose.dev-postgres.yml` intern auf `./config/blacklab` korrigiert
4. `webapp/scripts/blacklab/start_blacklab_docker_v3.ps1` auf App-Config umgestellt
5. `webapp/scripts/blacklab/build_blacklab_index.ps1` auf App-Config umgestellt
6. `webapp/scripts/blacklab/build_blacklab_index.sh` auf App-Config umgestellt
7. `C:\dev\corapan\docs\repo_finish\repo_finish.md` fachlich korrigiert

### 6.1 Korrekturen in `repo_finish.md`

Geaendert:

- Root-`config/` aus der Zielstruktur entfernt
- `data/config` als kanonische Runtime-Config in die Zielstruktur aufgenommen
- `app/config/blacklab` explizit als versionierte BlackLab-Konfiguration festgehalten
- `.gitignore`-Liste um den nicht mehr kanonischen Root-`config/`-Eintrag bereinigt
- unter den Pipeline-Pruefpunkten die getrennte BlackLab-Konfiguration ergaenzt

Warum geaendert:

- der alte Plan vermischte Root-`config/` mit der inzwischen belegten produktionsnahen `data/config`-Realitaet
- zugleich fehlte die explizite Festhaltung, dass BlackLab-Konfiguration getrennt vom Runtime-Datenbaum bleibt

Ersetzte fruehere Planannahme:

- frueher: Root-`config/` als Teil der finalen Struktur
- jetzt: `data/config` fuer Runtime-Config, `app/config/blacklab` fuer versionierte BlackLab-Konfiguration

## 7. Erforderliche Folgearbeiten

### Sofort als naechster Umsetzungsrun sinnvoll

1. Laufenden `blacklab-server-v3` kontrolliert auf die nun korrigierte Root-Compose umstellen
2. danach per `docker inspect` erneut verifizieren, dass `/etc/blacklab` aus `C:\dev\corapan\webapp\config\blacklab` kommt
3. Root-`config\blacklab` gegen `webapp\config\blacklab` inhaltlich diffen und entscheiden, ob Root-`config` komplett entfernbar ist

### Danach

4. offene Hilfsskripte und Doku mit alten Root-`config/blacklab`-Annahmen bereinigen
5. `data/config` nur dann mit konkretem Runtime-Payload befuellen, wenn dieser Payload fachlich wirklich Runtime-Konfiguration ist und nicht versionierte App-/BlackLab-Konfiguration

### Bis nach Git-Root-Hochzug warten

6. Entfernen der `webapp`-Kompatibilitaetslogik in Maintenance-Wrappern
7. groessere Repo-weite Pfadbereinigung aller `webapp/`-Bezeichnungen

### Bis nach `webapp -> app` warten

8. finaler Wechsel aller App-Config-Referenzen von `webapp/config/blacklab` auf `app/config/blacklab`
9. Entfernen der letzten `WebappRepoPath`-Kompatibilitaetsaliasen dort, wo sie nur noch Rename-Uebergangslogik tragen

## 8. Go / No-Go fuer den naechsten Run

### GO

Jetzt direkt moeglich:

1. kontrollierter BlackLab-Neustart auf Basis der korrigierten Root-Compose
2. danach Root-`config/blacklab` als redundante Altlast verifizieren
3. weitere Compose-/Script-Drifts gegen die nun definierte Trennung bereinigen:
   - Runtime-Config unter `data/config`
   - BlackLab-Config unter `webapp/config/blacklab` bzw. spaeter `app/config/blacklab`

### NO-GO

Noch nicht sinnvoll:

1. BlackLab-Konfiguration in `data/config` verschieben
2. Root-`config/` ohne Laufzeit-Recheck sofort loeschen
3. `webapp -> app` im selben Run mit dieser Config-Kanonisierung mischen
4. pauschal alle `webapp`-Pfadangaben entfernen, solange Git-Root-Hochzug und Rename noch ausstehen

## Ergebnisbewertung

Bereits kanonisiert in diesem Run:

- `data/config` als kanonischer Runtime-Config-Pfad festgelegt und lokal angelegt
- BlackLab-Konfiguration explizit als getrennte App-Konfiguration festgelegt
- Root-Dev-Compose und die zentralen lokalen BlackLab-Helfer auf diese Trennung ausgerichtet
- `repo_finish.md` auf das reale Zielbild korrigiert

Jetzt als Source-of-Truth festgelegt:

- Runtime-Config: `C:\dev\corapan\data\config`
- aktive versionierte BlackLab-Konfiguration im Zwischenzustand: `C:\dev\corapan\webapp\config\blacklab`
- finale BlackLab-Konfiguration nach Rename: `C:\dev\corapan\app\config\blacklab`

Offen bleibende Drift:

- laufender BlackLab-Container wurde in diesem Run nicht neu erzeugt und muss noch kontrolliert auf die nun korrigierte Root-Compose gezogen werden
- Root-`config\blacklab` existiert noch physisch und ist als redundante Driftkopie noch nicht entfernt
- einige Doku- und Hilfsskript-Referenzen ausserhalb der direkt korrigierten Kernpfade tragen weiter historische `config/blacklab`-Annahmen

Arbeitsfazit:

- **Der Weg ist frei fuer den naechsten Umsetzungsrun.**
- Der naechste fachlich saubere Schritt ist jetzt nicht mehr Grundsatzanalyse, sondern ein kontrollierter BlackLab-Config-Recheck inklusive Umschalten der laufenden Dev-Instanz auf die nun korrigierte kanonische Compose-/Script-Quelle.