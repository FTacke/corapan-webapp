# BlackLab Config Path Cleanup Audit

Datum: 2026-03-25

## A. Executive Summary

Nach der produktiven BlackLab-Reparatur wurde ein gezieltes Cleanup-Audit der Config-Pfadreferenzen durchgefuehrt.

Ergebnis:

- der aktuelle kanonische Vertrag ist technisch klar
- es gab noch mehrere aktive Fehlreferenzen auf den stale Outer-Path
- diese aktiven Fehlreferenzen wurden korrigiert
- mehrere historische oder irrefuehrende Doku-Artefakte bleiben als Audit-Befund sichtbar, wurden aber nicht zwangsweise grossflächig umgebaut

Kanonischer Vertrag nach Audit:

- DEV: `app/config/blacklab -> /etc/blacklab`
- PROD: `/srv/webapps/corapan/app/app/config/blacklab -> /etc/blacklab`

Der Outer-Path

- `/srv/webapps/corapan/app/config/blacklab`

bleibt als stale/dangerous klassifiziert und soll nicht aus optischen Gruenden reaktiviert werden.

## B. Aktueller kanonischer DEV-/PROD-Vertrag

### DEV

- versionierte BlackLab-Config im Repo: `app/config/blacklab`
- aktiver Dev-Mount: `app/config/blacklab -> /etc/blacklab`
- belegt durch `docker-compose.dev-postgres.yml`

### PROD

- root-gelifteter Checkout: `/srv/webapps/corapan/app` mit innerem App-Tree `/srv/webapps/corapan/app/app`
- aktive versionierte Prod-Config: `/srv/webapps/corapan/app/app/config/blacklab`
- aktiver Prod-Mount: `/srv/webapps/corapan/app/app/config/blacklab -> /etc/blacklab`
- live belegt im reparierten `corapan-blacklab`-Container

### Nicht kanonisch

- `/srv/webapps/corapan/app/config/blacklab`

Status:

- stale/dangerous
- darf nicht als aktueller Prod-Standard angenommen werden

## C. Gefundene BlackLab-Config-Pfadreferenzen

| Datei | Exakte Referenz | Bewertung | Empfohlene Maßnahme |
| --- | --- | --- | --- |
| `app/scripts/blacklab/run_bls_prod.sh` | `/srv/webapps/corapan/app/app/config/blacklab` | A. aktiv korrekt | behalten |
| `app/scripts/blacklab/build_blacklab_index_prod.sh` | `/srv/webapps/corapan/app/app/config/blacklab/corapan-tsv.blf.yaml` | A. aktiv korrekt | behalten |
| `app/scripts/deploy_sync/publish_blacklab_index.ps1` | default `ConfigDir=/srv/webapps/corapan/app/config/blacklab` | B. aktiv falsch / zu korrigieren | korrigiert auf inneren Prod-Pfad |
| `app/scripts/deploy_sync/tasks/publish_blacklab_index.ps1` | default `ConfigDir=/srv/webapps/corapan/app/config/blacklab` | B. aktiv falsch / zu korrigieren | korrigiert auf inneren Prod-Pfad |
| `maintenance_pipelines/_2_deploy/publish_blacklab.ps1` | `ConfigDir = "$RemoteAppRoot/config/blacklab"` | B. aktiv falsch / zu korrigieren | korrigiert auf `$RemoteAppRoot/app/config/blacklab` |
| `app/scripts/deploy_sync/README.md` | default `/srv/webapps/corapan/app/config/blacklab` | D. dokumentarisch irrefuehrend | auf inneren Prod-Pfad aktualisiert |
| `docs/blacklab/README.md` | fehlte expliziter DEV-/PROD-Vertrag | D. dokumentarisch irrefuehrend | DEV-/PROD-Mount-Vertrag ergänzt |
| `docs/architecture/blacklab_operational_safety.md` | `Git root: webapp/`, `config/blacklab -> /etc/blacklab` | D. dokumentarisch irrefuehrend | zentrale Dev-Pfadreferenzen auf aktuellen Vertrag korrigiert |
| `.github/skills/blacklab-operational-safety/SKILL.md` | innerer Prod-Pfad + outer path stale | A. aktiv korrekt | behalten |
| `.github/instructions/devops.instructions.md` | innerer Prod-Pfad + outer path stale | A. aktiv korrekt | behalten |
| `docs/rsync/blacklab_prod_fix_report.md` | outer path als Fehlerzustand, innerer Pfad als Fix | C. historisch / Übergang | behalten als Reparaturnachweis |
| `docs/changes/2026-03-25-blacklab-prod-config-mount-fix.md` | old -> new contract | C. historisch / Übergang | behalten |
| `docs/rsync/server-agent_rsync_audit.md` | outer path als aktiver Mount | D. dokumentarisch irrefuehrend | mit Historik-Hinweis versehen; spaeter konsolidieren |
| `docs/architecture/corapan_workspace_and_blacklab_model.md` | aelteres Root-Lift-Modell mit frueheren BlackLab-Pfaden | D. dokumentarisch irrefuehrend | mit Historik-Hinweis versehen; spaeter gezielt konsolidieren |
| `docs/architecture/blacklab_operational_safety.md` | weitere `webapp/`-Verweise | D. dokumentarisch irrefuehrend | teilweise korrigiert, Rest spaeter bereinigen |
| `app/tmp/prod_backport/scripts/deploy_sync/README.md` | old outer path default | E. spaeter entfernbar | nicht aktiv; nur bei Backport-Bedarf konsolidieren |
| `maintenance_pipelines/_2_deploy/_logs/publish_blacklab_wrapper_*.log` | old outer path in historical logs | C. historisch / Übergang | nicht editieren |
| `app/scripts/deploy_sync/legacy/20260116_211115/PUBLISH_BLACKLAB_INDEX.md` | old outer path | C. historisch / Übergang | nur als Legacy belassen |

