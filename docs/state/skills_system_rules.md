# Skills System Rules

Datum: 2026-03-20
Zweck: konsolidiertes, uebertragbares Regelwerk fuer Agenten- und Skill-Systeme
Quellenbasis: vorhandene Wellen-Summaries aus Entwicklungs-, Verifikations- und Produktionsinventur-Runs
Hinweis: eine separate Welle-1-Summary-Datei war im aktuellen Scope nicht vorhanden und wurde daher nicht als eigenstaendige Quelle verarbeitet

## 5.1 Core Rules (CRITICAL)

1. Alle operativen Pfade muessen aus einer expliziten, zentralen Quelle aufgeloest werden.
Kategorien: PATH_RESOLUTION, SYSTEM_ARCHITECTURE
Prioritaet: CRITICAL

2. Keine Komponente darf auf implizite Fallback-Pfade vertrauen.
Kategorien: PATH_RESOLUTION, DATA_INTEGRITY
Prioritaet: CRITICAL

3. Produktionsannahmen muessen aus der Live-Laufzeit, realen Mounts und aktiven Verbrauchern abgeleitet werden, nicht aus Dokumentation oder historischen Skripten.
Kategorien: PRODUCTION_SAFETY, DEPLOYMENT
Prioritaet: CRITICAL

4. Ein Deploy-Ziel darf nie von dem Pfad abweichen, den der produktive Verbraucher tatsaechlich liest.
Kategorien: DEPLOYMENT, DATA_INTEGRITY, PRODUCTION_SAFETY
Prioritaet: CRITICAL

5. Ein Pfad darf erst entfernt, zusammengelegt oder migriert werden, wenn Leser, Schreiber und Deploy-Ziele vollstaendig bekannt sind.
Kategorien: DATA_INTEGRITY, PRODUCTION_SAFETY, SYSTEM_ARCHITECTURE
Prioritaet: CRITICAL

6. Doppelte Strukturen sind als Risiko zu behandeln, bis ihre aktive Rolle explizit klassifiziert ist.
Kategorien: SYSTEM_ARCHITECTURE, PRODUCTION_SAFETY
Prioritaet: CRITICAL

7. Spezialrouten, Spezialpfade und Spezial-Backends brauchen eigene Verifikation; erfolgreiche Standardpfade sind kein Stellvertreterbeweis.
Kategorien: DEBUGGING, DATA_INTEGRITY
Prioritaet: CRITICAL

8. Fehlerklassifikation muss Ursache und Symptom trennen; ein Infrastruktur- oder Abhaengigkeitsfehler darf nicht als Pfad- oder Datenfehler maskiert werden.
Kategorien: DEBUGGING, PRODUCTION_SAFETY
Prioritaet: CRITICAL

9. Deploy-Orchestratoren, Runner, Sync-Skripte und Hilfsskripte sind Teil der Systemrealitaet und muessen wie produktive Komponenten analysiert werden.
Kategorien: DEPLOYMENT, SYSTEM_ARCHITECTURE
Prioritaet: CRITICAL

10. Produktionskritische Daten, Secrets, Datenbanken und Indizes duerfen nur nach expliziter Beleglage und mit klarer Schutzklassifikation angefasst werden.
Kategorien: PRODUCTION_SAFETY, DATA_INTEGRITY
Prioritaet: CRITICAL

## 5.2 Erweiterte Regeln

### PATH_RESOLUTION

1. Pfadauflosung muss deterministisch, zentral und wiederverwendbar sein.
Prioritaet: HIGH

2. Modul-lokale Pfadlogik ist zu vermeiden, wenn mehrere Komponenten auf dieselbe Struktur zugreifen.
Prioritaet: HIGH

3. Importzeitlich gebundene Pfadkonstanten sind riskant, wenn sich Umgebung oder Runtime-Kontext aendern kann.
Prioritaet: HIGH

4. Abgeleitete Unterpfade muessen aus derselben kanonischen Quelle stammen wie ihr Oberpfad.
Prioritaet: HIGH

5. Wenn ein Legacy-Pfad bestehen bleiben muss, ist er explizit zu markieren statt still weiterzuleben.
Prioritaet: MEDIUM

### DEPLOYMENT

1. Vor jeder deploy-relevanten Aussage ist zu pruefen, welcher Pfad live gelesen wird und welcher Pfad vom aktuellen Deploy-Unterbau beschrieben wird.
Prioritaet: CRITICAL

