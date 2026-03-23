# Infra Guardrails

**Scope:** operative Guardrails aus den Infra-Lessons Welle 1-6  
**Source-of-truth:** [docs/state/LESSONS_LEARNED_INFRA_WELLE_1_6.md](../state/LESSONS_LEARNED_INFRA_WELLE_1_6.md)

## Guardrails

### 1. Kein impliziter Pfad fuer operative Daten

- **Regel:** Operative Pfade fuer Daten, Media, Metadata, Stats, Logs und Exporte muessen ueber zentrale Resolver oder klar benannte Infrastruktur-Helper laufen.
- **Begruendung:** Lokale Modulableitungen erzeugen Drift zwischen Dev, Prod und Spezial-Deploys.
- **Beispiel:** Ein neuer Exportpfad darf nicht relativ zu einem Modulordner zusammengesetzt werden, wenn es bereits einen kanonischen Runtime-Resolver gibt.

### 2. Produktionsrealitaet geht vor Repo-Annahme

- **Regel:** Bei produktionsrelevanten Entscheidungen muessen zuerst Live-Mounts, laufende Container, reale Dateibaeume, aktive Writer und effektive ENV-Werte geprueft werden.
- **Begruendung:** Repo und Doku koennen alte oder nur teilweise gueltige Modelle enthalten.
- **Beispiel:** Ein Pfad darf nicht umgestellt werden, nur weil er im Compose-File plausibel aussieht, wenn der Live-Reader nachweislich woanders liest.

### 3. Kein docker-compose v1 im Produktionspfad

- **Regel:** Produktive Deploy-Pfade duerfen Compose v1 nicht still verwenden; das effektive Compose-CLI muss explizit validiert und bei Inkompatibilitaet hart blockiert werden.
- **Begruendung:** Moderne Docker-Hosts koennen mit Compose v1 spaet und intransparent scheitern.
- **Beispiel:** Ein Deploy-Skript muss `docker compose` bevorzugen und v1 nicht als stillen Fallback behandeln.

### 4. Deploy-Bootstrap muss deterministisch sein

- **Regel:** Wenn ein Workflow ein Skript aus einem persistenten Ziel-Checkout startet, muss dieser Checkout vor dem Skriptstart auf den Trigger-Commit gesetzt werden.
- **Begruendung:** Sonst sind Aenderungen am Deploy-Skript selbst im ersten Lauf nicht wirksam.
- **Beispiel:** Vor `bash scripts/deploy_prod.sh` muss der Ziel-Checkout auf `${GITHUB_SHA}` gebracht werden.

### 5. Compose-Ressourcen in drei Ebenen pruefen

- **Regel:** Bei Compose-Konflikten sind Realname, Projektname und logische Compose-ID getrennt zu pruefen.
- **Begruendung:** Ein korrekter Realname beweist nicht, dass Labels, Ownership und Repo-Metadaten konsistent sind.
- **Beispiel:** Ein bestehendes Netzwerk kann `corapan-network-prod` heissen und dennoch wegen eines abweichenden logischen Keys im Repo konfliktbehaftet sein.

### 6. Repo-Fix vor Server-Fix bei aktiven Compose-Ressourcen

- **Regel:** Wenn eine aktive Compose-Ressource nur an logischen Metadaten vom Repo abweicht, ist zuerst die Repo-seitige Schluesselangleichung zu waehlen.
- **Begruendung:** Server-Bereinigung gefaehrdet aktive Netzwerke, Container und Ownership-Zustaende unnoetig.
- **Beispiel:** Ein Netzwerk-Key im Compose-File wird angepasst, statt `external: true` einzufuehren oder ein aktives Netzwerk neu anzulegen.

### 7. Volumes sind Hochrisiko-Persistenz

- **Regel:** Bei DB- und Persistenzkonflikten muessen Container, Service-Definition und Volume getrennt bewertet werden; Volumes sind tabu, solange keine klare Inaktivitaet belegt ist.
- **Begruendung:** Ein Containerproblem ist nicht automatisch ein Datenproblem, aber ein falscher Cleanup kann echte Persistenz zerstoeren.
- **Beispiel:** Ein stale DB-Container darf nicht blind entfernt werden, ohne Labels, Mounts und Volumes vorher getrennt zu pruefen.

### 8. Keine Bereinigung ohne Verbraucher-Matrix

- **Regel:** Kein produktiver Pfad, Container, Netzwerk oder Datenbaum darf entfernt, umgehaengt oder vereinheitlicht werden, bevor alle Leser, Schreiber und Deploy-Ziele explizit bekannt sind.
- **Begruendung:** Unsichtbare Operator-Routinen, Runner oder Sync-Skripte koennen weiterhin daran haengen.
- **Beispiel:** `blacklab_index` oder `logs` sind kein Cleanup-Kandidat, solange nicht alle Live- und Default-Schreiber inventarisiert sind.

