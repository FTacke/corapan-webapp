# Phase 4b - Cleanup and Push Readiness

Datum: 2026-03-23
Workspace: `C:\dev\corapan`
Modus: lokaler Cleanup- und Verifikationslauf ohne Push, ohne Deploy

## 1. Kurzurteil

Der Root-Lift ist technisch sauber.

- Es gibt genau ein aktives Git-Root: `C:\dev\corapan\.git`.
- `maintenance_pipelines` ist **kein** eigenes Git-Repo mehr.
- Es existieren keine `.gitmodules`, keine Gitlinks und keine `.git`-Reste unter `app/` oder `maintenance_pipelines/`.
- Der nicht-kanonische Root-`config/`-Baum ist weiterhin nicht im Arbeitsbaum vorhanden.
- Root-README und zentrale operative Dokumentation wurden auf den erreichten Endzustand gebracht.

Bewertung fuer den naechsten Schritt:

### GO FUER FINALEN PRE-PUSH-CHECK

Noch **nicht** freigegeben ist ein echter Push. Vor dem Push fehlt weiterhin die bewusste Festlegung der kanonischen Root-Remote und der Erstpublikationsstrategie.

## 2. Nested-Git / maintenance_pipelines Pruefung

### Technische Pruefung

Geprueft wurden:

- `C:\dev\corapan\maintenance_pipelines\.git`
- `git -C C:\dev\corapan status`
- `git -C C:\dev\corapan\maintenance_pipelines status`
- `git -C C:\dev\corapan\maintenance_pipelines rev-parse --show-toplevel`
- `git -C C:\dev\corapan\maintenance_pipelines rev-parse --git-dir`

### Ergebnis

- Unter `C:\dev\corapan\maintenance_pipelines\.git` existiert **nichts**.
- `git -C C:\dev\corapan\maintenance_pipelines rev-parse --show-toplevel` liefert `C:/dev/corapan`.
- `git -C C:\dev\corapan\maintenance_pipelines rev-parse --git-dir` liefert `C:/dev/corapan/.git`.

Damit ist technisch eindeutig belegt:

- `maintenance_pipelines` ist ein Unterbaum des Root-Repos
- `maintenance_pipelines` ist **kein** eigenes Repo
- eine separate SCM-Anzeige in VS Code waere damit kein Dateisystem- oder Git-Zustand, sondern hoechstens ein Editor-/Workspace-Artefakt oder Cache-Effekt

### Bereinigung

Keine weiteren Nested-Git-Dateien mussten in `maintenance_pipelines/` entfernt werden, weil dort keine `.git`-Datei, kein `.git`-Ordner und kein Gitfile mit `gitdir:` mehr vorhanden war.

## 3. Weitere Repo-Reste / Git-Reste

### Geprueft

- rekursive Suche nach `.git`-Eintraegen im gesamten Workspace
- Root-`.gitmodules`
- Gitlinks ueber `git ls-files --stage` mit Modus `160000`
- Git-Aufloesung aus `app/` und `maintenance_pipelines/`

### Ergebnis

Gefunden wurde genau ein `.git`:

- `C:\dev\corapan\.git`

Nicht gefunden wurden:

- `.gitmodules`
- Gitlinks / Submodule im Index
- `.git`-Artefakte unter `app/`
- `.git`-Artefakte unter `maintenance_pipelines/`
- Reparse-Point-/Link-Konstruktionen als Git-Ersatz

### Entscheidung

Der Zustand ist repo-seitig sauber: exakt ein aktives Git-Root, keine Nested-Git-Reste.

## 4. Root-Config / Legacy-Bereinigung

### Geprueft

- Existenz von `C:\dev\corapan\config`
- aktive Referenzen auf einen Root-`config/`-Baum in operativen Dateien

### Ergebnis

- `C:\dev\corapan\config` existiert nicht mehr im Arbeitsbaum.
- Der Legacy-Baum wurde bereits in Phase 4 in den Backup-Bereich ausgelagert und ist dort dokumentiert.
- Im aktuellen Arbeitsbaum gibt es keinen konkurrierenden Root-Config-Pfad mehr.

### Klassifikation

- `data/config` = aktiv fuer Runtime-Web-Config
- `app/config/blacklab` = aktiv fuer versionierte BlackLab-Konfiguration
- ehemaliges Root-`config/` = Legacy/Drift, nicht mehr aktiv im Arbeitsbaum

## 5. Root-README / App-README Bewertung und Aenderungen

### Ausgangslage