2. Deploy-Dokumentation, Orchestrator-Header und Unterbau-Skripte muessen konsistent sein; Widersprueche sind als Gefahr zu klassifizieren.
Prioritaet: HIGH

3. Schutzmechanismen wie Excludes, Blocklisten, DryRun, Validierungs-Gates und Ownership-Schritte sind Teil der fachlichen Wahrheit eines Deploy-Flows.
Prioritaet: HIGH

4. Ein Sync- oder Publish-Skript darf nicht als harmlos gelten, nur weil es nicht im Hauptworkflow liegt.
Prioritaet: HIGH

5. Manuelle oder legacy Deploy-Pfade muessen separat klassifiziert werden und duerfen nicht mit dem Standardpfad vermischt werden.
Prioritaet: MEDIUM

### DATA_INTEGRITY

1. Doppelte Datenbaeume sind solange als potenziell inkonsistent zu behandeln, bis Inode-, Leser- und Schreiberlage geklaert sind.
Prioritaet: CRITICAL

2. Cache-, Temp- und abgeleitete Dateien duerfen nicht mit kanonischen Quelldaten verwechselt werden.
Prioritaet: HIGH

3. Selektive Ausnahmen innerhalb geschuetzter Bereiche muessen explizit allowlist-basiert und nicht implizit sein.
Prioritaet: HIGH

4. Nicht jeder existierende Pfad ist ein aktiver Pfad; Existenz ist kein Nutzungsbeweis.
Prioritaet: HIGH

5. Wenn Daten an mehreren Orten auftauchen, muss fuer jeden Ort getrennt beantwortet werden: Quelle, Spiegel, Cache, Legacy oder aktives Ziel.
Prioritaet: HIGH

### PRODUCTION_SAFETY

1. Live-Systeme schlagen Repo-Annahmen.
Prioritaet: CRITICAL

2. Produktionsaenderungen sind blockiert, solange Beleglage oder Verbraucher-Matrix unvollstaendig sind.
Prioritaet: CRITICAL

3. Secrets, Auth-Daten, Kern-Datenbanken und Suchindizes sind gesondert zu klassifizieren und nie implizit in Strukturarbeiten einzubeziehen.
Prioritaet: CRITICAL

4. Eine scheinbar leere oder ungenutzte Struktur darf in Produktion erst nach Laufzeit- und Deploy-Analyse als entfernbar gelten.
Prioritaet: HIGH

5. Unterschiedliche aktive Modelle in demselben System muessen offen benannt werden; Harmonisierung darf nicht durch Wunschannahmen ersetzt werden.
Prioritaet: HIGH

### DEBUGGING

1. Verifikation muss gegen einen frischen, eindeutig kontrollierten Prozess stattfinden, wenn alte Prozesse, Caches oder stale Zustande Ergebnisse verfälschen koennen.
Prioritaet: HIGH

2. Debug-Logging soll Pfadauflosung, Backend-Auswahl und konkrete Entscheidungswege sichtbar machen, nicht nur Fehler am Ende melden.
Prioritaet: HIGH

3. Ein reproduzierter Fehler ist erst dann korrekt klassifiziert, wenn Pfad, Abhaengigkeiten, Laufzeitkontext und Rueckgabecode zusammen betrachtet wurden.
Prioritaet: HIGH

4. Spezialfaelle brauchen gerichtete Regressionstests statt allgemeiner Green-Checks.
Prioritaet: HIGH

5. Falsche Fehlercodes erzeugen falsche Reparaturen; Status und Meldung muessen die eigentliche Fehlerklasse widerspiegeln.
Prioritaet: MEDIUM

### SYSTEM_ARCHITECTURE

1. Es muss genau einen klaren strukturellen Ursprung fuer operative Daten geben.
Prioritaet: CRITICAL

2. Wenn mehrere Wahrheiten existieren, sind sie nicht als gleichwertig zu behandeln, sondern als aktiv, legacy, redundant oder gefaehrlich zu klassifizieren.
Prioritaet: CRITICAL

3. Architekturarbeit darf keine impliziten Nebenmigrationen von Daten, Deploy-Logik oder Betriebsmodellen ausloesen.
Prioritaet: HIGH

4. Nicht vereinheitlichte Randbereiche muessen bewusst isoliert und benannt werden, statt die Gesamtarchitektur still zu unterlaufen.
Prioritaet: HIGH

