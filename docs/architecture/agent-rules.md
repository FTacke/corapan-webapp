# Agent Rules

**Scope:** Regeln fuer kuenftige Agentenlaeufe mit Infra-, Deploy-, Pfad- oder Persistenzbezug  
**Source-of-truth:** [docs/state/LESSONS_LEARNED_INFRA_WELLE_1_6.md](../state/LESSONS_LEARNED_INFRA_WELLE_1_6.md)

## Ziel

Dieses Dokument uebersetzt die Infra-Lessons in konkrete Entscheidungsregeln fuer Agentenlaeufe. Es trennt Analyse von Eingriff, macht Stop-Bedingungen explizit und reduziert das Risiko von Repo- oder Serveraenderungen ohne ausreichende Verifikation.

## Agent-Wahl

### Repo-Agent verwenden, wenn

- die Aufgabe auf Repository-Dateien, Dokumentation oder statische Konfigurationsaenderungen begrenzt ist
- ein Konflikt mit einer Repo-seitigen Metadaten- oder Schluesselanpassung geloest werden kann
- statische Verifikation ausreicht
- keine Live-System-Realitaet veraendert werden darf

### Server-Agent verwenden, wenn

- die produktive Wahrheit nur ueber den Live-Host beobachtbar ist
- Mounts, laufende Container, echte Compose-Ressourcen, Runner-Workspaces oder Host-Dateibaeume verifiziert werden muessen
- unklar ist, ob Repo und Live-System voneinander abweichen
- ein Repo-Fix nur dann sicher ist, wenn vorher Live-Realitaet belegt wurde

### Beide kombinieren, wenn

- zuerst live forensisch geklaert werden muss, welche Realitaet aktiv ist
- danach ein eng begrenzter Repo-Fix die sicherste Korrektur ist

## Read-only Pflicht

Ein Agent muss read-only bleiben, wenn eine der folgenden Bedingungen gilt:

- die aktive Produktionsrealitaet ist noch nicht belegt
- mehrere plausible Pfade, Netzwerke, Container oder Deploy-Flows konkurrieren
- ein Eingriff aktive Daten, Volumes, Secrets oder Live-Leserpfade beruehren koennte
- die Ursache ist noch nicht sauber auf Repo-Metadaten, Live-Tooling oder stale Artefakte eingegrenzt

Read-only bedeutet hier insbesondere:

- keine Service-Starts oder -Stops
- keine Deploys
- keine Migrationen
- keine administrativen Reset- oder Bootstrap-Skripte
- keine destruktiven Docker- oder Git-Kommandos

## STOP-Bedingungen

Ein Agent muss anhalten und eskalieren, wenn:

- nicht sicher bestimmbar ist, welcher Host, Checkout, Container oder Pfad aktiv ist
- mehrere konkurrierende Produktionswahrheiten nicht sauber klassifiziert werden koennen
- ein geplanter Fix aktive Volumes, Auth-Daten, `passwords.env`, BlackLab-Live-Pfade oder produktive Stats-Kernpfade beruehren wuerde
- ein vorgeschlagener Eingriff einen Recreate, Cleanup oder sonstige destruktive Servermassnahmen erfordern wuerde
- der freie Speicherplatz als harte Nebenbedingung kritisch ist und der Eingriff Build-, Recreate- oder Publish-Last erzeugen wuerde

## Kein automatischer Fix erlaubt, wenn

- die Ursache nur vermutet, aber nicht belegt ist
- Live-Reader und Default-Schreiber noch nicht als Matrix aufgenommen wurden
- ein Server-Fix nur deshalb attraktiv wirkt, weil der Repo-Zustand noch nicht sauber geprueft wurde
- die bereinigte Ressource aktiv genutzt sein koennte, auch wenn sie gerade nicht laeuft
- eine alte V1-Ressource, ein Runner-Workspace oder ein paralleler Baum nur scheinbar inaktiv aussieht

## Standardablauf fuer Infra-Faelle

1. Produktions- oder Dev-Realitaet bestimmen.
2. Aktive Quellen gegen Repo und Doku klassifizieren.
3. Leser, Schreiber und Deploy-Ziele identifizieren.
4. Risikozonen und Tabubereiche abgrenzen.
5. Kleinsten sicheren Eingriff bestimmen.
6. Erst danach dokumentieren oder aendern.

## Safety-First-Regeln

- Zuerst den realen Ausfuehrungsort eines Deploys verifizieren, dann das Werkzeug.
- Zuerst Metadaten- oder Repo-Konflikte pruefen, dann Server-Bereinigung erwägen.
- Zuerst die Schreiberseite korrigieren, dann ueber Leser- oder Strukturmigration nachdenken.
- Zuerst Volumes, Secrets und Live-Leserpfade isolieren, dann ueber Cleanup sprechen.
- Zuerst gegen frische Prozesse oder isolierte Ports verifizieren, dann Regressionen behaupten.

## Erlaubte automatische Eingriffe

Ein Agent darf ohne weitere Eskalation automatisch handeln, wenn alle folgenden Punkte erfuellt sind:

- die Produktions- oder Dev-Realitaet ist belegt
- der Eingriff ist rein repo-seitig oder rein dokumentarisch
- keine laufkritischen Komponenten werden veraendert
- keine Daten, Volumes, Secrets, Auth- oder BlackLab-Live-Pfade werden beruehrt
- die statische oder read-only Verifikation deckt den Konflikt eindeutig ab

## Verwandte Dokumente

- [docs/state/LESSONS_LEARNED_INFRA_WELLE_1_6.md](../state/LESSONS_LEARNED_INFRA_WELLE_1_6.md)
- [docs/architecture/infra-lessons.md](infra-lessons.md)
- [docs/architecture/infra-guardrails.md](infra-guardrails.md)
- [docs/state/Welle_7_lessons_integration_summary.md](../state/Welle_7_lessons_integration_summary.md)