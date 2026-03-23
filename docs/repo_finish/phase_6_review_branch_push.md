# Phase 6 - Review Branch Push

Datum: 2026-03-23
Workspace: `C:\dev\corapan`
Modus: kontrollierter Review-Branch-Run ohne Push nach `main`, ohne Deploy

## 1. Kurzurteil

Der Review-Branch-Push wurde in diesem Run **nicht** ausgefuehrt.

Grund ist ein echter Vor-Push-Widerspruch im aktiven Dev-/Runtime-Vertrag:

- die Repo-Dokumentation und die Root-Lift-Freigabedokumente klassifizieren `data/config` als kanonischen Runtime-Web-Config-Pfad
- der aktive Dev-Startpfad setzt `CORAPAN_RUNTIME_ROOT` auf den Workspace-Root `C:\dev\corapan`
- der aktive App-Config-Code loest `CONFIG_ROOT` daraus als `CORAPAN_RUNTIME_ROOT/config` auf, also aktuell zu `C:\dev\corapan\config`
- `C:\dev\corapan\config` existiert im Arbeitsbaum bewusst **nicht** mehr
- vorhanden ist stattdessen `C:\dev\corapan\data\config`

Nach der vereinbarten Regel fuer diesen Run gilt deshalb: stoppen, dokumentieren, kein Push.

## 2. Lokaler Zustand vor Push

### Git-Zustand

Geprueft wurden:

- aktueller Branch
- `git status`
- Upstream-Konfiguration
- Remotes

Ergebnis:

- lokaler Branch: `main`
- Upstream: keiner gesetzt
- Remotes:
  - `origin = git@github.com:FTacke/corapan-webapp.git`
  - `legacy-webapp = C:\dev\corapan_git_backups\20260323_095902\webapp.git`

Arbeitsbaum vor einem moeglichen Review-Branch-Push:

- modifiziert:
  - `.github/workflows/deploy.yml`
  - `README.md`
  - `app/README.md`
  - `app/scripts/deploy_prod.sh`
- untracked:
  - `docs/changes/2026-03-23-phase-5-final-pre-push-check.md`
  - `docs/repo_finish/phase_5_final_pre_push_check.md`

Bewertung:

- der Arbeitsbaum war **nicht** push-bereit
- es lag ein sinnvoll zusammenhaengender, aber noch uncommitteter Dokumentations-/Deploy-Hinweis-Stand vor
- vor einem Branch-Push waere daher ohnehin zunaechst ein bewusster Commit erforderlich gewesen

### Repo-Struktur

Geprueft wurden:

- Git-Root
- Vorhandensein von `app/`
- Abwesenheit von `webapp/` als aktivem App-Ordner
- `maintenance_pipelines` als normales Unterverzeichnis
- Nested-Git-Indikatoren

Ergebnis:

- Git-Root: `C:\dev\corapan`
- `app/`: vorhanden
- `webapp/`: nicht vorhanden
- `maintenance_pipelines/`: normales Unterverzeichnis vorhanden
- `app/.git`: nicht vorhanden
- `maintenance_pipelines/.git`: nicht vorhanden
- `.gitmodules`: nicht vorhanden
- keine Gitlinks/Submodule belegt

Bewertung:

- die Repo-Struktur bleibt fuer den Root-Lift-Zielzustand sauber
- der Push-Stop kommt **nicht** aus Git-Strukturproblemen

## 3. Dev- und Struktur-Checks

### Operative Kernpfade

Geprueft wurden:

- `README.md`
- `app/README.md`
- `.gitignore`
- `.github/`
- `docker-compose.dev-postgres.yml`
- `app/config/blacklab`
- `data/config`

Ergebnis:

- alle geforderten Pfade/Artefakte sind vorhanden
- `data/config` ist vorhanden
- ein Root-`config/`-Baum ist **nicht** vorhanden

### Compose-Check

Geprueft wurde der kanonische lokale Dev-Stack:

- `docker compose -f docker-compose.dev-postgres.yml config`

Ergebnis:

- die Compose-Datei rendert sauber
- Dev-Mounts zeigen auf:
  - `C:\dev\corapan\data\blacklab\index -> /data/index/corapan`
  - `C:\dev\corapan\app\config\blacklab -> /etc/blacklab`
  - `C:\dev\corapan\data\db\restricted\postgres_dev -> /var/lib/postgresql/data`
  - `C:\dev\corapan\app -> /app`

Bewertung:

- der Root-Dev-Compose ist formal und strukturell plausibel

### Dev-Einstiegspfade

Geprueft wurden:

