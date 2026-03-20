# `docs/state/instance-structure-unification-plan.md`

## Zweck

Diese Datei ist die **kanonische Steuerungsgrundlage** für die Vereinheitlichung der CORAPAN-Instanzstruktur über **Dev und Prod**.

Ziel ist eine **einheitliche, template-fähige, robuste und verständliche Struktur**, ohne parallele Wahrheiten, ohne implizite Fallbacks und ohne Risiko für produktive Daten.

Alle strukturellen Änderungen (Pfade, Resolver, Runtime, Datenzugriffe) müssen mit diesem Plan konsistent sein.

---

## Zielbild (kanonisches Modell)

Die Instanzwurzel ist:

```
corapan/
```

Darunter liegen direkt:

```
corapan/
  app/        # Anwendungscode (Repo / deployter Code)
  config/     # Laufzeitkonfiguration
  data/       # operative Daten
  media/      # Medien (Audio, Transkripte etc.)
  logs/       # Logs
  runner/     # Deployment / GitHub Runner
```

### Grundprinzipien

* **Genau eine Instanzwurzel** (`corapan/`)
* **Keine zweite parallele Struktur**
* **Keine impliziten Pfad-Fallbacks**
* **Explizite Konfiguration > implizite Ableitung**

---

## Nicht-Ziel / Legacy

Folgende Struktur ist **nicht Teil des Zielmodells**:

```
corapan/runtime/corapan/...
```

Diese wird als:

* **Legacy-Struktur**
* **Migrationsartefakt**
* **nicht kanonisch**

klassifiziert.

Sie darf **nicht weiter als gleichwertige Alternative behandelt werden**.

---

## Sicherheitsgrenzen (nicht verhandelbar)

Folgende Bereiche sind in frühen Phasen **tabu**:

* **Produktive PostgreSQL-Daten**
* **Auth-Datenbank**
* **Analytics-Daten / Tracking**
* **BlackLab-Indizes und Exportpfade**
* **docmeta.jsonl (produktiv)**
* **db/public / db/restricted**

### Regeln

* Keine Migration ohne explizite Verifikation
* Keine Löschung ohne belegte Inaktivität
* Keine impliziten Änderungen durch Refactoring
* Keine gleichzeitige Struktur- und Datenmigration

---

## Arbeitsprinzipien

* **Erst analysieren, dann ändern**
* **Explizite Pfade statt Fallbacks**
* **Dev und Prod dürfen nicht unterschiedliche Modelle haben**
* **Keine „funktioniert irgendwie“-Zustände**
* **Jede Änderung muss deterministisch nachvollziehbar sein**

---

## Umsetzungsplan (Wellen)

### Welle 0: Zielmodell festziehen

* Zielstruktur final bestätigen
* Legacy (`runtime/corapan`) klar als nicht-kanonisch markieren
* Dokumentation angleichen

**Stop-Kriterium:**
Es gibt **keine widersprüchlichen Aussagen** mehr zur Instanzstruktur.

---

### Welle 1: Inventarisierung (Dev + Prod)

Für jede relevante Komponente erfassen:

* Welche Pfade werden tatsächlich gelesen?
* Welche Pfade werden geschrieben?
* Welche Quelle ist aktiv?
* Gibt es doppelte Daten?
* Gibt es Inkonsistenzen?

Bereiche:

* `data/` vs `runtime/.../data`
* `media/` vs `runtime/.../media`
* `config/`
* `logs/`
* `docmeta.jsonl`
* Atlas-Metadaten
* Statistikdateien
* Transkripte
* Audio-Dateien

**Ergebnis:**

Klassifikation je Pfad:

* `ACTIVE_CANONICAL`
* `ACTIVE_LEGACY`
* `UNCLEAR`
* `INACTIVE`

---

### Welle 2: Dev funktional stabilisieren

Ziel: Dev muss vollständig über **kanonische Pfade** laufen.

