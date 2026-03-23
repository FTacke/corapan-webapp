# Phase 4 - Root Lift Execution

Datum: 2026-03-23
Workspace: `C:\dev\corapan`
Ausfuehrungsmodus: kontrollierte lokale Migration ohne Push

## Ergebnis

Phase 4 wurde lokal erfolgreich ausgefuehrt.

- `C:\dev\corapan` ist jetzt das einzige aktive Git-Root.
- `C:\dev\corapan\webapp` wurde nach `C:\dev\corapan\app` umbenannt.
- `maintenance_pipelines` ist aus dem Nested-Git-Zustand geloest und Teil des Root-Repos.
- aktive Root-, App-, Maintenance- und Governance-Pfade zeigen jetzt auf `app/` statt auf `webapp/`.
- die redundante Root-Konfigurationskopie `C:\dev\corapan\config` wurde als Legacy-Snapshot ausgelagert.

## Ausgefuehrte Git-Schritte

Die Migration wurde nicht per `git subtree` ausgefuehrt, weil `git subtree` in der lokalen Umgebung nicht verfuegbar war. Stattdessen wurde History-Sicherung vor der Entkopplung vorgenommen.

### 1. Zustand der Nested-Repos verifiziert

Vor dem Umbau wurden Branch, Status, Remotes und letzte Commits der beiden bisherigen Repos geprueft:

- `C:\dev\corapan\webapp\.git`
- `C:\dev\corapan\maintenance_pipelines\.git`

### 2. Bare-Mirror-Backups erzeugt

Externe Mirror-Backups wurden erstellt unter:

- `C:\dev\corapan_git_backups\20260323_095902\webapp.git`
- `C:\dev\corapan_git_backups\20260323_095902\maintenance_pipelines.git`

### 3. Nested `.git` entkoppelt

Die bisherigen Nested-Git-Verzeichnisse wurden aus den Arbeitsbaeumen entfernt und in den Backup-Kontext ueberfuehrt:

- `C:\dev\corapan\webapp\.git`
- `C:\dev\corapan\maintenance_pipelines\.git`

### 4. Neues Root-Repo initialisiert

Aktives Git-Root ist jetzt:

- `C:\dev\corapan\.git`

Legacy-History wurde im neuen Root-Repo als Remote verfuegbar gemacht:

- `legacy-webapp -> C:\dev\corapan_git_backups\20260323_095902\webapp.git`
- `legacy-maintenance -> C:\dev\corapan_git_backups\20260323_095902\maintenance_pipelines.git`

### 5. Physischer Rename

Der bisherige App-Baum wurde umbenannt:

- vorher: `C:\dev\corapan\webapp`
- nachher: `C:\dev\corapan\app`

## Struktur- und Pfad-Aenderungen

### Finaler Zielzustand

```text
corapan/
  .github/
  app/
  data/
  docs/
  maintenance_pipelines/
  media/
  scripts/
  .gitignore
  .python-version
  README.md
  docker-compose.dev-postgres.yml
```

### Explizite Pfad-Aenderungen

- `webapp/` wurde zu `app/`.
- Root-Compose mountet jetzt `./app:/app:ro`.
- Root-Compose mountet jetzt `./app/config/blacklab:/etc/blacklab:ro`.
- Root-Wrapper unter `scripts/` loesen nur noch `app/` auf.
- Maintenance-Resolver unter `maintenance_pipelines/` loesen standardmaessig nur noch `app/` auf.
- Root-`config/` wurde nicht weiter als konkurrierender Pfad behalten, sondern als Legacy-Snapshot ausgelagert nach `C:\dev\corapan_git_backups\20260323_095902\root_config_legacy`.
- das leere App-Artefakt `app/.github` wurde ausgelagert nach `C:\dev\corapan_git_backups\20260323_095902\app_dot_github_empty`.

## Genau geaenderte Dateien

### Root-Wrapper und Root-Compose

- `scripts/dev-start.ps1`
- `scripts/dev-setup.ps1`
- `scripts/blacklab/start_blacklab_docker_v3.ps1`
- `scripts/blacklab/build_blacklab_index.ps1`
- `scripts/blacklab/migrate_legacy_blacklab_dev_layout.ps1`
- `scripts/blacklab/run_export.py`
- `docker-compose.dev-postgres.yml`

### Maintenance-Pipelines