5. Ein zentrales Systemmodell ist nur dann belastbar, wenn Code, Laufzeit und Deploy-Pfade darauf ausgerichtet sind.
Prioritaet: HIGH

## 5.3 Anti-Patterns

1. Implizite Fallbacks auf historische oder bequeme Pfade.
Kategorien: PATH_RESOLUTION, SYSTEM_ARCHITECTURE
Prioritaet: CRITICAL

2. Annahme, dass dokumentierte oder konfigurierte Pfade automatisch die live genutzten Pfade sind.
Kategorien: PRODUCTION_SAFETY, DEPLOYMENT
Prioritaet: CRITICAL

3. Bereinigung oder Migration ohne vollstaendige Leser-/Schreiber-/Deploy-Matrix.
Kategorien: DATA_INTEGRITY, PRODUCTION_SAFETY
Prioritaet: CRITICAL

4. Behandlung von Doppelstrukturen als rein kosmetisches Problem.
Kategorien: SYSTEM_ARCHITECTURE, DATA_INTEGRITY
Prioritaet: CRITICAL

5. Gleichsetzung von erfolgreichem Smoke-Test auf Standardrouten mit Systemgesundheit aller Spezialpfade.
Kategorien: DEBUGGING
Prioritaet: HIGH

6. Diagnose eines Backend- oder Infrastrukturproblems als Dateinichtfund oder Pfadfehler.
Kategorien: DEBUGGING
Prioritaet: HIGH

7. Analyse von Deploy-Flows ohne Orchestratoren, Runner oder Sync-Helfer.
Kategorien: DEPLOYMENT
Prioritaet: HIGH

8. Nutzung von Existenz, Dateigroesse oder Verzeichnisinhalt als alleiniger Aktivitaetsbeweis.
Kategorien: DATA_INTEGRITY
Prioritaet: HIGH

9. Verifikation gegen lang laufende Prozesse mit unbekanntem Zustand.
Kategorien: DEBUGGING
Prioritaet: MEDIUM

10. Lokale Modulentscheidungen statt zentraler Resolver fuer dieselbe Struktur.
Kategorien: PATH_RESOLUTION
Prioritaet: MEDIUM

## 5.4 Agent-Anweisungen

1. Lies zuerst Laufzeitrealitaet, dann kanonische Konfiguration, dann Implementierung, dann Dokumentation.

2. Erstelle fuer struktur- oder deploy-relevante Aufgaben immer zuerst eine Konfliktkarte:
active, legacy, redundant, dangerous.

3. Suche gezielt nach impliziten Fallbacks, importzeitlichen Pfadbindungen, lokalen Sonderauflösungen und verdeckten Legacy-Pfaden.

4. Wenn ein Pfad kritisch ist, beantworte explizit vier Fragen:
wer liest, wer schreibt, wer deployt, wer schuetzt.

5. Behandle Orchestratoren, Runner, Sync-Unterbau und Hilfsskripte als produktive Systemteile.

6. Verifiziere Spezialrouten und Spezialpfade separat; leite ihre Korrektheit nicht aus allgemeinen Erfolgen ab.

7. Unterscheide bei Fehlern systematisch zwischen Pfadproblem, Zustandsproblem, Cacheproblem, Abhaengigkeitsproblem und Infrastrukturproblem.

8. Wenn mehrere reale Strukturen gleichzeitig existieren, plane keine Bereinigung, bevor aktive Verbraucher- und Schreiberbeziehungen belegt sind.

9. Nutze frische Prozesse oder isolierte Verifikationskontexte, wenn alte Prozesse, Caches oder Nebenwirkungen das Ergebnis verfälschen koennen.

10. Formuliere Regeln und Diagnosen auf Strukturebene, nicht als Einmalfall oder lokale Ausnahme.

## Herkunft der Regeln

Die Regeln wurden aus wiederkehrenden Fehlerklassen extrahiert:

- implizite Pfadauflosung
- unsichtbare Doppelstrukturen
- falsch ausgerichtete Deploy-Ziele
- unvollstaendige Produktionsannahmen
- unzureichende Verifikation von Spezialpfaden
- Verwechslung von Backend- und Pfadfehlern

Das Regelwerk ist bewusst allgemein formuliert und fuer andere Projekte mit Pfad-, Deploy-, Laufzeit- und Betriebslogik uebertragbar.