* `data` und `media` müssen vollständig funktionieren
* fehlende Unterstrukturen identifizieren und ergänzen
* keine impliziten runtime-Fallbacks mehr

**Wichtig:**

* keine Strukturverschiebung
* keine Datenlöschung
* nur funktionale Konsistenz herstellen

**Stop-Kriterium:**

* alle Dev-Endpunkte greifen korrekt auf `corapan/data` und `corapan/media` zu

---

### Welle 3: Resolver vereinheitlichen

* Pfadauflösung in Code zentralisieren

* Reihenfolge:

  1. explizite ENV-Variablen
  2. kanonische Struktur (`corapan/data`, `corapan/media`)
  3. **kein stiller Fallback mehr auf runtime**

* Runtime nur noch optional oder deaktiviert

**Stop-Kriterium:**

* keine Codepfade greifen mehr implizit auf `runtime/corapan/...` zu

---

### Welle 4: Legacy entkoppeln

* prüfen, ob `runtime/corapan/...` noch aktiv genutzt wird
* falls nein:

  * als deprecated markieren
  * Nutzung unterbinden
* ggf. read-only machen

**Wichtig:**

* noch nichts löschen, wenn Unsicherheit besteht

---

### Welle 5: Legacy abbauen

* kontrollierte Entfernung von:

  * `runtime/corapan/...`
* nur nach:

  * vollständiger Inaktivitätsbestätigung
  * Backup
  * klarer Dokumentation

---

### Welle 6: Codepfad vereinheitlichen (`webapp → app`)

* Dev-Struktur an Prod angleichen
* Repo-Code konsistent unter `app/`

**Erst jetzt**, da:

* Pfade stabil
* Daten eindeutig
* Resolver konsistent

---

### Welle 7: BlackLab separat

* keine Kopplung an vorherige Schritte
* eigene Analyse:

  * Indexpfade
  * Exportpfade
  * Nutzung durch Analytics
* eigene Migration (falls nötig)

---

### Welle 8: Token_ID-Search reparieren!

* Frage User was gemeint ist.

---

## Lessons Learned (verbindlich)

### Architektur

* Eine Instanz darf **nur eine Wurzel haben**
* Parallele Strukturen erzeugen inkonsistente Realität
* Fallbacks maskieren Fehler statt sie zu lösen

### Dev vs Prod

* Dev und Prod müssen **dasselbe Strukturmodell verwenden**
* Unterschiede nur in Konfiguration, nicht in Struktur

### Runtime-Fehler

* `runtime/corapan` entstand durch falsche Annahme über Instanzwurzel
* führte zu doppelten Daten und unklaren Pfaden

### Konfigurationsfehler

* implizite Defaults sind gefährlich
* explizite ENV-Konfiguration ist stabiler

## Lessons Learned – Run 2026-03-20

- Problem:
  Dev nutzte fuer Web-App, Atlas und Advanced Search noch implizite repo-lokale Runtime-Fallbacks, waehrend die kanonische Dev-Struktur bereits bei `corapan/data` und `corapan/media` lag.
- Ursache:
  Mehrere Resolver und aktive Dev-Skripte behandelten `runtime/corapan` weiter als gueltigen Dev-Ersatzpfad. Zusaetzlich lag `docmeta.jsonl` nur im repo-lokalen Exportbaum, und Atlas erwartete Recording-Dateien unter `metadata/latest/tei`, obwohl sie in `metadata/latest` lagen.
- Fix:
  Dev-Resolver wurden auf explizite kanonische ENV-Aufloesung ohne repo-lokalen Runtime-Fallback umgestellt, `docmeta.jsonl` wurde einmalig nach `corapan/data/blacklab_export` kopiert, und Atlas faellt in Dev kontrolliert von `metadata/latest/tei` auf `metadata/latest` zurueck.
