# Prod Migration Plan

## Zielbild

Vor dem nächsten produktiven Push soll ein belastbares Bild darüber vorliegen,

* wie **Repo-Sollzustand** und **Server-Istzustand** auseinanderlaufen,
* welche Risiken beim nächsten Deploy real bestehen,
* welche Reihenfolge für einen kontrollierten Prod-Cutover nötig ist,
* wie **Auth/Postgres** und weitere Kernfunktionen im Fehlerfall schnell wiederhergestellt werden können,
* und wie danach die Repository-Struktur sauber auf `corapan/` als Git-Root angehoben wird.

Das Ziel ist **nicht**, dass beim ersten Push sofort alles perfekt läuft. Das Ziel ist ein Setup, in dem ein kontrollierter Deploy verantwortbar ist und bei Problemen eine Wiederherstellung in überschaubarer Zeit möglich bleibt.

---

## Leitprinzipien

1. **Server-Istzustand geht vor Repo-Annahme.** Nichts über aktive Pfade, Mounts, Container oder Config raten.
2. **Repo-Sollzustand muss explizit dokumentiert werden.** Keine impliziten Dev-Annahmen.
3. **BlackLab-Index nie im laufenden Betrieb blind überschreiben.** Der bekannte Korruptionsfall ist ein harter Risikofaktor.
4. **Auth/Postgres ist Go/No-Go-kritisch.** Ein Deploy ist nur vertretbar, wenn Wiederherstellung klar und testbar beschrieben ist.
5. **Jeder Run erzeugt oder aktualisiert Dokumentation in `docs/prod_migration/`.** Nichts Entscheidungsrelevantes bleibt nur im Chat.

---

## Rollen: Repo-Agent vs. Server-Agent

### Repo-Agent

Der Repo-Agent ist zuständig für den **Sollzustand**:

* Struktur, Pfadannahmen und Runtime-Root im Code
* Compose-/Deploy-/Entrypoint-Logik im Repository
* Env-Variablen und Config-Quellen
* Auth-/DB-Annahmen im Code
* BlackLab-Pfadannahmen, Index-Handling, Startreihenfolge
* Risiken durch die spätere Umbenennung `webapp -> app`
* Risiken durch das spätere Anheben des Git-Roots auf `corapan/`

Der Repo-Agent darf **nicht** behaupten, was auf prod tatsächlich läuft, sondern nur:

* was das Repo erwartet,
* wo diese Erwartungen hart kodiert sind,
* welche Risiken daraus bei Abweichung entstehen.

### Server-Agent

Der Server-Agent ist zuständig für den **Istzustand**:

* aktive Container / Compose-Projekte / Services
* reale Mounts und Host-Pfade
* reale Config-Dateien und deren Speicherorte
* reale Env-Werte und Env-Quellen
* reale Auth-/DB-Anbindung
* realer BlackLab-Indexpfad und Betriebszustand
* reale Deploy-Mechanik auf dem Server
* Backup-/Rollback-/Restart-Möglichkeiten

Der Server-Agent darf **nicht** den Repo-Sollzustand erfinden, sondern muss ihn aus den dokumentierten Repo-Ergebnissen gegenprüfen.

---

## Arbeitsmodus

Jede Welle besteht aus:

1. **Repo-Agent liefert Sollbild / erwartete Auswirkungen**
2. **Server-Agent verifiziert gegen Realität**
3. **Repo-Agent präzisiert bei Bedarf die Ableitungen im Code**
4. **Server-Agent formuliert daraus Betriebsentscheidung und Cutover-Reihenfolge**
5. **Ergebnisse werden in `docs/prod_migration/` gespeichert**

Dateinamenschema pro Run:

* `YYYY-MM-DD_repo_<thema>.md`
* `YYYY-MM-DD_server_<thema>.md`
* optional konsolidiert: `YYYY-MM-DD_<thema>_summary.md`

---

## Welle 1: Repo-Sollzustand hart erfassen

### Ziel

Ein belastbares, textlich sauberes Sollbild aus dem aktuellen stabilen Dev-Stand erzeugen.

### Repo-Agent prüft

* Welche Verzeichnisse im Code als Runtime-Root angenommen werden
* Welche Pfade für `data`, `config`, `media`, BlackLab, Auth, Migrations, Seeds etc. erwartet werden
* Welche Env-Variablen Pflicht sind und welche Defaults gefährlich wären
* Welche Deploy-Skripte, Entry-Points, Compose-Dateien und Shell-Helfer produktionsrelevant sind
* Welche Teile noch historisch auf alte Strukturformen deuten
* Welche Stellen bei einem Deploy in Altpfade schreiben würden
* Welche Teile beim späteren Rename `webapp -> app` brechen würden
* Welche Teile beim Git-Root-Umzug auf `corapan/` angepasst werden müssen

### Ergebnis

Ein Repo-Dokument, das mindestens enthält:

1. Kanonischer Sollzustand
2. Pfadmatrix
3. Pflicht-Env-Variablen
4. Deploy-relevante Skripte
5. Altstruktur-Risiken
6. Rename-/Git-Root-Risiken
7. Offene Unsicherheiten

