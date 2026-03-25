# Zielbild

Am Ende gibt es kein loses Script-Bündel mehr, sondern ein klar definiertes lokales Produktions-Sync-System mit drei getrennten Lanes:

* **Data**
* **Media**
* **BlackLab**

Und dazu:

* **ein** verbindlicher Transportvertrag
* **ein** SSH-Layer
* **ein** Logging-Layer
* **klare Guards**
* **saubere Doku**
* **Agent-/Skill-Regeln, die keine funktionierenden Workarounds kaputtoptimieren**

# Harte Architekturentscheidungen

Diese Punkte sind ab jetzt fest:

1. **Standardtransport**

   * `rsync` via repo-gebundeltes cwRSync `ssh.exe`
   * nicht generisches Windows-OpenSSH
   * nicht „PATH-ssh“
   * nicht vereinfachen

2. **Fallback 1**

   * `scp -O`

3. **Fallback 2**

   * `tar|ssh` nur für kleine bis mittlere Transfers und nur auf dem funktionierenden Pfad
   * nicht für große Dateien
   * nicht als gleichwertiger Ersatz behandeln

4. **Lane-Trennung bleibt**

   * Data/Media werden nicht mit BlackLab verschmolzen
   * BlackLab behält Staging, Validierung, atomischen Swap, Backup-Retention

5. **Keine aggressive Bereinigung**

   * Fallbacks, Manifest-Migration, Abort-Marker und cwRsync-Sonderlogik werden nicht entfernt, bevor sie explizit ersetzt oder entbehrlich belegt sind.

# Zielstruktur im Repo

```text
app/scripts/deploy_sync/
  core/
    transport.ps1
    ssh.ps1
    rsync.ps1
    logging.ps1
    guards.ps1
    paths.ps1
  tasks/
    sync_data.ps1
    sync_media.ps1
    publish_blacklab_index.ps1

maintenance_pipelines/_2_deploy/
  deploy_data.ps1
  deploy_media.ps1
  publish_blacklab.ps1

docs/rsync/
  README.md
  operator_prerequisites.md
  transport_matrix.md
  live_validation_sync.md
  repo_rsync_audit.md
  server_rsync_audit.md
  technical_precheck_sync_constraints.md
```

# Verantwortlichkeiten der Core-Module

## `core/transport.ps1`

Zentrale Auswahl des Transferwegs.

Aufgaben:

* Standard = `rsync-cwrsync`
* Fallback = `scp-legacy`
* Optional begrenzt = `tar-ssh`
* blockiert technisch ungeeignete Wege
* enthält eine kleine Entscheidungslogik:

  * große Datei oder Media-Lane → niemals `tar|ssh`
  * kein funktionierendes cwRSync → Fallback nur bewusst und geloggt
  * generisches Windows-OpenSSH für rsync → als ungeeignet markieren

## `core/ssh.ps1`

Einziger SSH-Vertrag.

Aufgaben:

* baut konsistente SSH-Argumente
* trennt:

  * cwRSync-SSH-Kontext
  * normales OpenSSH für Prüfungen/Fallbacks
* führt keine stillen impliziten Pfade
* erlaubt parametrisierte Host/User/Port/Key/KnownHosts
* unterstützt Host-Key-Härtung, aber mit Bootstrap-Pfad

Wichtig:

* hier keine naive Vereinheitlichung auf „einfach ssh.exe“
* Live-Test hat gezeigt, dass genau das brechen kann. 

## `core/rsync.ps1`

Einziger rsync-Weg.

Aufgaben:

* nur repo-gebundenes cwRSync `rsync.exe`
* nur dazu passendes gebündeltes `ssh.exe`
* standardisierte Flags
* sauberes Itemized-Logging
* No-Change-Erkennung
* Resume-Verhalten beibehalten (`--partial`)

## `core/logging.ps1`

Einheitliche Logs.

Lokal:

* schreibt pro Lauf strukturierte Logs und Summary-Dateien

Optional remote:

* legt Laufprotokolle unter `/srv/webapps/corapan/logs/sync/` ab, soweit sicher umsetzbar

Pflichtdaten pro Lauf:

* Lane
* Start/Ende
* Transportweg
* Dry-Run ja/nein
* Quelle/Ziel
* Exitcode
* geänderte Dateien
* gelöschte Dateien
* No-Change
* Fallback benutzt ja/nein

## `core/guards.ps1`

Sicherheitschecks.

Pflichtprüfungen:

* Source existiert
* Source nicht leer, wenn später `--delete` aktiv sein könnte
* Zielpfad plausibel
* keine produktiven Zielpfade im Testmodus
* Media-Lane mit großen Dateien blockiert `tar|ssh`
* BlackLab-Lane blockiert generische Vereinfachungen

## `core/paths.ps1`

Kanonische Pfade.

Aufgaben:

* lokale Runtime-Quellen
* Remote-Zielpfade
* `.sync_state`
* Testpfade
* Logpfade