- Neue Regel:
  Agenten und Skills duerfen Dev-Probleme nicht dadurch "loesen", dass sie `runtime/corapan` wieder als impliziten Sicherheitsanker verwenden. Wenn eine Dev-Verifikation laeuft, muessen sie den kanonischen Workspace-Root explizit setzen und belegbar gegen diesen Pfad pruefen.

## Lessons Learned – Run 2026-03-20 (Media)

- Problem:
  Nach Welle 2 wurde ein Dev-Media-Fehler gemeldet, obwohl `MEDIA_ROOT` bereits auf `corapan/media` zeigte.
- Ursache:
  Die aktuelle Media-Aufloesung war auf einem frischen Prozess korrekt; die beobachtete Abweichung liess sich nur als veralteter lokaler Prozess, veraltete Verifikationssituation oder fehlende Sichtbarkeit der tatsaechlich aufgeloesten Transcript-Pfade plausibel einordnen.
- Fix:
  Kein erneuter Resolver-Umbau. Stattdessen wurden Transcript-Aufloesungslogs ergaenzt und Regressionstests fuer flache sowie verschachtelte Media- und Transcript-Requests gegen die kanonische Subfolder-Struktur hinzugefuegt.
- Neue Regel:
  Pfadkonsolidierung kann Subfolder-Strukturen brechen, wenn Code implizit flache Strukturen annimmt. Dev-Media-Verifikation muss deshalb immer sowohl flache als auch verschachtelte URL-Formen gegen einen frischen Prozess pruefen.

## Lessons Learned – Run 2026-03-20 (Resolver)

- Problem:
  Trotz stabilisierter Dev-Pfade gab es noch mehrere moduleigene Pfadableitungen fuer Metadata, Statistics, docmeta und Logs.
- Ursache:
  Die zentrale Runtime-Aufloesung war vorhanden, aber noch nicht der einzige Pfadursprung. Einzelne Module behielten relative Segmente, importzeitliche Konstanten oder eigene Sonderlogik.
- Fix:
  Ein zentraler `get_*`-Resolver-Satz wurde als gemeinsame Runtime-Quelle eingefuehrt und die verbleibenden App-Module darauf umgestellt. Verbleibende repo-lokale BlackLab-Pfade wurden explizit als `ACTIVE_LEGACY` markiert.
- Neue Regel:
  Resolver duerfen nie implizite Strukturannahmen enthalten. Wenn ein Pfad nicht ueber den zentralen Resolver laeuft, muss er entweder entfernt oder als `ACTIVE_LEGACY` klassifiziert werden.

## Lessons Learned – Run 2026-03-20 (Audio Playback)

- Problem:
  Nach gruenen Verifikationen fuer `/media/full/...` und `/media/transcripts/...` scheiterte der Search-UI-Player weiterhin auf `/media/play_audio/...` mit `404`.
- Ursache:
  Die Pfadauflosung war korrekt; die Route fand sogar den passenden Split-Chunk. Der eigentliche Fehler lag im Audio-Backend: pydub wollte `ffmpeg` und `ffprobe` ausfuehren, die im Dev-Prozess nicht vorhanden waren. Dieser Backend-Fehler wurde faelschlich wie ein fehlender Audio-Quellpfad behandelt.
- Fix:
  Die Snippet-Erzeugung wurde auf einen expliziten ffmpeg-Backend-Pfad umgestellt, mit Aufloesung ueber `CORAPAN_FFMPEG_PATH`, System-`ffmpeg` oder gebuendeltes `imageio-ffmpeg`. Die Playback-Route meldet fehlende Backend-Verfuegbarkeit jetzt als `503` statt als falsches `404`.
- Neue Regel:
  Spezialrouten wie `/media/play_audio` muessen separat verifiziert werden. Ein erfolgreiches `/media/full` beweist nicht, dass Audio-Snippet-Extraktion oder Decoder-Abhaengigkeiten funktionieren.

