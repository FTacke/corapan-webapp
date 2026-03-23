# Phase 1b - Corrected Dev/Prod Assessment

## 1. Kurzurteil

Die aktuelle lokale Dev-Umgebung ist funktional bereits nah am produktiven Zielbild, aber strukturell noch nicht kanonisch finalisiert.

Das letzte Assessment war in mehreren Punkten zu hart, weil es Laufzeitdefekte aus leeren Shell-Umgebungen und aus der noch nicht hochgezogenen Repo-Struktur abgeleitet hat. Diese Schlussfolgerung ist so nicht haltbar.

Belegbare Kurzfassung:

- Die aktive lokale Dev-Orchestrierung kommt aktuell aus `C:\dev\corapan\docker-compose.dev-postgres.yml`.
- Die kanonischen Dev-Einstiegspunkte sind aktuell `C:\dev\corapan\scripts\dev-start.ps1` und `C:\dev\corapan\scripts\dev-setup.ps1`; beide delegieren bewusst an die versionierten Implementierungen unter `C:\dev\corapan\webapp\scripts\...`.
- Die versionierten Dev-Skripte setzen `CORAPAN_RUNTIME_ROOT`, `CORAPAN_MEDIA_ROOT`, `AUTH_DATABASE_URL`, `FLASK_ENV`, `BLS_BASE_URL` und `BLS_CORPUS` explizit zur Laufzeit. Eine leere Shell-Umgebung beweist deshalb kein allgemeines Laufzeitproblem.
- Die aktuelle Dev-Realitaet enthaelt aber echte Strukturdrifts, vor allem bei den Konfigurationsquellen und bei der Trennung zwischen aktiver kanonischer Quelle und Uebergangskopien.

Harter Arbeitsstatus:

- GO fuer gezielte Struktur-Bereinigung und Source-of-Truth-Klaerung
- NO-GO fuer einen sofortigen grossen Umbau `webapp -> app` oder fuer ein pauschales Entfernen aller `webapp`-Kompatibilitaetspfade

## 2. Korrigierte Bewertung der Befunde des letzten Runs

