# Phase 7 - Merge Strategy Check fuer root-lift-review ohne gemeinsame Merge-Base

Datum: 2026-03-23
Workspace: `C:\dev\corapan`
Modus: Analyse und Strategievergleich ohne Merge, ohne Push nach `main`, ohne Deploy

## 1. Kurzurteil

Die eigentliche Publikation des Root-Lift-Stands auf `origin/root-lift-review` ist erfolgt, aber ein normaler Pull Request von `root-lift-review` nach `main` ist fuer den spaeteren Uebergang **nicht** der sichere Standardweg.

Grund:

- `origin/main` und `origin/root-lift-review` haben **keine gemeinsame Merge-Base**
- GitHub klassifiziert beide Branches als unterschiedliche Historien
- eine lokale Merge-Simulation mit `--allow-unrelated-histories` erzeugt zahlreiche echte Konflikte
- eine Cherry-Pick-Simulation des publizierten Review-Standes auf `origin/main` ist ebenfalls konfliktbehaftet

Die aktuell sicherste spaetere Uebergangsstrategie ist deshalb:

### REVIEW-BRANCH FUER SICHTUNG, DANN SEPARATER INTEGRATIONS-BRANCH AUF BASIS VON `origin/main`

Der empfohlene Weg ist also **nicht** der direkte Merge von `root-lift-review` nach `main`, sondern ein spaeter bewusst erzeugter Bridge-/Integrations-Branch, der auf `origin/main` beginnt und den Root-Lift-Baum kontrolliert als neue Zielstruktur uebernimmt.

## 2. Tatsaechliche Merge-Lage

Geprueft wurden:

- lokales `main`
- `origin/main`
- lokales `root-lift-review`
- `origin/root-lift-review`
- Elternbeziehungen der relevanten Commits

Ergebnis:

- `origin/main` zeigt weiterhin auf `9c819e6`
- `root-lift-review` lokal und remote zeigen auf `07f5b6e`
- `07f5b6e` hat als Parent `93e0e1a`
- `93e0e1a` hat als Parent `50f8d20`
- `50f8d20` ist Root-Commit ohne Parent

Damit ist die Root-Lift-Linie eine eigenstaendige orphan-Historie.

Die entscheidenden Merge-Base-Pruefungen ergaben:

- `git merge-base main origin/main` -> keine gemeinsame Basis
- `git merge-base origin/main origin/root-lift-review` -> keine gemeinsame Basis

Folgerung:

- aus Git-Sicht ist `root-lift-review` **kein normaler Nachfolger** von `origin/main`
- ein Standard-PR mit gewoehnlicher Merge-Logik ist damit historisch ein Sonderfall

## 3. GitHub-PR-Bewertung

Die GitHub-Compare-Pruefung fuer `main...root-lift-review` zeigte zwei Dinge gleichzeitig:

- die Seite meldet: `There isn't anything to compare.`
- zusaetzlich meldet GitHub: `main and root-lift-review are entirely different commit histories.`

Gleichzeitig wurde aber weiterhin ein Endpunkt-Diff angezeigt mit:

- 13 geaenderten Dateien
- 717 Additions
- 61 Deletions

Bewertung:

- GitHub kann zwar die Baumdifferenz der Endstaende visualisieren
- daraus folgt aber **nicht**, dass ein normaler PR-Merge fuer diesen Fall sauber oder verlässlich ist
- der Compare-Bildschirm bestaetigt vielmehr, dass der Fall historisch ausserhalb des gewoehnlichen PR-Flows liegt

Praktische Bedeutung:

- `root-lift-review` ist als Review- und Sichtungsbranch brauchbar
- fuer den spaeteren Uebergang nach `main` sollte man sich **nicht** auf den Standard-Merge-Button als primaeren Migrationsmechanismus verlassen

## 4. Vergleich der moeglichen Strategien

### A. Normaler PR `root-lift-review -> main`

Bewertung: **schwach / nicht empfohlen als technischer Uebernahmeweg**

Dafuer spricht:

- gute Sichtbarkeit im Remote-Review
- vorhandener publizierter Review-Branch kann diskutiert werden

Dagegen spricht:

- keine gemeinsame Merge-Base
- GitHub klassifiziert die Historien als getrennt
- lokale Merge-Simulation mit `--allow-unrelated-histories` erzeugte viele Konflikte
- Konflikte traten gerade in hochrelevanten Root-Dateien auf, unter anderem:
  - `.github/workflows/ci.yml`
  - `.github/workflows/deploy.yml`
  - `.github/workflows/md3-lint.yml`
  - `.gitignore`
  - `README.md`
  - `docker-compose.dev-postgres.yml`
  - mehrere operative Skripte unter `scripts/`

Fazit:

- als Review-Oberflaeche brauchbar
- als technischer Integrationsmechanismus nicht robust genug

### B. `root-lift-review` nur fuer Review, spaetere lokale kontrollierte Uebernahme

Bewertung: **stark / sinnvoller Oberbegriff fuer den spaeteren Weg**

Dafuer spricht:

- trennt Sichtung und eigentliche Integration sauber
- vermeidet Druck, den Spezialfall direkt ueber GitHub-Standardmerge abzuwickeln
- ermoeglicht vorbereitete technische Uebernahme mit klarer lokaler Kontrolle

Grenze:

- diese Strategie braucht eine konkrete technische Unterform
- genau diese Unterform ist hier am sinnvollsten als Bridge-/Integrations-Branch umzusetzen

### C. `main` ersetzen oder auf die orphan-Historie umhaengen

Bewertung: **nicht empfohlen**

Dagegen spricht:

- hohes Risiko fuer Remote-Historie, Branch-Schutz und Team-Nachvollziehbarkeit
- wuerde den bestehenden `origin/main`-Verlauf hart ueberschreiben oder entwerten
- erhoeht das Risiko unbeabsichtigter Betriebsfolgen deutlich

Fazit:

- nur als Notfall- oder Repo-Neustart-Methode denkbar
- fuer diesen Bestand unnoetig riskant

### D. Cherry-Pick oder Rebase der Root-Lift-Commits auf `origin/main`

Bewertung: **nicht empfohlen**

Die Simulation eines Cherry-Picks von `07f5b6e` auf `origin/main` ergab reale Konflikte, unter anderem in:

- `README.md`
- `app/README.md`
- `docs/changes/2026-03-21-push-deploy-blocker-fix.md`
- `docs/local_runtime_layout.md`
- `docs/state/push-deploy-readiness-fix.md`

Bewertung:

- schon der einzelne publizierte Spitzencommit laesst sich nicht konfliktfrei uebernehmen
- Rebase auf eine fremde, nicht verwandte Historie waere noch fehleranfaelliger und schwerer nachvollziehbar
- diese Option zerlegt den Root-Lift kuenstlich in Historienoperationen, obwohl eigentlich eine Strukturuebernahme noetig ist

### E. Bridge-/Integrations-Branch auf Basis von `origin/main`

Bewertung: **am staerksten / empfohlen**

Simulation:

- temporaerer Branch startete auf `origin/main`
- der bestehende Baum wurde kontrolliert entfernt
- anschliessend wurde der Baum von `origin/root-lift-review` gezielt in den Arbeitsbaum uebernommen

Beobachtung:

- der resultierende Index zeigte **keine** normale unrelated-histories-Merge-Konfliktlage
- viele Veraenderungen wurden sinnvoll als Renames bzw. strukturierte Verschiebungen erkannt
- typische Beispiele:
  - `.dockerignore -> app/.dockerignore`
  - `AGENTS.md -> app/AGENTS.md`
  - `Dockerfile -> app/Dockerfile`
  - `config/blacklab/... -> app/config/blacklab/...`
  - `infra/... -> app/infra/...`
  - `scripts/... -> app/scripts/...`

Vorteile:

- neue Historie bleibt auf `origin/main` verankert
- der eigentliche Uebergang kann als bewusster Integrations-Commit oder kleine Integrationsserie erfolgen
- GitHub-PR nach `main` waere dann ein normaler PR von verwandter Historie
- Review-Branch bleibt weiterhin als Forensik- und Vergleichsreferenz erhalten

Risiko:

- die Methode ist kein Knopfdruck, sondern ein bewusstes Integrationsvorhaben
- vor dem spaeteren echten Einsatz sind erneut Struktur-, Runtime- und CI-Checks erforderlich

## 5. Empfohlene Uebergangsstrategie nach `main`

Empfohlen wird folgender spaeterer Ablauf:

1. `root-lift-review` bleibt unveraendert als publizierter Review-Stand bestehen.
2. Nach fachlicher Sichtung wird **ein neuer Integrations-Branch von `origin/main`** erstellt.
3. Auf diesem Branch wird der Zielbaum kontrolliert auf die Root-Lift-Struktur umgestellt.
4. Das Ergebnis wird lokal geprueft:
   - Git-Diff und Rename-Bild
   - Repo-Struktur
   - Root-/App-README-Rollen
   - Dev-Compose-Render
   - minimaler `create_app('development')`-Check
   - relevante CI-Workflows in der neuen Root-Struktur
5. Erst dieser Integrations-Branch wird spaeter per normalem PR nach `main` vorgeschlagen.
6. Ein Merge nach `main` erfolgt erst bewusst zu einem Zeitpunkt, an dem ein produktiver Deploy zulaessig ist.

Wesentliche Begruendung:

- `main` behaelt seine verknuepfte Historie
- die Root-Lift-Zielstruktur wird dennoch vollstaendig uebernommen
- der Integrationsschritt wird als inhaltliche Baumuebernahme statt als fehleranfaelliger Historien-Trick modelliert

## 6. Merge-Blocker und Nicht-Blocker

### Echte Blocker fuer einen direkten Uebergang `root-lift-review -> main`

- keine gemeinsame Merge-Base
- GitHub klassifiziert die Branches als unterschiedliche Historien
- konfliktreiche Merge-Simulation mit `--allow-unrelated-histories`
- konfliktbehaftete Cherry-Pick-Simulation

### Kein Blocker mehr

- der zuvor reale Laufzeitblocker `CONFIG_ROOT` ist behoben
- der publizierte Review-Branch existiert remote stabil
- `main` wurde bisher nicht veraendert
- es wurde kein Deploy ausgeloest

### Operative Nicht-Blocker mit Bedingungen

- das Review von `root-lift-review` ist moeglich
- eine spaetere Integration nach `main` ist moeglich, aber nur ueber einen kontrollierten Integrationsschritt und nicht als unvorbereiteter Direktmerge

## 7. Go / No-Go

### GO

Fuer:

- Review und Sichtung auf Basis von `origin/root-lift-review`
- spaetere Vorbereitung eines separaten Integrations-Branchs auf Basis von `origin/main`

### NO-GO

Fuer:

- direkten Standard-Merge von `root-lift-review` nach `main` als primaeren Uebernahmeweg
- Cherry-Pick-/Rebase-Strategien als Hauptmethode
- jede Form von Branch-Ersatz oder History-Umschreiben auf `main`

Kurzform des Urteils:

### REVIEW-BRANCH BLEIBT BESTEHEN. UEBERGANG NACH `main` NUR UEBER SEPARATEN INTEGRATIONS-BRANCH AUF BASIS VON `origin/main`.