# Phase 5 Final Pre-Push Check

Datum: 2026-03-23

## Was geaendert wurde

- Root-README wurde um projektweite Forschungsressourcen und Root-Publikationskontext erweitert
- App-README wurde auf die technische Anwendungssicht unter `app/` fokussiert
- aktive Deploy-Hinweise in `.github/workflows/deploy.yml` wurden an den aktuellen Serververtrag angepasst
- eine veraltete Runtime-Pfadannahme in `app/scripts/deploy_prod.sh` wurde entfernt
- der finale Pre-Push-Entscheid fuer Option B wurde in `docs/repo_finish/phase_5_final_pre_push_check.md` dokumentiert

## Warum

Nach Phase 4 und 4b war die lokale Root-Migration technisch abgeschlossen, aber fuer den echten ersten Push in das bestehende GitHub-Repo fehlten noch drei Dinge:

- eine sauber getrennte Root-/App-README-Struktur fuer die Repo-Publikation
- die explizite Bestimmung der kanonischen Root-Remote fuer Option B
- ein hartes Urteil, ob und in welcher Form ein erster Push ohne unbeabsichtigten Production-Deploy zulaessig ist

Phase 5 schliesst diese Luecke und legt die kontrollierte Publikationsstrategie fest.

## Operative Wirkung

- `origin` ist als bestehendes GitHub-Repo fuer Option B verifiziert
- der lokale Root-Stand ist git-seitig ein Nachfolger von `origin/main`
- der erste zulaessige Publikationsschritt ist jetzt klar definiert: neuer Review-Branch statt Direkt-Push auf `main`
- Root- und App-README repraesentieren die Rollen von Repository und Anwendung jetzt sauber getrennt

## Kompatibilitaet und Grenzen

- kein Push wurde ausgefuehrt
- kein Deploy wurde ausgefuehrt
- ein direkter Push auf `main` bleibt weiterhin nicht freigegeben, weil er sofort den produktiven Deploy-Workflow startet
- die Freigabe gilt fuer einen kontrollierten ersten Push auf einen dedizierten Review-Branch mit anschliessendem Pull Request nach `main`