## Lessons Learned – Run 2026-03-20 (PROD Inventory)

- Problem:
  Die produktive Pfadrealitaet liess sich nicht verlaesslich aus Repo, Compose und Doku allein ableiten.
- Ursache:
  In PROD sind fuer unterschiedliche Verbraucher unterschiedliche Pfadmodelle gleichzeitig aktiv: die Web-App laeuft runtime-first, BlackLab nutzt weiter Top-Level-Pfade, und Secrets kommen aus `config/passwords.env` ausserhalb des runtime/config-Mounts. Zusaetzlich existieren mehrere echte Doppelbaeume mit verschiedenen Inodes.
- Fix:
  Keine Struktur- oder Datenaenderung. Stattdessen wurde die Live-Realitaet read-only ueber Host-Dateibaeume, Container-Mounts, redaktierte ENV-Werte, Logs und sichere Smoke-Requests inventarisiert und pro Pfad klassifiziert.
- Neue Regel:
  Produktive Pfadvereinheitlichung darf nie auf Repo-Annahmen beruhen; Live-Laufzeit und reale Mounts schlagen Compose- und Doku-Annahmen.

## Lessons Learned – Run 2026-03-20 (Consumer Matrix)

- Problem:
  Kritische und doppelte PROD-Pfade waren zwar inventarisiert, aber noch nicht vollstaendig nach Lesern, Schreibern und Deploy-Zielen zerlegt.
- Ursache:
  Die produktive Pfadrealitaet wird nicht nur von laufenden Containern bestimmt, sondern auch von self-hosted Runnern, externen Orchestratoren und deploy_sync-Unterbau. Dadurch koennen Live-Leser und Standard-Deploy-Ziele auseinanderlaufen.
- Fix:
  Fuer die kritischen Pfade wurde eine explizite Verbraucher-/Schreiber-Matrix gegen Live-Mounts, App-Code, BlackLab-Skripte, Runner-Workflow, maintenance_pipelines und deploy_sync aufgebaut. Dabei wurde der BlackLab-Widerspruch sichtbar: Live-Leser top-level, Default-Publish-Ziel runtime/data.
- Neue Regel:
  Ein Pfad darf erst entfernt oder vereinheitlicht werden, wenn alle Leser, Schreiber und Deploy-Ziele vollstaendig bekannt sind.
- Neue Zusatzregel:
  Deploy-Orchestratoren und Sync-Skripte sind Teil der produktiven Pfadrealitaet und duerfen nie als blosse Hilfsskripte ignoriert werden.

## Lessons Learned – Run 2026-03-20 (Rules Consolidation)

- Problem:
  Die bisherigen Wellen enthielten viele richtige Einzelregeln, aber noch kein konsolidiertes, uebertragbares Regelset fuer Agenten und Skills.
- Ursache:
  Lessons Learned entstehen oft ereignisbezogen. Ohne Normalisierung bleiben sie an konkrete Pfade, Bugs oder Runs gebunden und verhindern kuenftige Fehler nur unvollstaendig.
- Fix:
  Die bisherigen Wellen wurden auf wiederkehrende Strukturmuster verdichtet und als allgemeine Regeln, Anti-Patterns und Agent-Anweisungen klassifiziert. Projektspezifische Details wurden bewusst entfernt.
- Neue Regel:
  Lessons Learned muessen nach mehreren zusammenhaengenden Wellen nicht nur gesammelt, sondern in allgemeine, priorisierte Systemregeln ueberfuehrt werden.
- Neue Zusatzregel:
  Ein Skill-System ist nur dann robust, wenn es nicht Einzelfaelle speichert, sondern wiederkehrende Fehlerklassen in uebertragbare Handlungsregeln uebersetzt.

## Lessons Learned – Run 2026-03-20 (BlackLab Writer Fix)