Damit verschwinden harte Pfade aus Task- und Orchestrator-Skripten.

# Refactor-Phasen

## Phase 1 — Einfrieren der Realität

Ziel: erst klare Wahrheit herstellen, noch ohne riskanten Umbau.

Umsetzen:

* `docs/rsync/README.md` anlegen
* `docs/rsync/operator_prerequisites.md` anlegen
* `docs/rsync/transport_matrix.md` anlegen
* Live-validierte Regeln aus dem Test dokumentieren:

  * Standardweg = cwRSync-rsync
  * `scp -O` bleibt
  * `tar|ssh` nicht großdateitauglich
  * Windows-OpenSSH nicht als rsync-Standard

Zusätzlich:

* alte/abweichende Doku mit Warnhinweis versehen, nicht sofort löschen

Ergebnis:

* keine Mythen mehr
* alle weiteren Änderungen arbeiten gegen eine explizite Referenz

## Phase 2 — Nur echte Fehler beheben

Ziel: sichere Sofortkorrekturen ohne Transportpfade zu beschädigen.

Umsetzen:

* doppelten Statistik-Deploy entfernen
* BlackLab-Validierung von bloßem Corpora-Check auf echte Query erweitern
* offensichtliche Doku-Widersprüche zu aktiven Pfaden korrigieren
* klare Markierung: `backup.sh` und Legacy-Artefakte nur noch archival oder raus, falls nachweislich tot.

Nicht anfassen:

* cwRSync-Kopplung
* Fallbacks
* Manifest-Migration
* Abort-Marker

## Phase 3 — Transport und SSH kapseln

Ziel: funktionierende Realität in saubere Schichten überführen.

Umsetzen:

* `core/transport.ps1` einführen
* `core/ssh.ps1` einführen
* `core/rsync.ps1` einführen
* direkte `ssh`, `scp`, `rsync`-Aufrufe in Tasks/Orchestratoren auf Core-Layer umstellen

Wichtig:

* nicht alles technisch auf einen einzigen Binärpfad reduzieren
* sondern sauber modellieren:

  * rsync-Transport hat eigene Toolchain
  * scp hat eigenen Fallback-Vertrag
  * tar|ssh hat begrenzten Geltungsbereich

Ergebnis:

* Ordnung ohne Funktionsverlust

## Phase 4 — Guards und Logging

Ziel: das System sicher und beobachtbar machen.

Umsetzen:

* Empty-Source-Guard vor allen riskanten Läufen
* `--delete` nicht ohne vorgelagerten Sicherheitscheck
* rsync mit `--itemize-changes --out-format`
* No-Change explizit loggen
* Fallback-Nutzung explizit loggen
* optional Summary JSON oder Markdown pro Lauf

Wichtig:

* zuerst Logging, dann weitere Härtung
* sonst tappt man im Dunkeln

## Phase 5 — Lane-spezifische Bereinigung

Ziel: jede Lane fachlich und technisch sauber ziehen.

### Data

* Scope klar festziehen
* Statistik-Dateien nur einmal
* `data/exports` explizit entscheiden: behalten und sauber dokumentieren oder aus dem Modell entfernen

### Media

* `--partial` bleibt Pflicht
* keine Experimente mit `tar|ssh` als Ersatz
* `-ForceMP3` und ähnliche Sonderlogik nur nach Prüfung vereinheitlichen

### BlackLab

* SSH-Uploadpfad über zentralen Vertrag ziehen, ohne den Staging-/Swap-Mechanismus zu beschädigen
* Query-basierte Validierung
* produktive BlackLab-Konfig mittelfristig aus deploybarem Checkout lösen

## Phase 6 — Sicherheitshärtung mit Migrationspfad

Ziel: sicherer werden, ohne den Betrieb abzuschießen.

Umsetzen:

* `known_hosts`-Bootstrap definieren
* Host-Key-Checking nicht blind erzwingen, sondern vorbereitet einführen
* Key-/Host-/Alias-Konfiguration parametrisierbar machen
* repo-harte Operator-Pfade entfernen, aber erst nach getesteter Parametrisierung

Wichtig:

* der Live-Test hat gezeigt: `StrictHostKeyChecking=yes` ist möglich, aber nur mit vorbereitetem `known_hosts`. Das muss als eigener Migrationsschritt behandelt werden. 

## Phase 7 — Erst dann Legacy abbauen

Entfernen oder archivieren erst, wenn die neue Schicht läuft und dokumentiert ist:

* 8.3-Sonderpfade nur, wenn auf echter Operator-Maschine wirklich entbehrlich
* `tar+base64`-Fallback nur, wenn explizit obsolet
* SCP-Fallback nur, wenn Zielhost endlich modernen SCP/SFTP sauber unterstützt
* Manifest-Migration nur nach Altzustands-Cutover

# Konkrete Regeln pro Lane