Die bisherige Root-README beschrieb den Root-Lift noch als laufende Transition. Damit repraesentierte sie das GitHub-Repo nach dem Root-Lift nicht mehr korrekt.

Die App-README enthielt weiterhin:

- alte Repo-Namen (`corapan-webapp`)
- veraltete Runtime-Pfade
- veraltete Deploy-Hinweise
- Root-vs-App-Abgrenzung nur unzureichend

### Entscheidung zur README-Struktur

#### Root-README muss enthalten

- Projektzweck und fachliche Mission
- Gesamtueberblick ueber Repository und System
- Root-vs-App-Trennung
- Runtime-/Deploy-Grundsaetze
- Verweise auf `app/README.md` fuer App-Details

#### App-README bleibt zustaendig fuer

- App-Features
- detaillierten Tech-Stack
- app-spezifische Setup- und Entwicklungsdetails
- app-spezifische Hinweise zu Deployment und BlackLab innerhalb des Anwendungsteils

### Umgesetzte Aenderungen

- Root-README wurde von einer Uebergangs-README zu einer echten Repository-README umgeschrieben.
- App-README wurde auf die neue Root-/App-Struktur ausgerichtet.
- zentrale Pfad- und Deploy-Angaben in der App-README wurden auf den post-root-lift Vertrag gebracht.

### Ergebnis

Das Root-Repo repraesentiert das Gesamtprojekt jetzt sinnvoll, ohne die technische Trennschaerfe zwischen Root-Ebene und `app/` zu verlieren.

## 6. Root-Artefakte

### Gepruefte Root-Artefakte

Vorhanden und plausibel:

- `README.md`
- `.gitignore`
- `.github/`
- `docker-compose.dev-postgres.yml`
- `scripts/`
- `docs/`
- `maintenance_pipelines/`
- `app/`
- `.python-version`

### Bewertung von `.python-version`

`.python-version` im Root ist sinnvoll und bewusst beibehalten.

Begruendung:

- die lokale `.venv` liegt am Root
- die kanonischen Dev-Einstiegsskripte liegen am Root
- die Python-Version soll fuer das Workspace-Setup gelten, nicht nur fuer `app/`

### `.gitignore`

Die Root-`.gitignore` wurde auf den neuen Zustand bereinigt:

- alte `webapp/*`-Ignore-Regeln wurden entfernt
- Root-Ignore-Verhalten fuer Runtime-, Cache- und Secret-Dateien bleibt passend zum neuen Root-Repo

## 7. Aktive Altpfad-Referenzen

### Direkt gefixte operative Funde

1. `maintenance_pipelines/_0_json/05_publish_corpus_statistics.py`
   - Problem: Root-Erkennung akzeptierte noch nur `corapan-webapp`
   - Risiko: Script waere nach Root-Lift funktional gebrochen
   - Fix: auf Workspace-Root mit `app/`, `maintenance_pipelines/` und `docs/` umgestellt
   - Push-blockierend: ja

2. `README.md`
   - Problem: beschrieb Root-Lift noch als laufende Transition
   - Risiko: Root-Repo falsch dargestellt
   - Fix: komplett auf finalen Root-Vertrag umgestellt
   - Push-blockierend: ja

3. `app/README.md`
   - Problem: alte Repo-, Runtime- und Deploy-Annahmen
   - Risiko: irrefuehrende App-Dokumentation im neuen Root-Repo
   - Fix: Root-vs-App geklaert, Setup/Deploy/Docs-Pfade korrigiert
   - Push-blockierend: mittel, fuer Repo-Repraesentation ja

4. `docs/operations/local-dev.md`
   - Problem: `webapp/`-Layout und `LOKAL/`-Pfade
   - Risiko: falsche lokale Startanweisungen
   - Fix: auf Root-Workspace und `maintenance_pipelines/` umgestellt
   - Push-blockierend: nein, aber operativ irrefuehrend

5. `docs/operations/production.md`
   - Problem: veraltete Prod-Pfade und Compose-Annahmen
   - Risiko: falsche Betriebsdokumentation
   - Fix: an `app/infra/docker-compose.prod.yml` und `app/scripts/deploy_prod.sh` angeglichen
   - Push-blockierend: nein, aber stark operativ relevant

6. `docs/operations/runtime_statistics_deploy.md`
   - Problem: veraltete Runtime- und `LOKAL/`-Pfade
   - Risiko: falsche Statistik-Deploy-Anleitung
   - Fix: auf Root-Workspace und `/srv/webapps/corapan/data/public/statistics` umgestellt
   - Push-blockierend: nein