- `scripts/dev-setup.ps1`
- `scripts/dev-start.ps1`
- `app/scripts/dev-start.ps1`
- `app/src/app/runtime_paths.py`
- `app/src/app/config/__init__.py`

Beobachtete aktive Aufloesung:

1. Root-Wrapper verweisen korrekt auf `app/scripts/...`
2. `app/scripts/dev-start.ps1` setzt im Dev-Fall `CORAPAN_RUNTIME_ROOT = C:\dev\corapan`
3. `app/src/app/runtime_paths.py` definiert `get_config_root()` als `get_runtime_root() / "config"`
4. damit wird `CONFIG_ROOT` im Dev-Fall zu `C:\dev\corapan\config`

### Kurzer realer App-Check

Es wurde **kein** Server gestartet und **kein** Deploy ausgefuehrt.

Stattdessen wurde ein minimaler App-Factory-Check mit den kanonischen Dev-Variablen ausgefuehrt:

- `FLASK_ENV=development`
- `CORAPAN_RUNTIME_ROOT=C:\dev\corapan`
- `CORAPAN_MEDIA_ROOT=C:\dev\corapan\media`
- `AUTH_DATABASE_URL=postgresql+psycopg2://corapan_auth:corapan_auth@127.0.0.1:54320/corapan_auth`
- `BLS_BASE_URL=http://localhost:8081/blacklab-server`
- `BLS_CORPUS=corapan`

Ergebnis:

- `create_app('development')` lief erfolgreich an
- Auth-DB-Verbindung wurde erfolgreich verifiziert
- dabei wurde zur Laufzeit geloggt:
  - `RUNTIME_ROOT=C:\dev\corapan`
  - `CONFIG_ROOT=C:\dev\corapan\config`
  - `MEDIA_ROOT=C:\dev\corapan\media`
  - `DOCMETA_PATH=C:\dev\corapan\data\blacklab\export\docmeta.jsonl`

### Klassifikation des Widerspruchs

Nach der geforderten Pruefreihenfolge:

1. live beobachtbare Dev-Laufzeit: `CONFIG_ROOT = C:\dev\corapan\config`
2. aktive Dev-Startskripte: setzen `CORAPAN_RUNTIME_ROOT = C:\dev\corapan`
3. aktiver Config-Code: `get_config_root() = CORAPAN_RUNTIME_ROOT/config`
4. Dokumentation: `data/config` als kanonischer Runtime-Web-Config-Pfad

Klassifikation:

- `C:\dev\corapan\config`: **aktiv im Dev-Codepfad, aber im Arbeitsbaum fehlend und damit gefaehrlich**
- `C:\dev\corapan\data\config`: **dokumentierter/strukturell vorbereiteter Zielpfad, aber aktuell nicht der gewinnende Dev-Codepfad**
- Root-README und Repo-Finish-Dokumente, die `data/config` als aktuelle Wahrheit behandeln: **derzeit fuer Dev nicht belastbar genug**

Folgerung:

- das ist ein echter Source-of-Truth-Konflikt in einem operativen Kernpfad
- damit ist die Vorbedingung fuer einen sicheren Review-Branch-Push nicht erfuellt

## 4. Branch- und Commit-Zustand

### Review-Branch-Existenz

Geprueft wurde:

- lokaler Branch `root-lift-review`
- Remote-Branch `origin/root-lift-review`

Ergebnis:

- lokal nicht vorhanden
- remote nicht vorhanden

### Commit-Lage

Lokaler Commit-Stand relativ zu `origin/main`:

- `origin/main` = `9c819e6`
- lokaler `main`-Stand = `93e0e1a`
- lokale Root-Lift-Spitze besteht weiterhin aus:
  - `50f8d20` - Finalize root lift and app rename
  - `93e0e1a` - Finalize phase 4b cleanup and push readiness

Zusatz:

- die Phase-5-Aenderungen sind noch **nicht committed**
- in diesem Run entstand **kein** neuer Commit

Bewertung:

- branch-technisch waere `root-lift-review` leicht anlegbar
- commit-seitig ist der Stand noch nicht sauber versandfertig
- unabhaengig davon blockiert der oben festgestellte Pfadkonflikt den Push

## 5. Push auf `root-lift-review`

### Geplanter Push

```bash
git push -u origin HEAD:root-lift-review
```

### Tatsaechlicher Status

- Push **nicht ausgefuehrt**
- kein Review-Branch angelegt
- kein Remote-Branch erzeugt
- `main` unveraendert
- kein Deploy ausgeloest