## Data-Lane

Behalten:

* rsync-basierter Delta-Transfer
* allowlist-basierte Statistik-Dateien
* produktive Auth-/Runtime-State-Sperren

Ändern:

* doppelten Statistiklauf entfernen
* klare Scope-Doku
* Logging verbessern

Nicht vereinfachen:

* nicht „einfach alles unter data/“ synchronisieren

## Media-Lane

Behalten:

* rsync + cwRSync
* `--partial`
* Delta-Verhalten
* klare Trennung von `mp3-temp`

Ändern:

* bessere Laufprotokolle
* mehr Guardrails gegen falsche Quelle
* explizite Kennzeichnung großer Dateiübertragungen

Nicht vereinfachen:

* kein Standardwechsel zu `tar|ssh`
* kein blindes Umschalten auf OpenSSH

## BlackLab-Lane

Behalten:

* separater Publish-Prozess
* Staging
* atomischer Swap
* Backup-Retention

Ändern:

* echte Query-Validierung
* Uploadpfad konsolidieren
* produktive Konfiguration aus Checkout lösen

Nicht vereinfachen:

* nicht in Data-Lane integrieren
* nicht Staging/Swap entfernen

# Was ausdrücklich nicht refactored werden darf

Diese Verbote sollten wörtlich in Doku und Skill landen:

* nicht `rsync`-Transport auf generisches `ssh.exe` vereinfachen
* nicht `scp -O` entfernen
* nicht `tar|ssh` als Standard für große Dateien darstellen
* nicht Fallbacks löschen, nur weil sie unschön aussehen
* nicht Host-Key-Härtung ohne Bootstrap einführen
* nicht Lane-Trennung auflösen
* nicht BlackLab wie Data/Media behandeln

Die Live-Validierung belegt genau diese Grenzen. 

# Dokumentationsplan

Neu oder aktualisiert unter `docs/rsync/`:

## `README.md`

Kurzer Einstieg:

* drei Lanes
* Standardweg
* Fallbacks
* Gefahren
* Verweise

## `operator_prerequisites.md`

Kanonische Operator-Voraussetzungen:

* Windows/PowerShell
* repo-gebundenes cwRSync
* VPN/Uni-Netz als betriebliche Voraussetzung
* SSH-Alias/Host/Key/KnownHosts-Modell
* Testpfadkonzept

## `transport_matrix.md`

Tabelle:

* `rsync + cwRSync ssh.exe` → Standard
* `scp -O` → Fallback
* `tar|ssh cmd` → kleiner/mittlerer Fallback
* `tar|ssh PowerShell` → nicht verwenden
* `rsync + Windows OpenSSH` → nicht verwenden

## `logging_contract.md`

Was jeder Lauf protokollieren muss.

## `safety_contract.md`

* Empty-Source
* Delete
* Testpfade
* Dry-Run
* Fallback-Regeln

# Skill-/Agent-Integration

Das gehört als neue Skill-Datei dazu, nicht nur als lose Doku:

```text
.github/skills/server-sync-production-lanes/SKILL.md
```

Inhalt:

* Produktions-Sync läuft lokal/operatorseitig, nicht über GitHub
* drei getrennte Lanes
* Standardtransport ist live-validiert
* cwRSync-Toolchain nicht kaputtoptimieren
* `scp -O` nicht entfernen
* `tar|ssh` nicht für große Dateien empfehlen
* `--delete` nur mit Guards
* Host-Key-Härtung nur mit Bootstrap
* Änderungen an `deploy_sync/**` oder `_2_deploy/**` müssen Lane-Klassifikation und Transportbewertung enthalten

Zusätzlich knapper Verweis in:

* `.github/instructions/devops.instructions.md`

# Reihenfolge der Umsetzung

Die sinnvolle Reihenfolge ist:

1. Doku kanonisieren
2. doppelten Statistik-Deploy entfernen
3. BlackLab-Validierung reparieren
4. Core-Layer für Transport/SSH/rsync einziehen
5. Logging und Guards einbauen
6. Task-Skripte auf Core-Layer umstellen
7. Known-hosts-/Sicherheitsmigration vorbereiten
8. Legacy erst ganz am Ende abbauen

# Abnahmekriterien

Der Refactor ist erst fertig, wenn diese Punkte erfüllt sind:

* `deploy_data.ps1` nutzt nur den zentralen Transport-/SSH-Layer
* `deploy_media.ps1` ebenso
* `publish_blacklab.ps1` ebenso, ohne BlackLab-Sonderlogik zu beschädigen
* jeder Lauf erzeugt klare Logs
* No-Change ist sichtbar
* Fallback-Nutzung ist sichtbar
* Standardtransport ist explizit cwRSync-rsync
* `scp -O` existiert noch als Fallback
* `tar|ssh` ist klar begrenzt
* Skill und `docs/rsync/` spiegeln dieselbe Wahrheit

