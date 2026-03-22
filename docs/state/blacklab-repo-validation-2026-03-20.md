# BlackLab Repo Validation 2026-03-20

Datum: 2026-03-20
Modus: repo-only, scoped validation
Scope:

1. src/app/*
2. src/scripts/*
3. scripts/blacklab/*
4. scripts/deploy_sync/*
5. config/*
6. compose-Dateien

Suchmuster:

- blacklab_export
- blacklab_index
- runtime/corapan/data/blacklab

Ziel:

- keine ACTIVE Referenz auf alte BlackLab-Pfade

## 1. Methodik

Die Validierung wurde absichtlich nicht repo-weit ausgefuehrt.
Geprueft wurden nur die freigegebenen Pfadgruppen aus dem Scope.

Zur Einordnung wurden zwei Sucharten kombiniert:

1. breite String-Suche auf die drei Suchmuster
2. praezise Altpfad-Suche auf echte alte Pfadformen wie:
   - data/blacklab_export
   - data/blacklab_index
   - runtime/corapan/data/blacklab

Konfigurationskontext wurde zusaetzlich gegen die kanonischen Quellen geprueft:

- src/app/config/__init__.py
- scripts/dev-start.ps1
- docker-compose.dev-postgres.yml
- infra/docker-compose.prod.yml

Ergebnis dieser Kontextpruefung:

- aktive App-Konfiguration verwendet BLS_BASE_URL und BLS_CORPUS explizit
- der aktive Docmeta-Pfad ist auf data/blacklab/export umgestellt
- Dev-Compose mountet data/blacklab/index
- Prod-Compose bereitet den kanonischen Exportpfad unter /app/data/blacklab/export vor

## 2. Gefundene Stellen

### 2.1 src/app

| Datei | Stelle | Treffer | Klassifikation | Bewertung |
|---|---|---|---|---|
| src/app/search/speaker_utils.py | Kommentar am Dateikopf | src/scripts/blacklab_index_creation.py | DOC | Nur Verweis auf Skriptnamen, kein alter Pfad |

Praezise Altpfad-Suche in src/app:

- keine Treffer auf data/blacklab_export
- keine Treffer auf data/blacklab_index
- keine Treffer auf runtime/corapan/data/blacklab

### 2.2 src/scripts

| Datei | Stelle | Treffer | Klassifikation | Bewertung |
|---|---|---|---|---|
| src/scripts/blacklab_index_creation.py | Usage-Docstring | Modulname blacklab_index_creation | DOC | Nur Skriptname, keine alte Pfadverdrahtung |

Praezise Altpfad-Suche in src/scripts:

- keine Treffer auf data/blacklab_export
- keine Treffer auf data/blacklab_index
- keine Treffer auf runtime/corapan/data/blacklab

### 2.3 scripts/blacklab

| Datei | Stelle | Treffer | Klassifikation | Bewertung |
|---|---|---|---|---|
| scripts/blacklab/build_blacklab_index_prod.sh | deaktiviertes Legacy-Skript | Verweise auf build_blacklab_index und publish_blacklab_index | LEGACY | Build-in-production ist hart deaktiviert, kein aktiver Pfad |
| scripts/blacklab/retain_blacklab_backups_prod.sh | Kommentarblock | blacklab_index.bak_* und blacklab_index.backup_* | LEGACY | Explizite Legacy-Erwaehnung in Retention-Doku, kein aktiver Default |
| scripts/blacklab/run_export.py | Modul-/Dateiname | 03b_generate_blacklab_export.py | LEGACY | Externer Runnername, kein Repo-Altpfad |

Praezise Altpfad-Suche in scripts/blacklab:

- keine Treffer auf data/blacklab_export
- keine Treffer auf data/blacklab_index
- keine Treffer auf runtime/corapan/data/blacklab

### 2.4 scripts/deploy_sync

| Datei | Stelle | Treffer | Klassifikation | Bewertung |
|---|---|---|---|---|
| scripts/deploy_sync/README.md | Nutzungsdoku | publish_blacklab_index.ps1 | DOC | Aktuelle Doku, kein Altpfad |
| scripts/deploy_sync/legacy/20260116_211115/PUBLISH_BLACKLAB_INDEX.md | mehrere Stellen | data/blacklab_index.new, /srv/webapps/corapan/data/blacklab_index* | LEGACY | Historisches Legacy-Material unter legacy/ |
| scripts/deploy_sync/legacy/20260116_211115/update_data_media.ps1 | Kommentar | blacklab_export | LEGACY | Historischer Legacy-Unterbau |
| scripts/deploy_sync/legacy/20260116_211115/sync_core.ps1 | Excludes | blacklab_index, blacklab_index.backup | LEGACY | Historischer Legacy-Unterbau |

Praezise Altpfad-Suche in scripts/deploy_sync ausserhalb legacy:

- keine Treffer auf data/blacklab_export
- keine Treffer auf data/blacklab_index
- keine Treffer auf runtime/corapan/data/blacklab

Praezise Altpfad-Suche in scripts/deploy_sync inklusive legacy:

- Treffer nur unter scripts/deploy_sync/legacy/*

### 2.5 config

| Datei | Stelle | Treffer | Klassifikation | Bewertung |
|---|---|---|---|---|
| config/blacklab/blacklab-server.yaml | Kommentar | blacklab_index folder | DOC | Allgemeine BlackLab-Server-Erlaeuterung, kein Hostpfad |
| config/blacklab/corapan-tsv.blf.yaml | Kommentar | blacklab_index_creation.py | DOC | Verweis auf Generator-Skriptname |

Praezise Altpfad-Suche in config:

- keine Treffer auf data/blacklab_export
- keine Treffer auf data/blacklab_index
- keine Treffer auf runtime/corapan/data/blacklab

### 2.6 Compose-Dateien

Breite Suche in compose-Dateien:

- keine Treffer auf blacklab_export
- keine Treffer auf blacklab_index
- keine Treffer auf runtime/corapan/data/blacklab

Bewertung:

- docker-compose.dev-postgres.yml ist sauber auf data/blacklab/index umgestellt
- infra/docker-compose.prod.yml bereitet den kanonischen Exportpfad vor und enthaelt keine alte BlackLab-Pfadreferenz

## 3. Klassifikation

### ACTIVE

Keine Fundstelle.

### LEGACY

- scripts/blacklab/build_blacklab_index_prod.sh
- scripts/blacklab/retain_blacklab_backups_prod.sh
- scripts/blacklab/run_export.py
- scripts/deploy_sync/legacy/20260116_211115/PUBLISH_BLACKLAB_INDEX.md
- scripts/deploy_sync/legacy/20260116_211115/update_data_media.ps1
- scripts/deploy_sync/legacy/20260116_211115/sync_core.ps1

### DOC

- src/app/search/speaker_utils.py
- src/scripts/blacklab_index_creation.py
- scripts/deploy_sync/README.md
- config/blacklab/blacklab-server.yaml
- config/blacklab/corapan-tsv.blf.yaml

### DEBUG

Keine Fundstelle im freigegebenen Scope.

## 4. Bewertung

### Ist das Repo sauber?

Ja, im freigegebenen Scope ist das Repo fuer aktive BlackLab-Pfade sauber.

Begruendung:

- In keinem geprueften aktiven Codepfad wurde ein echter alter BlackLab-Pfad gefunden.
- Die einzigen echten Altpfad-Treffer liegen im Legacy-Unterbaum von scripts/deploy_sync.
- Die uebrigen Treffer sind Namensreferenzen oder Kommentare, nicht aktive Pfadverdrahtung.
- Die compose-Dateien im Scope enthalten keine alten BlackLab-Pfade mehr.

### Ergebnis gegen das Ziel

Ziel erreicht:

- keine ACTIVE Referenz auf alte BlackLab-Pfade

## 5. Verbleibende Risiken

1. Legacy-Kommentare in scripts/blacklab/retain_blacklab_backups_prod.sh nennen alte Namensschemata noch als historische Referenz.
   Bewertung: niedrig, weil nicht als aktiver Default verwendet.

2. Das deaktivierte Skript scripts/blacklab/build_blacklab_index_prod.sh bleibt als Legacy-Artefakt im Repo.
   Bewertung: niedrig bis mittel, weil es zwar fail-fast blockiert, aber weiterhin alte Betriebsrealitaet dokumentiert.

3. Unter scripts/deploy_sync/legacy existiert weiterhin vollstaendiges historisches Material mit alten BlackLab-Pfaden.
   Bewertung: niedrig fuer Deployment, solange der legacy-Unterbaum nicht wieder als aktiver Standard verwendet wird.

4. Die Validierung war absichtlich scoped und kein globaler Repo-Scan.
   Bewertung: akzeptiert, weil genau das angefordert war. Historische Treffer ausserhalb des Scopes sind damit bewusst nicht Teil dieser Aussage.

## 6. Schlussaussage

Repo ist bereit fuer Deployment.

Begruendung:

- im geprueften aktiven Scope existiert keine ACTIVE Referenz auf alte BlackLab-Pfade
- verbleibende Altpfade sind als LEGACY oder DOC klassifizierbar
- die kanonischen Konfigurationsquellen sind konsistent mit data/blacklab/{index,export,...}