### Ablage

`docs/prod_migration/YYYY-MM-DD_repo_runtime_sollbild.md`

---

## Welle 2: Server-Istzustand forensisch erfassen

### Ziel

Ohne Änderung am System exakt feststellen, wie prod derzeit wirklich läuft.

### Server-Agent prüft

* Welche Compose-Projekte und Container aktiv sind oder als Altartefakte vorhanden sind
* Welche Volumes und Bind-Mounts effektiv genutzt werden
* Welche Host-Pfade in `/srv/webapps/corapan/app` und angrenzend relevant sind
* Welche Env-Dateien, Secret-Dateien oder Service-Units aktiv sind
* Welche Config-Pfade real gelesen werden
* Wo Postgres-Daten real liegen, wie sie eingebunden sind und wie Auth darauf zeigt
* Wo BlackLab-Daten/Indexe real liegen und ob laufende Prozesse darauf zugreifen
* Wie Restart und Deploy aktuell tatsächlich ausgeführt werden

### Ergebnis

Ein Server-Dokument, das mindestens enthält:

1. Beobachteter Istzustand
2. Aktive Container-/Mount-Matrix
3. Env-/Config-Quellen
4. Auth/Postgres-Istbild
5. BlackLab-Istbild
6. Altartefakte und Konfliktquellen
7. Unsicherheiten oder blinde Flecken

### Ablage

`docs/prod_migration/YYYY-MM-DD_server_prod_reality_audit.md`

---

## Welle 3: Soll-Ist-Abgleich mit Bruchstellenanalyse

### Ziel

Glasklar benennen, was beim nächsten Blind-Deploy bricht und was unkritisch ist.

### Repo-Agent liefert

* präzise Referenz auf Code-/Script-Stellen, die bestimmte Pfade oder Reihenfolgen erwarten
* Einschätzung, welche Repo-Annahmen zwingend erfüllt sein müssen

### Server-Agent verifiziert

* welche dieser Annahmen auf prod bereits erfüllt sind
* welche nicht
* wo Deploy in Altstruktur, falsche Mounts oder falsche Runtime-Wurzeln schreiben würde

### Bewertungsachsen

* Auth / Postgres
* BlackLab / Index
* Config / Runtime-Root
* Docker / Compose / Mount-Logik
* Deploy / Restart / Reihenfolge
* Dateirechte / Ownership, falls relevant

### Ergebnis

Ein konsolidierter Bruchstellenbericht mit:

1. Blind-Deploy-Folgen
2. Unkritische Bereiche
3. Vorbedingungen für sicheren Deploy
4. No-Go-Bedingungen

### Ablage

`docs/prod_migration/YYYY-MM-DD_prod_gap_analysis.md`

---

## Welle 4: Wiederherstellbarkeit absichern (Auth/Postgres zuerst)

### Ziel

Vor dem produktiven Push sicherstellen, dass Auth/Postgres im Fehlerfall schnell wiederhergestellt werden können. Analytics und weitere Nebensysteme folgen danach.

### Server-Agent prüft und dokumentiert

* Wie ein Postgres-Ausfall oder Fehlstart derzeit diagnostiziert wird
* Welche Volumes / Datenpfade gesichert werden müssen
* Welche Config-/Env-Werte für Auth zwingend korrekt sein müssen
* Wie der DB-Container oder Service kontrolliert gestoppt/gestartet wird
* Wie geprüft wird, dass Auth wieder sauber gegen Postgres spricht
* Welche Minimalchecks nach Wiederherstellung nötig sind

### Repo-Agent ergänzt

* Welche Migrations-/Bootstrap-/Init-Skripte Auth-seitig produktionsrelevant sind
* Welche Variablen oder Defaults Auth unbemerkt auf einen falschen DB-Pfad kippen könnten
* Welche Codepfade beim Wiederanlauf zuerst scheitern würden

### Mindestziel dieser Welle

* schriftlicher Recovery-Pfad für Auth/Postgres
* eindeutige Go/No-Go-Kriterien für produktiven Push
* Minimal-Restore in überschaubarer Zeit realistisch machbar

### Optional danach

* Analytics
* weitere Services oder Hilfsdaten
* sekundäre Verwaltungsjobs

### Ablage

`docs/prod_migration/YYYY-MM-DD_auth_postgres_recovery_plan.md`

---

## Welle 5: Sicherer Prod-Cutover- und Deploy-Plan

### Ziel

Eine exakte, operational brauchbare Reihenfolge für den ersten kontrollierten produktiven Deploy formulieren.

### Server-Agent definiert

* was **vor Deploy** vorbereitet werden muss
* was **während Deploy** gestoppt werden muss
* in welcher Reihenfolge Dienste und Container neu gestartet werden
* wann BlackLab gestoppt sein muss
* an welcher Stelle kein Index überschrieben werden darf
* welche Verifikationen unmittelbar nach Deploy laufen müssen
* was der sofortige Rollback-/Fallback-Pfad ist

### Repo-Agent liefert Zuarbeit

