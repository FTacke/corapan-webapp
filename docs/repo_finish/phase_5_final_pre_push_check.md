# Phase 5 - Final Pre-Push Check for Option B

Datum: 2026-03-23
Workspace: `C:\dev\corapan`
Modus: finaler Pre-Push-Lauf ohne Push, ohne Deploy

## 1. Kurzurteil

Der Root-Lift ist fuer Option B technisch publikationsfaehig, aber nicht fuer einen unkontrollierten Direkt-Push auf `origin/main`.

- Die kanonische Root-Remote fuer Option B ist belastbar bestimmt: `origin = git@github.com:FTacke/corapan-webapp.git`
- Der lokale Root-Stand haengt direkt auf `origin/main` und ist damit git-seitig integrierbar.
- `origin/main` ist gleichzeitig der produktive Auto-Deploy-Trigger.
- Ein erster Publikationsschritt darf deshalb nicht als Direkt-Push auf `main` erfolgen.

Finale Freigabe fuer Option B:

### GO FUER FINALEN PUSH

Diese Freigabe gilt ausschliesslich fuer einen kontrollierten ersten Push auf einen neuen Nicht-Deploy-Review-Branch mit anschliessendem Pull Request nach `main`.

Ein unmittelbarer Direkt-Push auf `origin/main` bleibt in diesem Zustand ein operatives No-Go.

## 2. README-Neuordnung

### Zielbild

Die Root-README muss das GitHub-Repo als Gesamtprojekt repraesentieren. Die App-README soll die technische Anwendung unter `app/` beschreiben und nicht den gesamten Projekt- und Publikationskontext duplizieren.

### Umgesetzt

- `README.md` staerkt jetzt die Repository- und Publikationssicht des Root-Repos.
- `README.md` enthaelt jetzt die getrennten Forschungsressourcen und DOI-Hinweise auf Root-Ebene.
- `app/README.md` wurde auf die technische Anwendungssicht unter `app/` fokussiert.
- projektweite Lizenz-, Daten- und Zitationskontexte wurden aus der App-README in die Root-README verlagert bzw. dort referenziert.

### Bewertung

Die README-Aufteilung ist fuer GitHub-Publikation und Repo-Verstaendlichkeit jetzt sauber genug. Root und `app/` haben klar getrennte Rollen.

## 3. Root-Remote- und Publikationsstrategie

### Festgestellte Remote-Lage

- `origin` (kanonische Ziel-Remote): `git@github.com:FTacke/corapan-webapp.git`
- `legacy-webapp` (lokales Backup/Mirror): `C:\dev\corapan_git_backups\20260323_095902\webapp.git`
- aktueller lokaler Branch: `main`
- aktueller lokaler Branch hat noch kein Upstream-Tracking gesetzt

### Branch- und Historienlage

Gepruefter Graph:

- `origin/main` zeigt auf `9c819e6`
- lokales `main` zeigt auf `93e0e1a`
- die lokalen Phase-4-/4b-Commits `50f8d20` und `93e0e1a` liegen direkt auf `origin/main`

Bewertung:

- es gibt keinen Historienbruch mehr als Push-Blocker
- der lokale Stand ist git-seitig ein kontrollierbarer Nachfolger von `origin/main`
- ein Fast-Forward-Push auf `origin/main` waere technisch moeglich
- operativ ist er trotzdem nicht freigegeben, weil `push -> main` sofort Production-Deploy ausloest

### Empfohlene Publikationsstrategie fuer Option B

1. Ersten Push nicht nach `origin/main`, sondern auf einen neuen dedizierten Review-Branch, z. B. `root-lift-review`
2. Danach Pull Request `root-lift-review -> main` auf GitHub
3. PR-Review und CI-Auswertung abwarten
4. Erst danach bewusste Merge-Entscheidung nach `main`
5. Mit dem Merge nach `main` den produktiven Deploy bewusst akzeptieren

Beispiel fuer den ersten zulaessigen Push:

```bash
git push -u origin HEAD:root-lift-review
```

## 4. Push- und Deploy-Risikoabschluss

### GitHub / Remote

- Das bestehende GitHub-Repo ist der richtige Zielort fuer Option B.
- Ein neues separates Repo ist fuer diese Strategie nicht erforderlich.
- Die Root-Remote ist jetzt explizit bestimmt und verifiziert.

### GitHub Actions / CI

- `.github/workflows/ci.yml` ist auf Root-Struktur mit `app/` als Working Directory ausgerichtet.
- CI reagiert auf `push` nach `main`, `push` nach `prod_prep` und `pull_request` nach `main`.
- Ein Push auf einen neuen Review-Branch loest fuer sich genommen nicht automatisch CI aus; der PR nach `main` aber schon.

### Deploy / Self-Hosted Runner

- `.github/workflows/deploy.yml` deployt bei `push` nach `main`.
- Der Runner arbeitet direkt im Server-Checkout unter `/srv/webapps/corapan/app`.
- `app/scripts/deploy_prod.sh` zieht weiterhin `origin/main` und deployt den Zustand von `main`.

Folgerung:

- jeder direkte Push nach `origin/main` ist zugleich ein produktiver Release-Vorgang
- fuer die erste Veroeffentlichung nach dem Root-Lift ist daher ein Branch-First-Ansatz zwingend

## 5. Aktive Restfunde und Klassifikation

Im Rahmen dieses Laufs wurden nur noch kleine aktive Restunklarheiten korrigiert:

- `.github/workflows/deploy.yml`: veraltete Verzeichnisbeschreibung auf den aktuellen Serververtrag gebracht
- `app/scripts/deploy_prod.sh`: ueberholte Runtime-Pfadannahme aus den Kommentaren/Variablen entfernt

Es wurden keine weiteren strukturellen Push-Blocker gefunden, die den ersten kontrollierten Review-Push verhindern.

## 6. Endentscheidung

### GO FUER FINALEN PUSH

Bedingungen dieser Freigabe:

- kein Direkt-Push auf `origin/main`
- erster Push nur auf neuen dedizierten Review-Branch
- anschliessend Pull Request nach `main`
- Merge nach `main` erst nach bewusster Freigabe als echter Deploy-Schritt

Nicht freigegeben ist:

- `git push origin main`
- jede andere Aktion, die sofort `push -> main -> deploy` ausloest

## 7. Konkreter naechster Schritt

Wenn der Push freigegeben werden soll, ist der naechste saubere Schritt:

```bash
git push -u origin HEAD:root-lift-review
```

Danach:

```text
Pull Request: root-lift-review -> main
```