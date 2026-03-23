# Repo Finalization Status (Post-Migration)

## Status
Die Repo-Root-Migration wurde lokal ausgefuehrt.

- aktives Git-Root: `C:\dev\corapan`
- aktiver Anwendungsteilbaum: `C:\dev\corapan\app`
- `maintenance_pipelines/` ist Teil desselben Root-Repos
- Root-`.github/workflows` ist die aktive versionierte Workflow-Wahrheit
- Push bleibt bis zur expliziten Festlegung einer neuen Root-`origin` gesperrt

---

## Ausgefuehrte Reihenfolge

1. Dev/Prod-Vertrag verifiziert
2. Repo-Root-Struktur definiert
3. Git auf `corapan/` hochgezogen
4. Maintenance-Pipelines auf Root-/App-Vertrag angepasst
5. `webapp` nach `app` umbenannt
6. Root- und App-Vertrag lokal verifiziert

---

# Phase 1 – Dev = Prod Verifikation (Pflicht vor allem anderen)

## Ziel
Sicherstellen, dass lokale Entwicklungsumgebung exakt dem produktiven Zustand entspricht.

## Prüfpunkte

- Docker Mounts entsprechen Prod
- Verzeichnisstruktur identisch:
  - app/
  - data/
  - media/
  - logs/
- BlackLab:
  - nutzt data/blacklab
  - keine Legacy-Pfade
- keine Referenzen mehr auf runtime/
- Auth/Postgres funktioniert identisch
- Audio/Media korrekt

## Risiko
Wenn hier Abweichungen existieren:
→ alles Weitere basiert auf falscher Grundlage

---

# Phase 2 – Repo-Root Struktur definieren

## Ziel
Klare Trennung zwischen:
- Code (app)
- System (corapan root)

## Zielstruktur

```
corapan/
  app/
  data/              (NICHT versioniert)
    config/          (kanonische Runtime-Config; entspricht prod data/config -> /app/config)
  media/             (NICHT versioniert)
  maintenance_pipelines/
  docs/
  .github/
  .gitignore
  README.md
```

## Entscheidungen

### Was bleibt im Repo-Root
- README.md (systemweite Beschreibung)
- .gitignore (systemweit)
- docs/
- maintenance_pipelines/
- .github/

### Was gehört in app/
- kompletter Anwendungscode
- Docker/Infra configs für App
- versionierte BlackLab-Konfiguration unter `app/config/blacklab`

## Wichtig
- keine Laufzeitdaten im Repo
- keine Vermischung von App und Infrastruktur
- kein konkurrierender Root-`config/`-Runtimepfad neben `data/config`
- BlackLab-Konfiguration bleibt als versionierte App-Konfiguration getrennt vom Runtime-Datenbaum

---

# Phase 3 – Git auf corapan/ hochziehen

## Status
Abgeschlossen.

## Ergebnis

- `C:\dev\corapan\.git` ist das einzige aktive Git-Root
- Legacy-History wurde ueber Backup-Mirror und Root-Remotes gesichert
- Root-README, Root-.gitignore, Root-Skripte und Root-Workflows sind Teil desselben Repos

## Anpassungen

### .gitignore
MUSS enthalten:

```
data/
media/
logs/
runtime/
.env
```

Wichtig:

- kein pauschales `*.sql`, weil versionierte Migrationen unter `app/migrations/` im finalen Root-Repo erhalten bleiben muessen
- stattdessen nur lokale Dumps/Archive ignorieren, z. B. `*.dump`, `*.sql.gz`, `*.sql.zip`

### README.md
- Systembeschreibung (nicht nur App)
- Struktur erklären
- Deploy-Flow erklären
- Runtime-Config `data/config` und versionierte BlackLab-Config `app/config/blacklab` explizit trennen

### Pre-Push-Regel fuer Root-Lift
- Root-README, Root-.gitignore und Root-Wrapper muessen vor dem Git-Root-Wechsel kanonisch vorbereitet sein
- Root-`.github/workflows` muessen fuer `app/` vorbereitet sein, duerfen aber die aktuelle versionierte Wahrheit unter `webapp/.github/workflows` vorher nicht stillschweigend ersetzen
- Maintenance-Pipelines und Root-Wrapper muessen `app/` und `webapp/` aufloesen koennen, bevor der physische Rename erfolgt