Begruendung fuer den Abbruch:

- echter Dev-/Runtime-Pfadkonflikt bei `CONFIG_ROOT`
- zusaetzlich noch uncommitteter Arbeitsbaum

## 6. Remote-/GitHub-Sicht nach Push

Da kein Push erfolgte, ergibt sich lokal/technisch folgende Remote-Sicht:

- `origin/main` blieb unveraendert
- `origin/root-lift-review` existiert weiterhin nicht
- es gab keine Hinweise auf serverseitige Hooks oder Remote-Probleme, weil kein Push stattgefunden hat
- es wurde kein Pull-Request-Hinweis erzeugt

Bewertung:

- fuer einen spaeteren PR `root-lift-review -> main` ist die Git-Historie weiter geeignet
- vor einem solchen Branch-Push muss aber zunaechst der Runtime-Config-Widerspruch aufgeloest werden

## 7. CI-/Workflow-Bewertung

Maßgeblich fuer diesen Run war nicht CI-Gruenheit, sondern die sichere Review-Branch-Stufe ohne Deploy.

Relevante Workflow-Sicht:

- `deploy.yml` bleibt produktiv relevant fuer `push -> main`
- der spaetere Merge nach `main` waere daher weiterhin ein bewusster Deploy-Schritt
- der geplante Review-Branch-Push haette **keinen** produktiven Deploy ausloesen sollen
- ein spaeterer Pull Request `root-lift-review -> main` bleibt die richtige Review-Richtung

Bekannter Zustand:

- CI ist seit laengerem nicht verlässlich gruen und wurde hier **nicht** als primaeres Freigabekriterium behandelt

Aktuelle Bewertung:

- CI ist in diesem Run nicht der Blocker
- Blocker ist der aktive Dev-/Runtime-Source-of-Truth-Konflikt

## 8. Merge-Vorbereitung fuer `main`

Empfohlene spaetere PR-Richtung bleibt:

- `root-lift-review -> main`

Vor einem spaeteren Merge nach `main` muss jetzt zuerst manuell geprueft bzw. bereinigt werden:

1. `CONFIG_ROOT`-Vertrag zwischen Dev-Skripten, Runtime-Code und Dokumentation vereinheitlichen
2. explizit entscheiden, ob der kanonische Web-Config-Pfad in Dev `CORAPAN/data/config` oder `CORAPAN/config` sein soll
3. den nicht gewaehlten Pfad danach als legacy/dangerous klassifizieren und nicht weiter als aktuelle Wahrheit darstellen
4. danach den Arbeitsbaum in einen bewussten Commit-Zustand bringen
5. erst dann `root-lift-review` anlegen und pushen

Bekannt, aber fuer den spaeteren Merge nicht primaer blockierend:

- CI ist historisch unzuverlaessig
- der Review-Branch existiert noch nicht
- der aktuelle Arbeitsbaum enthaelt noch uncommittete Phase-5-Aenderungen

Wirklich merge-blockierend:

- ein ungelöster aktiver Widerspruch in Runtime-/Config-Pfaden
- jeder Zustand, in dem `push -> main` den Deploy ausloest, ohne dass vorher klar ist, welcher Config-Pfad in Dev und Doku wirklich gilt

## 9. Go / No-Go

### NO-GO

Begruendung:

- Review-Branch-Push wurde bewusst gestoppt, weil ein real beobachtbarer Konfigurationspfad dem dokumentierten Root-Lift-Vertrag widerspricht
- der Konflikt betrifft einen operativen Kernpfad und nicht nur eine Randdoku
- zusaetzlich war der lokale Stand noch nicht committet

### VORLAEUFIGE MERGE-EINSCHAETZUNG FUER MAIN

noch nicht merge-bereit wegen des ungeklärten `CONFIG_ROOT`-Vertrags zwischen Dev-Codepfad und dokumentierter Runtime-Struktur

## Zusatz - exakte Laufdaten dieses Runs

- lokal verwendeter Branch: `main`
- gepushte Commits: keine
- neue Commits in diesem Run: keine
- Unerwartetes Ereignis: ja
  - `CONFIG_ROOT` wurde im realen Dev-App-Check zu `C:\dev\corapan\config` aufgeloest, obwohl `data/config` als kanonischer Runtime-Config-Pfad dokumentiert und vorbereitet ist
- vor spaeterem Merge nach `main` manuell zu pruefen:
  - Entscheidung und Bereinigung des kanonischen Web-Config-Pfads
  - danach bewusster Commit des Arbeitsbaums
  - erst anschliessend Push auf `root-lift-review`