- Problem:
  Der Standard-Publish-Pfad fuer BlackLab zeigte weiterhin auf `runtime/corapan/data/blacklab_index`, obwohl der live laufende BlackLab-Container ausschliesslich den Top-Level-Pfad `/srv/webapps/corapan/data/blacklab_index` liest.
- Ursache:
  `publish_blacklab_index.ps1` uebernahm seinen Default implizit aus `Get-RemotePaths().DataRoot`. Diese gemeinsame Remote-Pfadquelle ist fuer runtime-first data/media-Deploys korrekt, aber fuer BlackLab falsch.
- Fix:
  In `scripts/deploy_sync/_lib/ssh.ps1` wurde ein eigener expliziter `BlackLabDataRoot` eingefuehrt und `publish_blacklab_index.ps1` auf diesen Pfad umgestellt. Ein stiller Fallback zur runtime-DataRoot wurde entfernt.
- Neue Regel:
  Wenn ein Spezial-Deploy bewusst nicht demselben Zielmodell wie andere Deploys folgt, braucht er einen eigenen expliziten Default statt Wiederverwendung einer allgemeinen Remote-Pfadquelle.
- Neue Zusatzregel:
  Ein gemeinsam genutzter Helper darf fuer Spezialpfade nur erweitert, aber nicht still umgedeutet werden, wenn dadurch andere aktive Deploy-Flows betroffen waeren.

## Lessons Learned – Run 2026-03-20 (Compose Deploy Fix)

- Problem:
  Der produktive Deploy scheiterte in `docker-compose` mit `KeyError: 'ContainerConfig'`, obwohl der Fehler zunaechst auch als Runner- oder Workflow-Problem haette fehlklassifiziert werden koennen.
- Ursache:
  Der reale Deploy-Pfad laeuft lokal auf dem Zielserver ueber den self-hosted Runner und `scripts/deploy_prod.sh`. Dort war kein `docker compose` verfuegbar, sondern nur `docker-compose 1.29.2` neben Docker `28.2.2`.
- Fix:
  Das Deploy-Skript loest das Compose-Kommando jetzt explizit auf, bevorzugt Compose V2, blockiert Compose v1 hart und macht Host-, Runner- und Versionskontext vor dem Deploy sichtbar.
- Neue Regel:
  Bei Deploy-Fehlern muss zuerst der reale Ausfuehrungsort verifiziert werden. Tooling darf nicht auf dem Runner vermutet werden, wenn der Workflow in Wahrheit lokal auf dem Zielserver laeuft.
- Neue Zusatzregel:
  Veraltete Infrastruktur-CLI-Pfade duerfen in produktiven Deploy-Skripten nicht still weiterlaufen; sie muessen entweder explizit als unterstuetzt belegt oder hart blockiert werden.

## Lessons Learned – Run 2026-03-20 (Compose Bootstrap Forensics)

- Problem:
  Der Deploy-Fehler `KeyError: 'ContainerConfig'` trat weiter auf, obwohl der Compose-Guard bereits in `scripts/deploy_prod.sh` implementiert worden war.
- Ursache:
  Der Workflow rief `cd /srv/webapps/corapan/app ; bash scripts/deploy_prod.sh` direkt auf, ohne den Ziel-Checkout vorher auf den ausloesenden Commit zu aktualisieren. Dadurch konnten Aenderungen an `scripts/deploy_prod.sh` selbst im ersten betroffenen Lauf noch von der alten on-disk-Version ueberschrieben werden.
- Fix:
  Der Workflow setzt `/srv/webapps/corapan/app` jetzt vor dem Skriptaufruf per `git fetch --prune origin` und `git reset --hard "${GITHUB_SHA}"` auf den ausloesenden Commit.
- Neue Regel:
  Wenn ein Deploy-Workflow ein Skript aus einem persistenten Server-Checkout startet und dieses Skript sich selbst per Git aktualisiert, sind Aenderungen an genau diesem Skript nicht self-applying. Der Checkout muss vor dem Skriptstart auf den Trigger-Commit gebracht werden.