---

# Phase 4 – Maintenance Pipelines prüfen (KRITISCH)

## Status
Abgeschlossen.

## Betroffene Komponenten

- maintenance_pipelines/_1_blacklab
- maintenance_pipelines/_2_deploy
- rsync-Skripte

## Prüfpunkte

- Zielpfade korrekt:
  - data/
  - data/blacklab/
  - media/
- BlackLab-Config weiter getrennt unter `app/config/blacklab`
- keine Referenzen mehr auf:
  - runtime/
  - alte blacklab_index Pfade
- Deploy-Skripte nutzen korrekte Containernamen

## Verifiziert

- Resolver zeigen auf `app/`
- Deploy-Helfer behalten `app/config/blacklab` als getrennten Config-Pfad
- keine aktiven Root-/App-Vertraege verweisen mehr auf `webapp` als Zielzustand

## Risiko
Wenn hier Fehler sind:
→ Daten landen am falschen Ort
→ stille Fehler möglich

---

# Phase 5 – Rename webapp → app (FINAL STEP)

## Status
Abgeschlossen.

## WICHTIG
Dieser Schritt wird bewusst zuletzt ausgeführt

## Ergebnis

- `C:\dev\corapan\webapp` wurde nach `C:\dev\corapan\app` umbenannt
- Root-Compose mountet `./app:/app:ro`
- Root-Compose mountet `./app/config/blacklab:/etc/blacklab:ro`
- App-, Root-, Maintenance- und Governance-Dateien nutzen den `app/`-Vertrag

Voraussetzungen vor dem Rename:

- Git-Root ist bereits auf `C:\dev\corapan` gehoben
- Root-Workflow-Dateien sind auf `app/` vorbereitet
- Root-Wrapper und Maintenance-Pipelines koennen `app/` direkt aufloesen
- kein push-kritischer Vertrag verweist mehr stillschweigend auf `webapp/.github/workflows` als kuenftigen Endzustand

## Verifikation

- Build
- Deploy
- vollständiger Smoke-Test

Bereits lokal bestaetigt:

- Compose-Rendering fuer Root und App erfolgreich
- aktive `webapp`-Treffer in operativen Dateien entfernt
- redundantes Root-`config/` als Drift-Snapshot aus dem Arbeitsbaum ausgelagert

## Risiko
Früh ausgeführt:
→ hoher Break-Risk

---

# Phase 6 – Final Validation

## Aktueller Status
Lokal abgeschlossen. Externer Push/Deploy bewusst noch nicht ausgefuehrt.

## Checks

- Deploy läuft
- Health OK
- Suche funktioniert
- Audio funktioniert
- Media vorhanden
- BlackLab korrekt

---

# Phase 7 – Lessons Learned & Agent Setup

## Ziel
Wissen dauerhaft sichern

## Schritte

- prod_migration Docs konsolidieren
- in docs/ integrieren
- Agent/Skills Setup aktualisieren
- Regeln festhalten:
  - keine runtime-Strukturen
  - klare Mount-Regeln
  - canonical paths

---

# Ergebnis

Nach Abschluss:

- ein lokales Root-Repo mit klarer Struktur
- `app/` als eindeutiger versionierter Anwendungsteilbaum
- keine konkurrierende aktive Root-Konfigurationskopie im Arbeitsbaum
- reproduzierbare lokale Grundlage fuer den ersten kontrollierten Root-Push

---

# Kurzfassung

Die urspruengliche Reihenfolge wurde eingehalten. Der verbleibende bewusste Schritt ist nicht mehr die Migration, sondern die spaetere Erstveroefentlichung des neuen Root-Repos.

1. Realitaet pruefen
2. Struktur definieren
3. Repo umbauen
4. Pipelines sichern
5. Rename zuletzt
6. Root-Remote spaeter explizit festlegen

Alles andere fuehrt zu unnoetigem Risiko.