* welche Scripts/Commands/Reihenfolgen aus Repo-Sicht zu den Deploy-Schritten passen
* wo Skripte vorab gehärtet werden müssen

### Ergebnis

Ein Runbook mit drei Blöcken:

1. Vorbereitungen
2. Deploy/Cutover
3. Post-Deploy-Verifikation und Fallback

### Ablage

`docs/prod_migration/YYYY-MM-DD_safe_prod_cutover_plan.md`

---

## Welle 6: Erst nach stabilem Prod-Cutover — Strukturumbau lokal

Diese Welle erfolgt **nicht vor** dem ersten kontrollierten produktiven Stabilisierungspfad.

### Ziel

Das Repository langfristig in die Zielstruktur bringen:

* Git-Root wird `corapan/`
* `webapp/` wird zu `app/`
* nicht versionierte Betriebsverzeichnisse liegen sauber unter `corapan/`
* z. B. `media/`, `data/`, `config/` bleiben gitignored, aber strukturell vorgesehen

### Repo-Agent prüft dafür

* alle relativen und absoluten Pfadannahmen für `webapp/`
* CI/CD-/Deploy-Referenzen auf `webapp/`
* Skripte, Imports, Dokumentation, lokale Helfer und Agent-Kontextdateien
* welche `.github`-Inhalte auf Root-Ebene erwartet werden
* welche Ignore-Regeln und Platzhalterverzeichnisse nötig sind

### Server-Agent verifiziert danach

* welche Deploy- oder Betriebsannahmen durch den neuen Git-Root berührt werden
* welche Serverpfade beim späteren Umstieg von `app` konsistent bleiben oder angepasst werden müssen

### Ergebnis

Ein separater Umzugsplan mit:

1. Rename `webapp -> app`
2. Git-Root-Anhebung auf `corapan/`
3. Anpassung von Deploy, Doku, Agenten-Setup und Ignore-Regeln
4. Reihenfolge ohne unnötige Doppelbrüche

### Ablage

`docs/prod_migration/YYYY-MM-DD_repo_restructure_plan.md`

---

## Mindest-Checks vor dem nächsten Push

Vor einem echten Push müssen mindestens diese Punkte dokumentiert und beantwortet sein:

### Durch Repo-Agent

* Kanonischer Runtime-Root eindeutig benannt
* Pflicht-Env-Variablen dokumentiert
* BlackLab-Pfadannahmen dokumentiert
* Auth-/DB-Annahmen dokumentiert
* Deploy-relevante Skripte und Entrypoints geprüft
* offensichtliche Altpfadschreiber identifiziert

### Durch Server-Agent

* aktiver Auth/Postgres-Pfad dokumentiert
* aktiver BlackLab-Indexpfad dokumentiert
* aktive Mounts dokumentiert
* reale Env-/Config-Quellen dokumentiert
* Blind-Deploy-Risiken dokumentiert
* Minimal-Recovery für Auth/Postgres dokumentiert

Ohne diese Punkte ist ein produktiver Push organisatorisch unkontrolliert.

---

## Definition von Go / No-Go

### Go

Ein Push/Deploy ist vertretbar, wenn:

* Soll- und Istzustand dokumentiert sind
* Blind-Deploy-Bruchstellen benannt sind
* Auth/Postgres-Wiederherstellung klar beschrieben ist
* BlackLab-Index-Schutz im Cutover-Plan abgesichert ist
* Vorher/Nachher-Verifikation definiert ist
* Fallback-Schritte konkret beschrieben sind

### No-Go

Ein Push/Deploy ist nicht vertretbar, wenn:

* produktive Mounts oder Config-Quellen unklar sind
* unklar ist, wohin Deploy tatsächlich schreibt
* Auth gegen Postgres nach Fehlerfall nicht kontrolliert wiederherstellbar ist
* BlackLab-Indexpfad oder Stop-Reihenfolge unklar ist
* Altcontainer/-volumes/-pfade die Zielrealität überlagern könnten

---

## Empfohlene nächste konkrete Reihenfolge

1. **Repo-Agent: Welle 1** — Runtime-Sollbild und Pfadmatrix erstellen
2. **Server-Agent: Welle 2** — Prod-Reality-Audit gegen echte Laufzeit durchführen
3. **Repo + Server: Welle 3** — Gap-Analyse und Blind-Deploy-Bruchstellenbericht
4. **Server + Repo: Welle 4** — Auth/Postgres-Recovery-Plan absichern
5. **Server + Repo: Welle 5** — Safe Prod Cutover Plan festziehen
6. **Erst danach Push/Deploy**
7. **Nach stabilisiertem Prod-Pfad: Welle 6** — `webapp -> app` und Git-Root auf `corapan/` anheben

---

## Dokumentationspflicht für jeden weiteren Run

Jeder weitere Agent-Run muss am Ende:

* Ergebnisse in `docs/prod_migration/` erstellen oder aktualisieren
* klar zwischen Beobachtung, Ableitung und Empfehlung trennen
* offene Unsicherheiten explizit benennen
* nicht nur chatbasiert antworten

Der Run gilt erst als abgeschlossen, wenn die Dateiablage erfolgt ist.