### 9. Spezial-Deploys brauchen eigene Defaults

- **Regel:** Wenn ein Spezial-Deploy bewusst nicht dem allgemeinen Daten- oder Runtime-Modell folgt, muss er einen eigenen expliziten Default haben.
- **Begruendung:** Allgemeine Defaults verschieben Spezialrealitaeten oft auf den falschen Pfad.
- **Beispiel:** BlackLab-Publish darf nicht still denselben Remote-DataRoot wie allgemeine runtime-first data/media-Deploys uebernehmen.

### 10. Legacy muss explizit klassifiziert werden

- **Regel:** Nicht entfernbarer Legacy ist als aktiv, dupliziert, ungenutzt oder blockiert explizit zu markieren.
- **Begruendung:** Versteckte Legacy erzeugt neue Drift und erschwert sichere Folgeeingriffe.
- **Beispiel:** Ein top-level-Pfad bleibt dokumentiert als aktive Sonderrealitaet, statt still als scheinbar harmlose Dublette weiterzulaufen.

### 11. Verifikation gegen frische Prozesse oder isolierte Ports

- **Regel:** Pfad- und Resolver-Fixes duerfen nicht gegen alte Prozesse, Cache-Zustaende oder unklare Instanzen verifiziert werden.
- **Begruendung:** Sonst wirken korrekte Fixes falsch oder fehlerhafte Zustandsreste wie echte Regressionen.
- **Beispiel:** Ein Media-Fix wird gegen einen frischen Dev-Prozess oder einen isolierten Port getestet.

### 12. Begrenzter Disk Space ist eine harte Betriebsbedingung

- **Regel:** Vor produktiven Rebuild-, Recreate- oder Publish-Runs ist freier Speicherplatz als Go/No-Go-Bedingung zu pruefen.
- **Begruendung:** Build-Cache, Images und produktive Daten teilen sich dieselbe Platte; Platzmangel kann halbfertige Zustaende erzeugen.
- **Beispiel:** Ein Recreate wird nicht gestartet, wenn der Host bereits kritisch ausgelastet ist.

### 13. Erste Eingriffe korrigieren die Schreiberseite

- **Regel:** Bei parallelen produktiven Dateibaeumen ist zuerst der Default-Schreiber zu korrigieren, nicht der Live-Leser umzubauen.
- **Begruendung:** Der Live-Leser ist oft stabil, waehrend der neue Standard-Writer bereits falsch zeigt.
- **Beispiel:** Ein Publish-Default wird repariert, bevor ein laufender Reader auf einen anderen Baum migriert wird.

### 14. Produktive Sonderzonen sind Tabubereiche

- **Regel:** `passwords.env`, Auth-Daten, Datenbank-Volumes, aktive BlackLab-Leserpfade und produktive Analytics-/Stats-Kernpfade duerfen nicht in allgemeine Cleanup- oder Vereinheitlichungslaeufe einbezogen werden.
- **Begruendung:** Diese Bereiche koppeln Persistenz, Authentifizierung und externe Systeme mit hohem Schaedigungsrisiko.
- **Beispiel:** Ein allgemeiner Struktur-Fix darf keine Auth-Volumes oder BlackLab-Live-Pfade mitumhaengen.

## Anti-Patterns

- blindes `docker rm` auf DB-Container ohne getrennte Pruefung von Laufstatus, Labels, Mounts und Volumes
- stille Weiterverwendung von Compose v1 nur weil der Befehl auf dem Host existiert
- Gleichsetzung von Repo-Pfaden und Live-Pfaden ohne belegte Mount-Realitaet
- Behandlung von runtime- und top-level-Baeumen als harmlose Duplikate
- Migration von Live-Leserpfaden vor der Korrektur des Default-Schreibers
- `external: true`, Netzwerk-Neuanlage oder Server-Bereinigung als erster Fix fuer aktive Compose-Netzwerke
- Deploy-Skripte, die sich erst waehrend des Laufs selbst aktualisieren
- Verifikation gegen alte Prozesse, Caches oder unklare Instanzen
- Behandlung von BlackLab wie eines normalen data/media-Deploys
- verdeckt weiterlaufende Legacy-Pfade statt expliziter Klassifikation
- Einmischung von Secrets-, Volume- oder Auth-Pfaden in allgemeine Cleanup-Laeufe

## Verwandte Dokumente

- [docs/state/LESSONS_LEARNED_INFRA_WELLE_1_6.md](../state/LESSONS_LEARNED_INFRA_WELLE_1_6.md)
- [docs/architecture/infra-lessons.md](infra-lessons.md)
- [docs/architecture/agent-rules.md](agent-rules.md)
- [docs/state/Welle_7_lessons_integration_summary.md](../state/Welle_7_lessons_integration_summary.md)