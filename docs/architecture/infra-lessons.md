# Infra Lessons

**Scope:** verdichtete Infrastruktur- und Deploy-Lessons aus den Wellen 1-6  
**Source-of-truth:** [docs/state/LESSONS_LEARNED_INFRA_WELLE_1_6.md](../state/LESSONS_LEARNED_INFRA_WELLE_1_6.md)

## Zweck

Dieses Dokument fasst die produktionsrelevanten Infra-Lessons in eine dauerhafte Architektur-Sicht zusammen. Es ersetzt keine Detailforensik, sondern destilliert die bindenden Systemprinzipien fuer kuenftige Repo- und Serverarbeit.

## Kernprinzipien

### 1. Single Source of Truth fuer operative Pfade

Operative Pfade duerfen nicht lokal in Modulen, Skripten und Routen konkurrierend zusammengesetzt werden. Pfadauflosung muss ueber zentrale Resolver oder klar benannte Infrastruktur-Helper erfolgen, damit Dev und Prod dieselbe Ressource auch tatsaechlich als dieselbe Ressource behandeln.

### 2. Live-Realitaet schlaegt Repo-Annahme

Produktionsentscheidungen duerfen nicht aus Repository-Struktur, Compose-Datei und Dokumentation allein abgeleitet werden. Massgeblich sind reale Mounts, laufende Container, aktive Writer, ENV-Werte und beobachtbare Dateibaeume.

### 3. Code und Runtime-Daten muessen getrennt gedacht werden

Repository-Code, Ziel-Checkout, Runtime-Daten, Volumes und operatorverwaltete Sonderzonen sind unterschiedliche Realitaeten. Fehler entstehen, wenn Code-Pfade, Runtime-Pfade und persistente Daten stillschweigend als austauschbar behandelt werden.

### 4. Deterministische Deploys haben Vorrang vor bequemen Deploys

Ein produktiver Deploy muss immer klar machen, welcher Host, welcher Checkout, welches Skript und welches CLI den Eingriff ausfuehren. Nicht-deterministische Self-Update-Muster oder implizite Tool-Auswahl verschieben Probleme nur spaeter in den Lauf.

### 5. Spezialrealitaeten brauchen eigene Defaults

Nicht jeder produktive Datenpfad folgt demselben Modell. BlackLab, Auth, Stats, data/media-Deploys und operatorverwaltete Secrets duerfen nicht ueber einen allgemeinen Default vereinheitlicht werden, wenn ihre produktive Wahrheit abweicht.

## Kategorien der Lessons

### Architektur

- zentrale Resolver statt lokaler Pfadlogik
- keine impliziten Defaults fuer kritische operative Pfade
- Produktionsrealitaet als bindende Quelle fuer Architekturentscheidungen

### Deploy / CI/CD

- realer Ausfuehrungsort zuerst
- self-updating Deploy-Skripte sind ohne vorgeschalteten Checkout nicht self-applying
- Tool-Auswahl und Versionskontext muessen im Deploy explizit validiert werden
- Workflows und Deploy-Helfer sind Teil der produktiven Pfadrealitaet

### Docker / Compose

- Compose v1 ist kein tragfaehiger Produktionspfad auf modernen Docker-Hosts
- Realname, Projektname und logische Compose-ID sind getrennte Ebenen
- bei Metadatenkonflikten hat der Repo-Fix Vorrang vor Server-Bereinigung
- stale V1-Artefakte koennen Ownership-Konflikte auch ohne aktiven Lauf ausloesen

### Daten und Volumes

- Volumes sind die kritische Persistenzgrenze
- Datenwurzeln enthalten Teilpfade mit sehr unterschiedlicher Kritikalitaet
- Deploy-Unterbau braucht Schutzregeln fuer persistente Kernbereiche

### Pfad- und Filesystem-Design

- runtime und top-level sind keine Alias-Strukturen
- Live-Leser und Default-Schreiber muessen fuer dieselbe Ressource kongruent sein
- Legacy darf nicht versteckt weiterlaufen
- Verifikation muss gegen frische Prozesse oder isolierte Ports erfolgen

### Safety / Operations

- erste sichere Eingriffe korrigieren meist die Schreiberseite, nicht die Leserseite
- keine Bereinigung ohne Verbraucher-Matrix
- produktive Sonderzonen sind explizite Tabubereiche
- begrenzter Disk Space ist eine operative Go/No-Go-Bedingung

## Architekturfolgen fuer dieses Repository

### Pfade und Resolver

Pfade fuer App-Daten, Medien, Statistiken, BlackLab, Secrets und Logs duerfen nur ueber kanonische, nachvollziehbare Quellen aufgeloest werden. Jede neue Pfadlogik muss explizit zeigen, ob sie einen bestehenden Resolver nutzt oder bewusst einen Spezialpfad modelliert.

### Deploy-Design

Produktive Deploys muessen einen deterministischen Bootstrap haben. Das schliesst ein:

- den Ziel-Checkout vor Skriptaufrufen auf den Trigger-Commit zu bringen
- das effektive Compose-Kommando und seine Version explizit zu validieren
- Live-Ressourcen nicht vorschnell umzudeuten, wenn nur die Repo-Metadaten abweichen

### Daten- und Persistenzdesign

Container, Volumes, bind mounts und operatorverwaltete Dateien duerfen nie als eine gemeinsame, beliebig bereinigbare Schicht behandelt werden. Persistente Kernbereiche brauchen eigene Safety-Regeln und duerfen nicht aus allgemeinen Cleanup- oder Vereinheitlichungsannahmen heraus veraendert werden.

## Operative Schlussfolgerung

Die Wellen 1-6 zeigen kein einzelnes Problem, sondern ein Muster: Drift entsteht dort, wo implizite Ableitungen, parallele Wahrheiten und unsichtbare Writer zusammenkommen. Das Gegenmittel sind deterministische Deploys, explizite Pfadquellen, getrennte Behandlung von Runtime-Daten und Code sowie hart dokumentierte Tabuzonen.

## Verwandte Dokumente

- [docs/state/LESSONS_LEARNED_INFRA_WELLE_1_6.md](../state/LESSONS_LEARNED_INFRA_WELLE_1_6.md)
- [docs/architecture/infra-guardrails.md](infra-guardrails.md)
- [docs/architecture/agent-rules.md](agent-rules.md)
- [docs/state/Welle_7_lessons_integration_summary.md](../state/Welle_7_lessons_integration_summary.md)