7. `maintenance_pipelines/_2_deploy/README.md`
   - Problem: alte `LOKAL/`- und `WebappRepoPath`-Beispiele
   - Risiko: irrefuehrende Orchestrator-Doku
   - Fix: auf `maintenance_pipelines/` und `AppRepoPath` umgestellt
   - Push-blockierend: nein

8. `app/scripts/dev-start.ps1`
   - Problem: Benutzerhinweise zeigten noch `LOKAL/_0_json/...`
   - Risiko: falsche Sofortanweisung im aktiven Dev-Start
   - Fix: auf `maintenance_pipelines/_0_json/...` umgestellt
   - Push-blockierend: nein

### Verbleibende nicht-blockierende Reste

Es bleiben nur noch folgende Klassen von Treffern:

- historische oder bewusst erklaerende Hinweise, z. B. `.github/workflows/README.md`
- ignorierte generierte Artefakte, z. B. `maintenance_pipelines/_0_json/99_check_pipeline_report.json`
- Legacy-Kommentar- oder Beispieltexte in Skripten, die keinen aktiven Pfadvertrag steuern
- Skill-/Agent-Beschreibungen mit dem alten Repo-Namen `corapan-webapp`

Diese Funde verfälschen nicht den aktuellen Git- oder Deploy-Zustand und sind fuer den naechsten finalen Pre-Push-Check nicht blockierend.

## 8. Verbleibende Blocker

### Keine strukturellen Blocker innerhalb des Repos

Nicht mehr offen sind:

- Nested-Git-Bereinigung
- Root-`config/`-Bereinigung
- Root-vs-App-Dokumentation
- Maintenance-Integration in das Root-Repo

### Vor einem echten Push noch offen

- Festlegung der kanonischen Root-Remote (`origin`)
- bewusste Entscheidung ueber die Erstpublikationsstrategie des neuen Root-Repos
- finaler Pre-Push-Check gegen die zu waehlende Ziel-Remote

## 9. Go / No-Go fuer finalen Pre-Push-Check

### GO FUER FINALEN PRE-PUSH-CHECK

Begruendung:

- Repo ist strukturell sauber
- genau ein Git-Root ist aktiv
- `maintenance_pipelines` ist sauber integriert
- kein Root-`config/`-Rest mehr im Arbeitsbaum
- Root-Dokumentation repraesentiert das GitHub-Repo jetzt sinnvoll
- verbleibende Altpfad-Treffer sind historisch, erklaerend oder nicht-blockierend

Ein echter Push bleibt weiterhin **nicht** freigegeben, solange Root-Remote und Erstpublikationsstrategie nicht explizit festgelegt wurden.

## Exakte Aenderungen

### Geaenderte Dateien

- `README.md`
- `.gitignore`
- `app/README.md`
- `app/scripts/deploy_sync/README.md`
- `app/scripts/dev-start.ps1`
- `docs/operations/blacklab_dev_health.md`
- `docs/operations/local-dev.md`
- `docs/operations/production.md`
- `docs/operations/runtime_statistics_deploy.md`
- `maintenance_pipelines/_0_json/05_publish_corpus_statistics.py`
- `maintenance_pipelines/_2_deploy/README.md`
- `maintenance_pipelines/_2_deploy/README_STATISTICS_DEPLOY.md`
- `maintenance_pipelines/_2_deploy/deploy_data.ps1`
- `maintenance_pipelines/_2_deploy/deploy_media.ps1`
- `docs/repo_finish/phase_4b_cleanup_and_push_readiness.md`
- `docs/changes/2026-03-23-phase-4b-cleanup-and-push-readiness.md`

### Entfernte oder bestaetigt nicht mehr vorhandene Altpfade / Git-Reste

- kein `maintenance_pipelines/.git`
- kein `app/.git`
- keine `.gitmodules`
- keine Gitlinks im Root-Index
- kein Root-`config/` im Arbeitsbaum
- alte `webapp/*`-Ignore-Regeln aus Root-`.gitignore` entfernt

### README-Entscheidungen

- Root-README ist jetzt Projekt- und Repo-README fuer das Gesamtvorhaben
- App-README bleibt technische Dokumentation des Anwendungsteils `app/`
- keine Volltextduplikation zwischen Root- und App-Ebene
- Root verweist auf `app/README.md`, App verweist auf Root-README und Root-Doku

### Vor dem echten Push noch offen

- neue kanonische Root-Remote setzen
- Push-Ziel und Branch-Strategie explizit festlegen
- danach letzten echten Pre-Push-Check gegen diese Remote ausfuehren
