# Welle 7 Lessons Integration Summary

Datum: 2026-03-20
Umgebung: Repo-only Dokumentations- und Guardrail-Integration
Scope: Ueberfuehrung der Lessons Learned aus Welle 1-6 in Architektur-Dokumentation, operative Guardrails und Agent-Regeln

## 1. Welche Lessons uebernommen wurden

Uebernommen wurden die Lessons aus [docs/state/LESSONS_LEARNED_INFRA_WELLE_1_6.md](LESSONS_LEARNED_INFRA_WELLE_1_6.md) zu:

- Single Source of Truth fuer operative Pfade
- Trennung von Spezialrealitaeten und allgemeinen Defaults
- Vorrang der Live-Realitaet vor Repo-Annahmen
- deterministischen Deploys und expliziter Tool-Validierung
- Compose-v1/v2-Konflikten, Ownership-Fragen und Netzwerk-Metadaten
- Schutz von Volumes, persistenter Datenpfade und Sonderzonen
- Trennung von runtime- und top-level-Realitaeten
- Safety-Regeln fuer Bereinigung, Disk Space und minimal-invasive Erstkorrekturen

## 2. Welche Kategorien gebildet wurden

Die Lessons wurden in drei dauerhafte Zielstrukturen ueberfuehrt:

- Architekturprinzipien und Systemdesign in [docs/architecture/infra-lessons.md](../architecture/infra-lessons.md)
- operative Guardrails und Anti-Patterns in [docs/architecture/infra-guardrails.md](../architecture/infra-guardrails.md)
- Entscheidungs- und Stop-Regeln fuer Agenten in [docs/architecture/agent-rules.md](../architecture/agent-rules.md)

Die inhaltlichen Kategorien darin sind:

- Architektur
- Deploy / CI/CD
- Docker / Compose
- Daten und Volumes
- Pfad- / Filesystem-Design
- Safety / Operations

## 3. Welche Guardrails definiert wurden

Definiert wurden insbesondere Guardrails fuer:

- zentrale Pfadauflosung statt impliziter Ableitung
- Vorrang der Produktionsrealitaet vor Repo-Annahmen
- Verbot von Compose v1 im Produktionspfad
- deterministischen Deploy-Bootstrap
- getrennte Pruefung von Realname, Projektname und logischer Compose-ID
- Repo-Fix vor Server-Fix bei aktiven Compose-Ressourcen
- Volumeschutz und Verbraucher-Matrix vor Cleanup
- eigene Defaults fuer Spezial-Deploys
- explizite Legacy-Klassifikation
- Verifikation gegen frische Prozesse
- Disk Space als harte Nebenbedingung
- Schreiberkorrektur vor Leser-Migration
- Tabuzonen fuer Auth, Secrets, BlackLab-Live-Pfade und produktive Stats-Kernbereiche

## 4. Welche Anti-Patterns identifiziert wurden

Explizit festgehalten wurden unter anderem:

- blindes `docker rm` auf DB-Container
- stille Compose-v1-Nutzung
- Gleichsetzung von Repo- und Live-Pfaden
- Behandlung paralleler Datenwurzeln als harmlose Duplikate
- Migration des Live-Lesers vor Korrektur des Standard-Schreibers
- `external: true` oder Netzwerk-Neuanlage als erster Fix fuer aktive Netze
- selbstaktualisierende Deploy-Skripte ohne vorgeschalteten Checkout
- Verifikation gegen Altprozesse oder Cache-Zustaende
- verdeckte Legacy statt expliziter Klassifikation

## 5. Warum keine Codeaenderungen notwendig waren

Die zugrunde liegenden technischen Probleme wurden in den vorherigen Wellen bereits forensisch ausgewertet und, wo noetig, minimal-invasiv korrigiert. Welle 7 hat keinen neuen Laufzeitkonflikt geloest, sondern die gewonnenen Erkenntnisse in dauerhafte Dokumentation und Guardrails ueberfuehrt. Deshalb waren nur Struktur-, Regel- und Referenzdokumente noetig.

## 6. Wie diese Integration zukuenftige Fehler verhindert

Die Integration reduziert Wiederholungsfehler auf drei Ebenen:

- Architektur: durch klare Prinzipien fuer Pfadquellen, Runtime-Daten und produktive Wahrheit
- Operations: durch harte Guardrails gegen nicht-deterministische Deploys, unklare Ownership und riskante Cleanup-Pfade
- Agentensteuerung: durch explizite Regeln fuer read-only Phasen, STOP-Bedingungen, Agent-Wahl und verbotene automatische Fixes

Damit werden Forensik-Ergebnisse nicht nur archiviert, sondern in wiederverwendbare Entscheidungsregeln fuer kuenftige Agentenlaeufe und Architekturarbeit ueberfuehrt.

## Verwandte Dokumente

- [docs/state/LESSONS_LEARNED_INFRA_WELLE_1_6.md](LESSONS_LEARNED_INFRA_WELLE_1_6.md)
- [docs/architecture/infra-lessons.md](../architecture/infra-lessons.md)
- [docs/architecture/infra-guardrails.md](../architecture/infra-guardrails.md)
- [docs/architecture/agent-rules.md](../architecture/agent-rules.md)