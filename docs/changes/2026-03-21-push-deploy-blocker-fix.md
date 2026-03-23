# Push/Deploy Blocker Fix

Datum: 2026-03-21
Umgebung: `webapp/.git` als echtes Repo, Deploy nach `/srv/webapps/corapan/app`

## Was geaendert wurde

Hinweis 2026-03-23:

- die damalige Zwischenkorrektur fuer `CONFIG_ROOT` ist durch den spaeter verifizierten Root-Lift-Zielzustand ersetzt
- aktueller kanonischer Vertrag ist `CORAPAN_RUNTIME_ROOT/data/config`, dokumentiert in `docs/repo_finish/phase_6b_config_root_fix.md`

- die geloeschten Repo-Workflows unter `.github/workflows/` wurden im echten Repo wiederhergestellt
- die geloeschten BlackLab-Konfigurationsdateien unter `config/blacklab/` wurden im echten Repo wiederhergestellt
- `src/app/runtime_paths.py` wurde so korrigiert, dass `CONFIG_ROOT` wieder aus `CORAPAN_RUNTIME_ROOT/config` abgeleitet wird

## Warum

Die vorherige Push-Freigabepruefung hatte drei harte Blocker bestaetigt:

- Deploy-/CI-Workflows waeren aus dem echten Repo entfernt worden
- produktionsrelevante BlackLab-Konfiguration waere aus dem echten Repo entfernt worden
- die Runtime-Pfadlogik war nicht mehr belastbar kompatibel mit dem bestehenden Deploy-Modell `webapp -> /srv/webapps/corapan/app`

## Operative Wirkung

- der bestaetigte Auto-Deploy bleibt innerhalb von `webapp/` funktionsfaehig
- die produktive BlackLab-Konfiguration bleibt im Server-Checkout unter `app/config/blacklab` erhalten
- die App erwartet Konfiguration in Dev und Prod wieder an der vom Runtime-Root abgeleiteten Position

## Kompatibilitaet

- keine Aenderung am echten Git-Root
- keine Aenderung am bestaetigten Deploy-Ziel
- Root-Helfer ausserhalb von `webapp/` bleiben lokal, sind aber nicht Teil der deploy-relevanten Wahrheit