## D. Aktive Fehlreferenzen

Vor dem Cleanup waren die klar aktiven Fehlreferenzen:

1. `app/scripts/deploy_sync/publish_blacklab_index.ps1`
2. `app/scripts/deploy_sync/tasks/publish_blacklab_index.ps1`
3. `maintenance_pipelines/_2_deploy/publish_blacklab.ps1`
4. `app/scripts/deploy_sync/README.md`

Diese Stellen steuern oder dokumentieren den aktuell benutzten Publish-/Operator-Pfad und wurden direkt korrigiert.

## E. Dokumentationsdrift

Die wichtigste verbleibende Dokumentationsdrift liegt in zwei aelteren Architekturtexten:

1. `docs/rsync/server-agent_rsync_audit.md`
- beschreibt den Outer-Path als aktiven Prod-Mount
- ist jetzt mit einem expliziten Historik-Hinweis versehen
- bleibt als Auditkontext nuetzlich, ist aber keine aktuelle Pfadquelle

2. `docs/architecture/corapan_workspace_and_blacklab_model.md`
- beschreibt ein aelteres Root-Lift-Modell
- ist jetzt mit einem expliziten Historik-Hinweis versehen
- darf nicht gegen den heute belegten DEV-Vertrag `app/config/blacklab` ausgespielt werden

Bewertung:

- beide Dateien sind als Kontexthistorie noch nutzbar
- beide sind als aktuelle Pfadquelle irrefuehrend

## F. Bewertung eines möglichen Outer-Path-Wechsels

Gepruefte Frage:

- sollte man von `/srv/webapps/corapan/app/app/config/blacklab` zurueck auf `/srv/webapps/corapan/app/config/blacklab` wechseln?

Bewertung:

Nein, nicht im aktuellen Zustand.

Technische Gruende:

1. Es waere ein BlackLab-Sonderfall.
- Der aktuelle root-geliftete Produktionsvertrag verwendet den inneren App-Tree als versionierten Implementierungsbereich.
- Eine Rueckkehr nur fuer BlackLab wuerde eine Sonderlogik schaffen statt den Vertrag zu vereinfachen.

2. Es widerspricht dem Root-Lift-Modell.
- `app/scripts/deploy_prod.sh` beschreibt explizit den Checkout unter `/srv/webapps/corapan/app` und die App-Implementierung unter `/srv/webapps/corapan/app/app`.
- Ein Outer-Path-Sonderfall fuer BlackLab wuerde diesen Vertrag partiell unterlaufen.

3. Es vereinheitlicht DEV und PROD nur scheinbar.
- DEV arbeitet korrekt mit dem Repo-Pfad `app/config/blacklab` relativ zum Workspace.
- PROD arbeitet korrekt mit dem inneren Checkout-Pfad relativ zum root-gelifteten Deploy-Layout.
- Die String-Aehnlichkeit des Outer-Paths ist kein stabiler Betriebsvorteil.

4. Der Umbau haette echten Folgekosten.
- Prod-Skripte
- Publish-Defaults
- Betriebsdokumentation
- moeglicherweise Host-Verzeichnisverwaltung ausserhalb des aktuellen Checkout-Modells

5. Der Nutzen ist kleiner als das Risiko.
- Der aktuelle innere Pfad funktioniert live.
- Der Outer-Path ist gerade erst als Fehlerquelle belegt worden.

Schluss:

- ein Outer-Path-Wechsel ist heute nicht sinnvoll
- falls spaeter gewollt, dann nur als bewusste groessere Layout-/Checkout-Migration, nicht als BlackLab-Einzelkorrektur

## G. Empfohlene Sofortkorrekturen

Bereits umgesetzt:

- aktive Publish-Defaults auf den inneren Prod-Pfad umgestellt
- zentrale BlackLab-/rsync-Doku auf expliziten DEV-/PROD-Vertrag nachgezogen
- Governance um die Regel erweitert, stale Pfade nicht aus optischen Gruenden wiederzubeleben

Noch sinnvoll, aber nicht zwingend sofort:

- `docs/rsync/server-agent_rsync_audit.md` spaeter von historischem Auditkontext in kanonische Wartungsdoku ueberfuehren oder kuerzen
- `docs/architecture/corapan_workspace_and_blacklab_model.md` spaeter gezielt umschreiben, falls das Root-Lift-Modell weiter aktiv dokumentiert werden soll

## H. Was später entfernt werden kann

- historische Wrapper-Logs unter `maintenance_pipelines/_2_deploy/_logs/`
- `app/tmp/prod_backport/...`-Verweise auf den stale Outer-Path, wenn dieser Backport-Zweig nicht mehr benoetigt wird
- explizite Legacy-Dokumentation zum Outer-Path erst dann, wenn keine operative Stelle und keine aktive Maintainer-Doku mehr darauf verweist

Nicht jetzt entfernen:

- der leere Hostpfad `/srv/webapps/corapan/app/config/blacklab`
- historische Fix- und Audit-Berichte, die den Drift noch als Befund dokumentieren

## I. Empfohlene nächste Schritte

1. `docs/rsync/server-agent_rsync_audit.md` als historischer Auditstand markieren oder in kanonische BlackLab-Doku ueberfuehren.
2. `docs/architecture/corapan_workspace_and_blacklab_model.md` entscheiden: bewusst historisch belassen oder gezielt auf aktuellen Vertrag umschreiben.
3. Bei jeder kuenftigen Aenderung an BlackLab-Mounts oder Publish-Pfaden zuerst den expliziten DEV-/PROD-Pfadvertrag pruefen, nicht String-Aehnlichkeiten von Pfaden.