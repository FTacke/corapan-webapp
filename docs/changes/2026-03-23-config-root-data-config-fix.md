# CONFIG_ROOT data/config fix

Datum: 2026-03-23

## Was geaendert wurde

- `app/src/app/runtime_paths.py` leitet `CONFIG_ROOT` jetzt aus `DATA_ROOT / config` statt aus `CORAPAN_RUNTIME_ROOT / config` ab
- damit folgt die aktive Runtime-Config-Aufloesung jetzt dem kanonischen Root-Lift-Vertrag `data/config`
- der Fix wurde in `docs/repo_finish/phase_6b_config_root_fix.md` dokumentiert

## Warum

Im Phase-6-Review-Branch-Check zeigte der reale Dev-App-Start einen Widerspruch zwischen Dokumentation und aktivem Code:

- dokumentiert war `data/config` als kanonischer Runtime-Web-Config-Pfad
- aktiv wurde aber `C:\dev\corapan\config` aufgeloest

Da der Root-`config/`-Baum bewusst nicht mehr aktiv ist, war das ein echter Architekturfehler vor jedem weiteren Push.

## Operative Wirkung

- Dev mit `CORAPAN_RUNTIME_ROOT=C:\dev\corapan` loest `CONFIG_ROOT` jetzt zu `C:\dev\corapan\data\config` auf
- der aktive Runtime-Pfad ist damit konsistent mit Root-README, Repo-Finish-Dokumentation und dem vorbereiteten Dateibaum
- es gibt keinen impliziten Zugriff mehr auf den nicht-kanonischen Root-Pfad `C:\dev\corapan\config`

## Kompatibilitaet und Grenzen

- `CORAPAN_RUNTIME_ROOT` bleibt weiterhin der Workspace-Root
- `app/config/blacklab` bleibt die getrennte versionierte BlackLab-Konfiguration
- historische/forensische Dokumente mit alten Zwischenstaenden bleiben bestehen und werden nicht als operative Wahrheit behandelt