- `maintenance_pipelines/_1_blacklab/blacklab_export.py`
- `maintenance_pipelines/_2_deploy/publish_blacklab.ps1`
- `maintenance_pipelines/_2_deploy/deploy_data.ps1`
- `maintenance_pipelines/_2_deploy/deploy_media.ps1`

### App-Implementierung und operative Helfer

- `app/scripts/dev-start.ps1`
- `app/scripts/dev-setup.ps1`
- `app/scripts/blacklab/start_blacklab_docker_v3.ps1`
- `app/scripts/blacklab/build_blacklab_index.ps1`
- `app/scripts/blacklab/build_blacklab_index.sh`
- `app/scripts/blacklab/run_export.py`
- `app/scripts/blacklab/migrate_legacy_blacklab_dev_layout.ps1`
- `app/src/scripts/blacklab_index_creation.py`
- `app/startme.md`

### Root-Governance und Agent-Kontext

- `.github/workflows/README.md`
- `.github/instructions/backend.instructions.md`
- `.github/instructions/database.instructions.md`
- `.github/instructions/devops.instructions.md`
- `.github/skills/config-validation/SKILL.md`
- `.github/skills/maintenance-script/SKILL.md`
- `.github/skills/blacklab-operational-safety/SKILL.md`
- `.github/copilot-instructions.md`
- `.github/agents/corapan-code-agent.agent.md`
- `.github/agents/lessons-integrated-2026-03-21.md`

### Root-Dokumentation

- `README.md`
- `.gitignore`
- `docs/repo_finish/repo_finish.md`
- `docs/repo_finish/phase_3_root_lift_pre_push.md`
- `docs/repo_finish/phase_4_root_lift_execution.md`
- `docs/changes/2026-03-23-root-lift-execution.md`

### Entfernte oder ausgelagerte doppelte Artefakte

Entfernt aus dem App-Baum:

- `app/.github/workflows/ci.yml`
- `app/.github/workflows/deploy.yml`
- `app/.github/workflows/md3-lint.yml`
- `app/.gitignore`
- `app/.python-version`

Ausgelagert in den Backup-Snapshot:

- `config/`
- `app/.github/`

## Verifikation

### Compose-Aufloesung

Root-Compose wurde erfolgreich gerendert. Relevante Mounts:

- `C:\dev\corapan\app -> /app`
- `C:\dev\corapan\app\config\blacklab -> /etc/blacklab`

App-Compose unter `app/docker-compose.dev-postgres.yml` wurde ebenfalls erfolgreich gerendert und loest intern korrekt auf `app/config/blacklab` auf.

### Aktive Referenzbereinigung

Gezielte Suche nach aktiven `webapp`-Vertragsannahmen in Root-Governance, Root-Skripten, Maintenance-Pipelines und App-Skripten ergab keine verbleibenden operativen Treffer mehr. Uebrig blieben nur historische oder erklaerende Doku-Hinweise.

### Drift-Kontrolle Root-Config

Die bisherige Root-Konfiguration `config/blacklab` wurde vor der Auslagerung gegen `app/config/blacklab` gehasht. Dabei zeigte `blacklab-server.yaml` einen inhaltlichen Drift. Deshalb wurde der Root-Baum nicht still weitergefuehrt, sondern als Legacy-Snapshot aus dem Arbeitsbaum entfernt.

## Push-Freigabe

### Entscheidung: NO-GO fuer direkten Push in diesem Lauf

Begruendung:

- das neue Root-Repo hat absichtlich noch keinen kanonischen `origin`
- die einzige vorhandene Remote-Konfiguration besteht aus History-Backups (`legacy-webapp`, `legacy-maintenance`)
- der erste Push nach diesem Root-Lift ist ein bewusst zu entscheidender Veroeffentlichungsschritt und darf nicht auf eine erratene Ziel-Remote gehen

### Lokaler Zustand

Lokal ist die Migration ausfuehrbar, konsistent und commit-faehig. Ein spaeterer Push ist erst dann GO, wenn die Ziel-Remote fuer das neue Root-Repo explizit festgelegt und die erste Publish-Strategie bewusst bestaetigt wurde.

## Offene Restpunkte nach Phase 4

Keine strukturellen Restblocker innerhalb des lokalen Arbeitsbaums.

Vor einem echten Push fehlt nur noch die bewusste Festlegung von:

- kanonischer Root-Remote
- Branch- und Erstpublikationsstrategie fuer das neue Root-Repo