- Neue Zusatzregel:
  Bei Forensik zu self-hosted Deploys muss zwischen Workflow-Version, on-disk-Zielcheckout und Runner-Workspace unterschieden werden. Ein alter Runner-Workspace ist Drift-Signal, aber nicht automatisch der aktive Ausfuehrungspfad.

## Lessons Learned – Run 2026-03-20 (Compose Network Label Fix)

- Problem:
  Compose V2 konnte beim produktiven Deploy mit einem bestehenden aktiven Netzwerk in einen Label-Konflikt laufen, obwohl Realname und Projektname bereits zur Produktionsrealitaet passten.
- Ursache:
  Der reale Netzwerkname war korrekt auf `corapan-network-prod` gesetzt, aber der logische Compose-Netzwerk-Key im Repo lautete noch `corapan-prod`. Damit wich die Repo-Metadaten-ID von der bestehenden Compose-Netzwerkrealitaet ab.
- Fix:
  Im produktiven Compose-File wurde ausschliesslich der logische Netzwerk-Key auf `corapan-network-prod` angeglichen und alle Service-Referenzen wurden entsprechend umgestellt.
- Neue Regel:
  Bei Compose-V2-Konflikten muessen realer Ressourcenname und logische Compose-ID getrennt geprueft werden. Ein passender Realname beweist nicht, dass die Compose-Metadaten konsistent sind.
- Neue Zusatzregel:
  Wenn ein bestehendes Produktionsnetzwerk aktiv verwendet wird und nur die logische Compose-ID abweicht, ist die kleinste sichere Korrektur eine Repo-seitige Schluesselangleichung statt `external: true`, Neuanlage oder Server-Bereinigung.


---

---

## Pflicht: Lessons Learned nach jedem Run aktualisieren

Nach **jedem relevanten Durchlauf (Agent, Script, Migration, Refactor)** muss:

1. geprüft werden:

   * welche Annahmen falsch waren
   * wo implizites Verhalten auftrat
   * wo Pfade unerwartet waren

2. ergänzt werden:

```
## Lessons Learned – Run YYYY-MM-DD

- Problem:
- Ursache:
- Fix:
- Vermeidungsregel:
```

3. zusätzlich abgeleitet werden:

* neue Regel für Agenten
* neue Regel für Skills
* ggf. neue Validierung oder Guardrail

**Ohne diese Ergänzung gilt der Run als unvollständig.**

---

## Ableitung für Agent-/Skill-Setup

Diese Datei ist Grundlage für:

* `AGENTS.md`
* `copilot-instructions.md`
* strukturbezogene Skills

### Verbindliche Regeln für Agenten

* Es gibt genau eine Instanzwurzel
* Keine zweite parallele Struktur einführen
* Keine stillen Fallbacks implementieren
* Immer reale Pfadnutzung prüfen (nicht nur Code lesen)
* Dev und Prod immer gemeinsam denken
* Strukturänderungen nur entlang dieses Plans durchführen

---

## Verifikation (pro Welle)

Jede Welle muss enthalten:

* überprüfte Pfade (Logs, tatsächliche Zugriffe)
* getestete Endpunkte
* explizite Bestätigung:

  * was funktioniert
  * was bewusst nicht verändert wurde
* Risikoanalyse

---

## Abbruchkriterien

Sofort stoppen bei:

* unklarer Datenquelle
* widersprüchlicher Pfadnutzung
* potenzieller Auswirkung auf Prod-DB
* unerwarteter Nutzung von Legacy-Pfaden

---

## Zielzustand

Am Ende gilt:

* eine Struktur (`corapan/...`)
* keine runtime-Duplikate
* identisches Modell in Dev und Prod
* keine impliziten Fallbacks
* klare, überprüfbare Pfade
* stabile Grundlage für Templates