| Befund aus letztem Run | Korrigierte Einstufung | Begruendung |
|---|---|---|
| Zwei `docker-compose.dev-postgres.yml` seien per se ein Laufzeitdefekt | UEBERGANGSARTEFAKT | Die laufenden Container tragen Docker-Compose-Labels mit `config_files=C:\dev\corapan\docker-compose.dev-postgres.yml` und `working_dir=C:\dev\corapan`. Die Root-Datei ist damit aktuell die massgebliche Dev-Compose. Die zusaetzliche Datei unter `webapp/` ist unschoen und drift-anfaellig, aber nicht bereits als solcher ein Laufzeitdefekt. |
| Es sei unklar, welche Dev-Compose aktuell aktiv ist | FALSCHE / UEBERZOGENE SCHLUSSFOLGERUNG | Dieser Punkt ist inzwischen belegbar geklaert: aktiv ist die Root-Compose unter `C:\dev\corapan\docker-compose.dev-postgres.yml`. |
| Leere `CORAPAN_RUNTIME_ROOT`- und `CORAPAN_MEDIA_ROOT`-Variablen in der Shell bedeuteten, dass die App aktuell nicht starten kann | FALSCHE / UEBERZOGENE SCHLUSSFOLGERUNG | `webapp/scripts/dev-start.ps1` und `webapp/scripts/dev-setup.ps1` setzen diese Variablen explizit auf den Workspace-Root bzw. `C:\dev\corapan\media`, wenn sie fehlen. Die App laeuft lokal ueber diese Skripte, nicht ueber eine nackte Shell. |
| `BLS_CORPUS` sei in Dev nicht explizit gesetzt | FALSCHE / UEBERZOGENE SCHLUSSFOLGERUNG | Die Dev-Skripte setzen `BLS_CORPUS=corapan` explizit. Dass die Variable nicht in der Dev-Compose steht, ist fuer den BlackLab-Container nicht entscheidend, weil der BlackLab-Server selbst die Corpus-ID aus dem gemounteten Index liest; relevant ist die App-Umgebung, und die wird durch die Dev-Skripte gesetzt. |
| Fehlender Media-Mount in der Dev-Compose sei ein Dev/Prod-Brecher | FALSCHE / UEBERZOGENE SCHLUSSFOLGERUNG | In Dev laeuft die App nicht im Docker-Container, sondern als Host-Prozess ueber `dev-start.ps1`. Deshalb muss `media/` in der DB/BlackLab-Compose nicht nach `/app/media` gemountet werden, damit die Dev-App funktioniert. |
| Fehlender Export-Mount in der Dev-Compose bedeute moeglichen Datenverlust | FALSCHE / UEBERZOGENE SCHLUSSFOLGERUNG | `data/blacklab/export` ist in Dev ein Host-Pfad fuer Export-/Build-Skripte. Die laufende Dev-Compose startet nur Postgres und BlackLab. Dass der Exportpfad nicht in den BlackLab-Container gemountet ist, ist fuer den laufenden Dev-Stack kein eigenstaendiger Datenverlustbeleg. |
| `webapp/` statt `app/` sei bereits jetzt ein akuter Laufzeitfehler | UEBERGANGSARTEFAKT | Der Repo-Finalisierungsplan legt den Rename bewusst auf den spaeteren isolierten Schritt. Aktuell ist `webapp/` der aktive versionierte App-Repo-Pfad; viele Wrapper sind bereits so gebaut, dass sie spaeter `webapp/` oder Root erkennen koennen. |
| Unterschiedlicher Postgres-User Dev/Prod sei bereits ein Blocker fuer Phase 2 | UEBERGANGSARTEFAKT | Dev nutzt `corapan_auth`, Prod nutzt `corapan_app`, jeweils gegen PostgreSQL und dieselbe logische Auth-DB. Das ist ein Strukturunterschied, aber aktuell kein belegter Funktionsbruch. Es ist ein Konsistenzthema, kein akuter Stopper. |
| Root-`config/blacklab` und `webapp/config/blacklab` seien einfach nur eine Dopplung | ECHTES PROBLEM - muss vor Finalisierung bereinigt werden | Die blosse Koexistenz ist noch kein Defekt. Belegt ist aber ein echter Drift: die kanonische Root-Compose loest `/etc/blacklab` auf `C:\dev\corapan\config\blacklab` auf, waehrend der laufende BlackLab-Container aktuell `C:\dev\corapan\webapp\config\blacklab` gemountet hat. Aktive Runtime und kanonische Compose stimmen also nicht ueberein. |

## 3. Echte Probleme

### 3.1 Aktiver Drift zwischen kanonischer Dev-Compose und laufendem BlackLab-Container

Beleg:

- Docker-Label am laufenden Dev-Container `corapan_auth_db` zeigt als aktive Compose-Quelle `C:\dev\corapan\docker-compose.dev-postgres.yml`.
- `docker compose -f C:\dev\corapan\docker-compose.dev-postgres.yml config` loest den BlackLab-Config-Mount auf `C:\dev\corapan\config\blacklab -> /etc/blacklab` auf.
- `docker inspect blacklab-server-v3` zeigt aktuell aber `C:\dev\corapan\webapp\config\blacklab -> /etc/blacklab`.

Bewertung:

- Das ist kein kosmetisches Doppelartefakt mehr, sondern ein echter Drift zwischen deklarierter kanonischer Dev-Konfiguration und der real laufenden Containerinstanz.
- Vor einer strukturellen Finalisierung muss klar sein, welche BlackLab-Konfigurationsquelle in Dev wirklich kanonisch ist und der Container muss kontrolliert an diese Quelle angeglichen werden.

Risiko: hoch

### 3.2 Konflikt im Zielbild fuer Runtime-Konfiguration

Beleg:

- `docs/repo_finish/repo_finish.md` nennt in der angestrebten Zielstruktur ein Root-`config/`.
- Die produktive Realitaet und die produktionsnahen Migrationsdokumente beschreiben aber fuer den laufenden Zielzustand `data/config` als Runtime-Config-Pfad, gemountet nach `/app/config`.
- Lokal existiert derzeit `C:\dev\corapan\config\blacklab`, waehrend `C:\dev\corapan\data\config` noch fehlt.

Bewertung:

- Das ist ein echter Architekturkonflikt zwischen Plan-Dokument und prod-proven Zielpfad.
- Solange dieser Konflikt nicht explizit entschieden ist, kann keine belastbare Endstruktur fuer Dev=Prod finalisiert werden.
- Fuer Dev=Prod darf das Laufzeit-Ziel nicht nur aus einem Wunschbild im Repo-Finalisierungsplan abgeleitet werden; die produktiv belegte `data/config`-Realitaet wiegt schwerer.

