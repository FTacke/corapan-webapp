# Root Lift Execution

Datum: 2026-03-23

## Was geaendert wurde

- `C:\dev\corapan` wurde als neues einziges Git-Root initialisiert
- die Nested-Repos unter `maintenance_pipelines/` und dem frueheren `webapp/` wurden entkoppelt
- `webapp/` wurde physisch nach `app/` umbenannt
- Root-Compose, Root-Wrapper, Maintenance-Pipelines, Governance-Dateien und aktive App-Helfer wurden auf den neuen Root- und App-Vertrag umgestellt
- die redundante Root-Konfiguration `config/` wurde als Legacy-Snapshot aus dem Arbeitsbaum entfernt und nach `C:\dev\corapan_git_backups\20260323_095902\root_config_legacy` verschoben

## Warum

Die bisherige Struktur hatte drei operative Probleme gleichzeitig:

- getrennte Git-Wahrheiten unter Root, `maintenance_pipelines/` und `webapp/`
- einen final nicht belastbaren Zwischenzustand zwischen `webapp` und `app`
- eine konkurrierende Root-Konfigurationskopie, die bereits gegen `app/config/blacklab` driftete

Der Root-Lift beseitigt diese Mehrfachwahrheiten und bringt die lokale Repo-Struktur in die beabsichtigte Form `corapan/` als Repo-Root mit `app/` als versioniertem Anwendungsteilbaum.

## Operative Wirkung

- Root-Workflows unter `.github/workflows` sind jetzt die aktive versionierte Wahrheit
- der Anwendungscode lebt unter `app/`
- BlackLab-Konfiguration bleibt versioniert unter `app/config/blacklab`
- Runtime-Config bleibt getrennt unter `data/config`
- Maintenance-Pipelines gehoeren jetzt zum selben Root-Repo wie die App- und Governance-Dateien

## Kompatibilitaet und Grenzen

- kein Push wurde in diesem Lauf ausgefuehrt
- Legacy-History bleibt ueber die Remotes `legacy-webapp` und `legacy-maintenance` nachvollziehbar
- fuer den ersten echten Push des neuen Root-Repos ist weiterhin eine explizite `origin`-Festlegung erforderlich
