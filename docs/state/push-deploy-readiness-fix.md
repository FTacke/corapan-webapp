# Push/Deploy Readiness Fix

Datum: 2026-03-21
Umgebung: bestehendes Git-/Deploy-Modell `webapp -> /srv/webapps/corapan/app`

## Ziel

Die drei in der Readiness-Pruefung bestaetigten Push-Blocker wurden innerhalb des echten Repos `webapp/.git` behoben, ohne das Git- oder Deploy-Modell umzubauen.

## Behobene Blocker

### 1. Repo-Workflows in `webapp/.github/workflows/`

Wiederhergestellt aus dem echten Repo-Stand:

- `.github/workflows/deploy.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/md3-lint.yml`

Bewertung:

- der Auto-Deploy bleibt im bestaetigten Modell unter `webapp/` verankert
- keine Root-`.github`-Ersatzstruktur wird als deploy-relevante Wahrheit benutzt

### 2. BlackLab-Konfiguration in `webapp/config/blacklab/`

Wiederhergestellt aus dem echten Repo-Stand:

- `config/blacklab/blacklab-server.yaml`
- `config/blacklab/corapan-json.blf.yaml`
- `config/blacklab/corapan-tsv.blf.yaml`
- `config/blacklab/corapan-wpl.blf.yaml`
- `config/blacklab/json-metadata.blf.yaml`

Bewertung:

- die produktionsrelevante Konfiguration liegt wieder im echten Deploy-Pfad `/srv/webapps/corapan/app/config/blacklab`
- keine Root-`config`-Ersatzstruktur wird als deploy-relevante Wahrheit benutzt

### 3. Runtime-Pfadlogik

Korrigiert:

- `src/app/runtime_paths.py`

Korrektur:

- `get_config_root()` zeigt wieder auf `CORAPAN_RUNTIME_ROOT/config`

Bewertung:

- Development bleibt kompatibel mit dem lokalen Runtime-Root
- Production bleibt kompatibel mit dem bestaetigten Container-Mount `/app/config`

## Ergebnis

Die drei zuvor bestaetigten Push-Blocker sind innerhalb von `webapp/` behoben. Root-Dateien ausserhalb von `webapp/` bleiben lokal hilfreich, sind aber nicht mehr als deploy-relevanter Ersatz erforderlich.