Risiko: hoch

### 3.3 Residuelle Legacy-/Fallback-Logik in Hilfsskripten

Beleg:

- `webapp/scripts/check_release_gates.ps1` faellt fuer Statistiken weiter auf `Join-Path $RepoRoot "runtime\corapan"` zurueck, wenn `CORAPAN_RUNTIME_ROOT` fehlt.
- In mehreren Hilfstexten und Beispielen stehen weiterhin `webapp`- und `corapan-webapp`-bezogene Pfadangaben.

Bewertung:

- Das betrifft nicht die aktive Laufzeit der lokalen App, ist aber ein echter Bereinigungsbedarf fuer die Finalstruktur.
- Solche Fallbacks und Altbezeichnungen koennen spaeter bei Checks, manuellen Operator-Schritten oder nach dem Git-Root-Umzug zu Fehlklassifikationen fuehren.

Risiko: mittel

### 3.4 Top-Level-`logs/` fehlt lokal noch als Zielstruktur-Baustein

Beleg:

- Unter `C:\dev\corapan` existiert derzeit kein `logs/`-Verzeichnis.
- Das Zielbild in der Produktionsdokumentation und im Repo-Finalisierungsplan sieht `logs/` als Bestandteil der finalen Systemstruktur vor.

Bewertung:

- Das ist kein belegter aktueller Laufzeitdefekt, aber ein real offener Strukturpunkt fuer die kanonische Finalstruktur.
- Vor Phase 2 sollte entschieden werden, ob `logs/` in Dev heute schon als fester Top-Level-Runtime-Pfad eingefuehrt wird oder bewusst erst mit dem groesseren Repo-Umzug.

Risiko: niedrig bis mittel

## 4. Uebergangsartefakte

### 4.1 Doppeltes `docker-compose.dev-postgres.yml`

Status:

- `C:\dev\corapan\docker-compose.dev-postgres.yml` ist aktuell die aktive kanonische Dev-Compose.
- `C:\dev\corapan\webapp\docker-compose.dev-postgres.yml` ist eine vorbereitende bzw. legacy-kompatible Parallelkopie.

Bewertung:

- Solange das Git-Root noch nicht auf `corapan/` hochgezogen wurde, ist diese Doppelstruktur erklaerbar.
- Sie ist aber nur als Uebergangsartefakt akzeptabel, wenn die Root-Datei explizit als massgeblich festgehalten und die `webapp`-Kopie nicht mehr als gleichwertige Quelle behandelt wird.

Finale Empfehlung fuer den kanonischen Ort:

- `C:\dev\corapan\docker-compose.dev-postgres.yml`

### 4.2 Root-Wrapper fuer Dev-Skripte

Status:

- `C:\dev\corapan\scripts\dev-start.ps1` und `C:\dev\corapan\scripts\dev-setup.ps1` sind sehr duenne Wrapper auf `C:\dev\corapan\webapp\scripts\...`.

Bewertung:

- Das ist im aktuellen Zwischenzustand sinnvoll: die Dev-Einstiegspunkte liegen schon am zukuenftigen Workspace-Ort, waehrend die aktive versionierte App-Implementierung noch unter `webapp/` lebt.
- Das ist derzeit kein Missstand, sondern eine bewusst eingefuehrte Bruecke fuer den spaeteren Git-Root-Umzug.

### 4.3 `webapp/` statt `app/`

Status:

- Der aktive versionierte App-Repo-Pfad ist weiterhin `C:\dev\corapan\webapp`.
- Mehrere Wrapper und Maintenance-Skripte erkennen bereits `webapp/` oder den Workspace-Root als moegliche App-Repo-Quelle.

Bewertung:

- Das ist ein bekannter Zwischenzustand und passt zum Finalisierungsplan, der den Rename bewusst spaet isoliert.
- Heute bricht daran nicht die laufende lokale App.
- Riskant wird dieser Punkt erst dann, wenn man den Rename ohne vorherige Konsolidierung der Pfadquellen, Wrapper und Repo-Wurzeln erzwingt.

### 4.4 `webapp`-Kompatibilitaet in Maintenance-Wrappern

Status:

- `maintenance_pipelines/_1_blacklab/blacklab_export.py`, `maintenance_pipelines/_2_deploy/deploy_data.ps1` und `maintenance_pipelines/_2_deploy/publish_blacklab.ps1` erkennen bewusst erst `workspace/webapp`, dann `workspace/`.
- Die Doku `docs/prod_migration/2026-03-21_maintenance_pipeline_alignment.md` beschreibt diese Mehrfachauflosung ausdruecklich als Schutz fuer Git-Root-Move und spaeteren Rename.

Bewertung:

- Diese Doppelerkennung ist derzeit kein Fehler, sondern eine sinnvolle Uebergangsmechanik.
- Sie sollte erst entfernt oder vereinfacht werden, wenn Git-Root-Move und abschliessende Repo-Struktur festgezogen sind.

## 5. Ueberzogene oder falsche Schlussfolgerungen des letzten Runs

### 5.1 Allgemeines Laufzeitversagen aus leerer Shell-Umgebung abgeleitet

Nicht belegt.

- Die lokale App laeuft ueber `dev-start.ps1`.
- Diese Skripte setzen die benoetigten Runtime- und App-Variablen explizit.
- Ein manueller Blick auf eine unvorbereitete Shell war daher kein valider Beleg fuer einen allgemeinen Startfehler.

### 5.2 Fehlender Media-Mount in der Dev-Compose als Dev/Prod-Showstopper gewertet

Nicht belegt.

- Die Dev-Compose startet nur Postgres und BlackLab.
- Die App laeuft auf dem Host und liest Medien ueber `CORAPAN_MEDIA_ROOT`.
- Der Punkt ist deshalb kein harter Dev/Prod-Brecher.

### 5.3 Fehlender Export-Mount als Datenverlustargument gewertet

Nicht belegt.

- Der Exportpfad ist in Dev ein Host-Arbeitsbaum fuer Export-/Build-Werkzeuge.
- Aus dem fehlenden Container-Mount folgt kein unmittelbarer Datenverlust.

### 5.4 `BLS_CORPUS` in Dev als faktisch ungesetzt bewertet

Zu hart.

- In der aktiven App-Laufzeit wird `BLS_CORPUS` durch `dev-start.ps1` und `dev-setup.ps1` explizit gesetzt.
- Korrekt ist nur: die Variable sitzt derzeit in den Dev-Skripten und nicht in einer einheitlichen, eigenstaendig dokumentierten Dev-ENV-Quelle.

### 5.5 Doppelte Dev-Compose als aktuelle Unklarheit bewertet

Inzwischen widerlegt.

- Die aktive Compose-Quelle ist ueber Docker-Labels klar belegt.
- Offen bleibt nur die Bereinigung der redundanten Nebenquelle, nicht die Frage der aktuellen Massgeblichkeit.

## 6. Zielbild fuer die kanonische Finalstruktur

Aus der Kombination von Repo-Finalisierungsplan, Prod-Migrationsdokumentation und beobachteter Dev-Realitaet ergibt sich als belastbares Zielbild:

```text
corapan/
  app/                       # aktives versioniertes App-Repo nach spaeterem Rename
  data/
    blacklab/
      index/
      export/
      backups/
      quarantine/
    public/
    stats_temp/
    db/
    config/                  # runtime-wirksame Konfiguration, wenn Dev=Prod ernst gemeint ist
  media/
  logs/
  maintenance_pipelines/
  docs/
  .github/
  docker-compose.dev-postgres.yml
  scripts/
```

Praezisierung zum derzeit strittigen Konfigurationsort:

- Fuer laufzeitwirksame Dev/Prod-Paritaet ist `data/config` derzeit das staerkere Zielsignal als ein allgemeines Root-`config/`, weil der produktive Zielzustand in den aktuellen Migrations- und Backport-Dokumenten `data/config -> /app/config` belegt.
- Wenn ein zusaetzliches Root-`config/` als authoring- oder staging-Ort beibehalten werden soll, muss das explizit als zweistufiges Modell dokumentiert werden. Ohne diese Entscheidung ist ein Root-`config/` als Endzustand nicht belastbar.

## 7. Empfohlene Reihenfolge fuer die heutige Bereinigung

### Schritt 1: Kanonische Dev-Quellen explizit festziehen

Zuerst festhalten:

- kanonische Dev-Compose: `C:\dev\corapan\docker-compose.dev-postgres.yml`
- kanonische Dev-Einstiegspunkte: `C:\dev\corapan\scripts\dev-start.ps1` und `C:\dev\corapan\scripts\dev-setup.ps1`
- `webapp/docker-compose.dev-postgres.yml` nur noch als Uebergangskopie oder vorbereitende Restdatei klassifizieren

Begruendung:

- Ohne saubere Quellprioritaet bleiben nachfolgende Bereinigungen interpretationsabhaengig.

### Schritt 2: Konfigurations-Source-of-Truth entscheiden

Danach die offene Grundsatzfrage entscheiden:

- runtime-wirksame Konfiguration kuenftig unter `data/config`
- oder bewusst zweistufig: versionierte Quellkonfiguration unter `app/config`, ausgerollte Runtime-Konfiguration unter `data/config`

Begruendung:

- Dieser Punkt blockiert die saubere Bewertung von `config/`, `webapp/config/` und spaeter `app/config/`.
- Vor dieser Entscheidung sollte nichts pauschal geloescht oder verschoben werden.

### Schritt 3: Laufenden BlackLab-Mount an die entschiedene Quelle angleichen

Danach den belegten Drift zwischen laufendem Container und kanonischer Dev-Compose bereinigen.

Begruendung:

- Erst wenn deklarierte Compose und laufender Container dieselbe Quelle nutzen, ist die Dev-Basis fuer weitere Strukturarbeiten belastbar.

### Schritt 4: Hilfsskripte und Checks von Alt-Fallbacks befreien

Dann die echten Restprobleme in Hilfsskripten bereinigen:

- `runtime/corapan`-Fallbacks in Check-/Gate-Skripten entfernen
- offensichtliche `corapan-webapp`-/`webapp`-Altbeispiele dort bereinigen, wo sie keine bewusste Uebergangserkennung mehr darstellen

Begruendung:

- Diese Bereinigung reduziert Fehlinterpretationen vor dem groesseren Repo-Umbau.

### Schritt 5: Erst danach Git-Root auf `corapan/` hochziehen

Begruendung:

- Nach den vorigen Schritten ist klarer, welche Dateien am Root wirklich kanonisch sind und welche nur Hilfskopien waren.

### Schritt 6: `webapp -> app` weiterhin isoliert zuletzt

Begruendung:

- Dieser Schritt bleibt sinnvoll als separater Finalschritt.
- Er sollte erst kommen, wenn Compose, Config, Scripts und Repo-Root bereits konsolidiert sind.

## 8. Go / No-Go fuer den naechsten Umsetzungsschritt

### GO

Die folgenden Strukturarbeiten koennen jetzt direkt gemacht werden:

1. Root-`docker-compose.dev-postgres.yml` explizit als kanonische Dev-Compose festschreiben.
2. `webapp/docker-compose.dev-postgres.yml` als redundant/uebergangsweise markieren und fuer spaetere Entfernung vormerken.
3. Den belegten BlackLab-Config-Drift zwischen laufendem Container und kanonischer Compose bereinigen.
4. Den finalen Runtime-Konfigurationspfad entscheiden und dokumentieren.
5. Echte Legacy-Fallbacks in Check-/Hilfsskripten bereinigen.

### NO-GO

Die folgenden Schritte sollten heute noch nicht gemacht werden:

1. Kein pauschaler grosser Rename `webapp -> app`.
2. Keine blanket-Loeschung aller `webapp`-Pfaderkennungen in Maintenance-Wrappern; ein Teil davon ist aktuell bewusst fuer den Uebergang eingebaut.
3. Kein stilles Festlegen auf Root-`config/` als Endzustand, solange der Konflikt zu `data/config` nicht entschieden ist.
4. Keine pauschale Aussage mehr, Dev sei wegen fehlender Container-Mounts fuer `media/` oder `logs/` generell unbrauchbar; diese Punkte sind fuer die heutige Host-basierte Dev-Laufzeit so nicht belegt.

## Schlussfolgerung

Die korrekte Arbeitsdiagnose fuer Phase 1b lautet nicht mehr "Dev kaputt", sondern:

`Dev laeuft funktional auf einer bewusst eingefuehrten Uebergangsarchitektur, hat aber noch echte Source-of-Truth- und Driftprobleme, die vor Git-Root-Move und vor dem isolierten Rename sauber entschieden werden muessen.`