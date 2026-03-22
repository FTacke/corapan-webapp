# Repo Backport from Prod

Datum: 2026-03-22
Ziel: produktiv bereits eingesetzte App-Repo-Aenderungen aus `/srv/webapps/corapan/app` sauber in das lokale versionierte Repo uebernehmen, damit der naechste Push den laufenden Produktivzustand nicht wieder ueberschreibt.

## 1. Ausgangslage

Der produktive Cutover ist bereits erfolgreich gelaufen. Auf dem Server existieren damit App-Repo-Aenderungen, die im lokalen Repo noch nicht oder noch nicht vollstaendig vorliegen.

Ohne Backport wuerde ein naechster Push/Deploy genau diese produktiv bereits funktionierenden Aenderungen im Server-Checkout unter `/srv/webapps/corapan/app` wieder ueberschreiben.

Betroffene Mindestdateien:

- `infra/docker-compose.prod.yml`
- `scripts/deploy_prod.sh`
- `scripts/deploy_sync/sync_core.ps1`
- `scripts/deploy_sync/README.md`

## 2. Verwendete Source of Truth

### Serverzustand als operative Wahrheit

Fuer diesen Backport wurde der bereits laufende Produktivstand unter folgendem Serverpfad als Source of Truth verwendet:

- `/srv/webapps/corapan/app/infra/docker-compose.prod.yml`
- `/srv/webapps/corapan/app/scripts/deploy_prod.sh`
- `/srv/webapps/corapan/app/scripts/deploy_sync/sync_core.ps1`
- `/srv/webapps/corapan/app/scripts/deploy_sync/README.md`

Diese Auswahl basiert auf:

- `docs/prod_migration/2026-03-22_phase_d4_execution.md`
- dem dort dokumentierten produktiven D4-Vollzug
- der Anforderung, den bereits erfolgreich eingesetzten Serverzustand zurueck in das Repo zu holen

### Dokumentarische Zusatzquelle

Als inhaltliche Referenz fuer die beabsichtigten produktiven Aenderungen wurde zusaetzlich verwendet:

- `docs/prod_migration/2026-03-22_phase_d4_execution.md`

Insbesondere relevant waren dort:

- Umstellung der Web-Mounts auf kanonische Top-Level-Pfade
- Wegfall des separaten Export-Mounts durch Voll-Mount von `/srv/webapps/corapan/data` nach `/app/data`
- Umstellung der Guard-Logik auf den echten Live-Containernamen `corapan-web-prod`

## 3. Lokale Ausgangslage

### Branch

Lokaler Branch zum Zeitpunkt des Backports:

- `main`

### Git-Status vor der Uebernahme

Vor dem Backport waren im Repo bereits unversionierte Dokumentdateien vorhanden:

- `docs/prod_migration/2026-03-22_migration_mapping.md`
- `docs/prod_migration/2026-03-22_phase_d4_execution.md`
- `docs/prod_migration/d1_results.md`
- `docs/prod_migration/d2_results.md`
- `docs/prod_migration/prod_migration_perfect.md`

Die vier Ziel-Backportdateien selbst waren vor diesem Run lokal versioniert und unterschieden sich inhaltlich vom Produktivstand.

### Warum der Backport noetig ist

Die lokale Repo-Fassung trug an mehreren Stellen noch den alten Produktionsvertrag:

- runtime-first-Mounts unter `runtime/corapan/*`
- separater Export-Mount nach `/app/data/blacklab/export`
- Guard-Logik mit altem Containernamen `corapan-webapp`
- README-Text mit altem Produktionslayout

Der Produktivserver laeuft dagegen bereits mit dem D4-Zielzustand:

- `/srv/webapps/corapan/data:/app/data`
- `/srv/webapps/corapan/media:/app/media`
- `/srv/webapps/corapan/logs:/app/logs`
- `/srv/webapps/corapan/data/config:/app/config`

## 4. Beschaffung der Serverdateien

### Lokaler Vergleichsordner

Die Serverdateien wurden lokal in folgenden temp-Vergleichsordner gespiegelt:

- `tmp/prod_backport/infra/docker-compose.prod.yml`
- `tmp/prod_backport/scripts/deploy_prod.sh`
- `tmp/prod_backport/scripts/deploy_sync/sync_core.ps1`
- `tmp/prod_backport/scripts/deploy_sync/README.md`

### Beschaffungsweg

Ein erster Abruf via `scp` scheiterte, weil der Server kein funktionierendes `scp`-Subsystem fuer diesen Zugriff lieferte.

Deshalb wurden die Dateien per SSH und `cat` lokal in den Vergleichsordner geschrieben.

Verwendeter Abrufweg:

```powershell
Set-Location 'c:\dev\corapan\webapp'
$ssh='C:\Windows\System32\OpenSSH\ssh.exe'
& $ssh -o StrictHostKeyChecking=no root@marele.online.uni-marburg.de "cat /srv/webapps/corapan/app/infra/docker-compose.prod.yml" | Out-File -FilePath '.\tmp\prod_backport\infra\docker-compose.prod.yml' -Encoding utf8
& $ssh -o StrictHostKeyChecking=no root@marele.online.uni-marburg.de "cat /srv/webapps/corapan/app/scripts/deploy_prod.sh" | Out-File -FilePath '.\tmp\prod_backport\scripts\deploy_prod.sh' -Encoding utf8
& $ssh -o StrictHostKeyChecking=no root@marele.online.uni-marburg.de "cat /srv/webapps/corapan/app/scripts/deploy_sync/sync_core.ps1" | Out-File -FilePath '.\tmp\prod_backport\scripts\deploy_sync\sync_core.ps1' -Encoding utf8
& $ssh -o StrictHostKeyChecking=no root@marele.online.uni-marburg.de "cat /srv/webapps/corapan/app/scripts/deploy_sync/README.md" | Out-File -FilePath '.\tmp\prod_backport\scripts\deploy_sync\README.md' -Encoding utf8
```

Hinweis:

- Die via `Out-File -Encoding utf8` erzeugten Vergleichsdateien enthalten auf Windows ein UTF-8-BOM.
- Diese BOM-Artefakte wurden nicht blind ins Repo uebernommen.
- Der Backport erfolgte inhaltlich manuell anhand der Serverfassung, nicht als 1:1-Dateiersatz aus dem temp-Ordner.

## 5. Lokale Ausgangsdiffs gegen Produktivstand

### `infra/docker-compose.prod.yml`

Status vor Backport:

- unterschiedlich

Relevante Unterschiede:

1. Lokal noch runtime-first:
   - `/srv/webapps/corapan/runtime/corapan/data:/app/data`
   - `/srv/webapps/corapan/runtime/corapan/media:/app/media`
   - `/srv/webapps/corapan/runtime/corapan/logs:/app/logs`
   - `/srv/webapps/corapan/runtime/corapan/config:/app/config`
2. Lokal noch separater Export-Mount:
   - `/srv/webapps/corapan/data/blacklab/export:/app/data/blacklab/export:ro`
3. Produktiv bereits top-level-kanonisch:
   - `/srv/webapps/corapan/data:/app/data`
   - `/srv/webapps/corapan/media:/app/media`
   - `/srv/webapps/corapan/logs:/app/logs`
   - `/srv/webapps/corapan/data/config:/app/config`

Bewertung:

- Hier war die Serverfassung fachlich eindeutig korrekt.
- Die Aenderung wurde inhaltlich 1:1 uebernommen, aber ohne BOM-Artefakt.

### `scripts/deploy_prod.sh`

Status vor Backport:

- unterschiedlich

Relevante Unterschiede:

1. Lokal sprach der Operator-Text noch von `runtime-first`-Mounts.
2. Produktiv spricht der Operator-Text von `canonical top-level mounts`.
3. Die funktionale Deploy-Logik blieb zwischen lokal und Produktivstand weitgehend gleich.
4. Die produktive Fassung enthaelt weiterhin die riskante Zeile:
   - `git reset --hard origin/main`

Bewertung:

- Der produktive D4-Backport fuer diese Datei ist vor allem textlich und operatorisch.
- Die riskante Reset-Logik wurde fuer diesen Run nicht separat umgebaut, weil dies keine reine Prod-Backport-Uebernahme waere, sondern eine neue Verhaltensaenderung.
- Diese Stelle bleibt als offener Follow-up-Punkt dokumentiert.

### `scripts/deploy_sync/sync_core.ps1`

Status vor Backport:

- unterschiedlich

Relevante Unterschiede:

1. Lokal pruefte der Guard noch gegen den alten Containernamen:
   - `corapan-webapp`
2. Lokal lautete die Fehlermeldung noch auf `runtime-first`.
3. Produktiv nutzt der Guard bereits:
   - `corapan-web-prod`
   - Fehlermeldung fuer kanonische Top-Level-Mounts

Bewertung:

- Die Serverfassung war hier die klare operative Wahrheit.
- Diese Aenderung wurde gezielt und inhaltlich aus der Produktivfassung uebernommen.

### `scripts/deploy_sync/README.md`

Status vor Backport:

- unterschiedlich

Relevante Unterschiede:

1. Lokal beschrieb die README noch den alten runtime-first-Produktionsvertrag.
2. Lokal war der Preflight-Fehlertext noch auf `corapan-webapp` und `runtime-first` bezogen.
3. Produktiv beschreibt die README bereits den kanonischen Top-Level-Vertrag.
4. Die Produktivfassung praezisiert ausserdem den Text zu `publish_blacklab_index.ps1`.
5. Der Statistik-Abschnitt verweist weiterhin auf den runtime-basierten Statistikzielpfad und wurde auf dem Server nicht im gleichen Masse wie der Mountvertrag umgestellt.

Bewertung:

- Die produktiven README-Aenderungen wurden inhaltlich uebernommen.
- Nicht serverseitig geaenderte Alttexte wurden in diesem Run nicht spekulativ weiter bereinigt.

## 6. Uebernommene Aenderungen

### 6.1 `infra/docker-compose.prod.yml`

Uebernommen:

1. Web-Mounts auf kanonische Top-Level-Pfade umgestellt.
2. Separaten Export-Mount entfernt.
3. Config-Mount auf `/srv/webapps/corapan/data/config:/app/config` umgestellt.
4. Kommentartext auf den kanonischen Top-Level-Vertrag aktualisiert.

Finaler Repo-Zustand:

- `/srv/webapps/corapan/data:/app/data`
- `/srv/webapps/corapan/media:/app/media`
- `/srv/webapps/corapan/logs:/app/logs`
- `/srv/webapps/corapan/data/config:/app/config`

### 6.2 `scripts/deploy_prod.sh`

Uebernommen:

1. Schritt 3 textlich auf `canonical top-level mounts` umgestellt.
2. Schritt 5 textlich auf `canonical mounts` umgestellt.
3. Nicht-ASCII-Haken aus der Serverfassung bewusst nicht uebernommen; stattdessen ASCII-konforme Logzeilen beibehalten.

Bewusst nicht uebernommen:

1. Kein 1:1-Dateiersatz mit BOM-Artefakt.
2. Keine neue funktionale Aenderung der bestehenden Reset-Logik in diesem Backport-Run.

### 6.3 `scripts/deploy_sync/sync_core.ps1`

Uebernommen:

1. Guard-Kommentar auf kanonische Produktionsmounts aktualisiert.
2. Containername von `corapan-webapp` auf `corapan-web-prod` umgestellt.
3. Fehlermeldung auf den echten produktiven Top-Level-Vertrag umgestellt.

### 6.4 `scripts/deploy_sync/README.md`

Uebernommen:

1. Produktionsvertrag von runtime-first auf kanonisches Top-Level-Layout umgestellt.
2. Zielpfade auf `/srv/webapps/corapan/{data,media,logs,data/config}` aktualisiert.
3. Preflight-Guard-Text auf `corapan-web-prod` und kanonische Top-Level-Mounts umgestellt.
4. Text zu `publish_blacklab_index.ps1` an die Produktivfassung angeglichen.

## 7. Bewusst NICHT uebernommene Aenderungen

Folgende Punkte wurden bewusst nicht ungeprueft oder nicht im selben Run uebernommen:

1. UTF-8-BOM-Artefakte aus den temp-Vergleichsdateien.
2. Die in der Produktivfassung von `deploy_prod.sh` weiterhin vorhandene Zeile `git reset --hard origin/main` wurde nicht entfernt, weil dies kein reiner Backport des laufenden Produktivzustands waere, sondern eine zusaetzliche inhaltliche Aenderung.
3. Weitere moegliche README-Konsolidierungen ausserhalb der im Produktivstand bereits real geaenderten Passagen wurden nicht spekulativ vorgenommen.

## 8. Validierung

Durchgefuehrte Validierung:

1. Hash- und Diff-Vergleich zwischen lokalem Repo und den abgezogenen Produktivdateien.
2. inhaltliche Plausibilitaetspruefung der vier Zieldateien gegen die D4-Dokumentation.
3. Dateidiagnostik nach dem Edit auf allen betroffenen Dateien.
4. finaler `git diff` auf die vier Rueckport-Dateien.
5. finaler `git status --short` auf die vier Rueckport-Dateien plus diese Dokumentation.

Ergebnis der Validierung:

1. `infra/docker-compose.prod.yml` bildet nun den produktiv eingesetzten Top-Level-Mountvertrag ab.
2. `scripts/deploy_prod.sh` beschreibt diesen Mountvertrag nun ebenfalls korrekt; die ASCII-sicheren Logzeilen bleiben bewusst erhalten.
3. `scripts/deploy_sync/sync_core.ps1` prueft nun gegen den echten Live-Containernamen `corapan-web-prod` und meldet Drift gegen den kanonischen Top-Level-Vertrag.
4. `scripts/deploy_sync/README.md` dokumentiert den produktiven Top-Level-Vertrag statt des alten runtime-first-Modells.
5. Die betroffenen vorhandenen Dateien wurden von der lokalen Diagnostik fehlerfrei gemeldet.
6. Die neue Rueckport-Dokumentation ist aktuell unversioniert (`??`) und wird deshalb in `git diff` nicht angezeigt, aber in `git status` korrekt als neue Datei gefuehrt.

## 9. Finaler Status

### Uebernommene Dateien

- `infra/docker-compose.prod.yml`
- `scripts/deploy_prod.sh`
- `scripts/deploy_sync/sync_core.ps1`
- `scripts/deploy_sync/README.md`

### Repo-Bewertung nach dem Backport

Der Repo-Stand bildet fuer die vier geforderten Dateien jetzt den bereits erfolgreich eingesetzten produktiven Zielzustand ab.

Damit sinkt das Risiko, dass der naechste Push genau diese Serveraenderungen wieder zurueckdreht.

### Commit-Bereitschaft

Der Backport-Teil fuer die vier genannten Dateien ist nach durchgefuehrtem Diff- und Diagnostik-Check inhaltlich commit-vorbereitbar, vorbehaltlich einer finalen Sichtung der gesamten Arbeitskopie.

### Offene Folgearbeit

1. Die Reset-Logik in `scripts/deploy_prod.sh` bleibt fachlich riskant und sollte separat beurteilt und ggf. in einem eigenen Run korrigiert werden.
2. Die deploy_sync-Dokumentation kann spaeter noch vollstaendig gegen die inzwischen kanonische Produktionsrealitaet harmonisiert werden, insbesondere dort, wo noch historisch runtime-basierte Detailtexte stehen.
3. Vor einem echten Commit sollte entschieden werden, ob die temp-Vergleichsdateien unter `tmp/prod_backport/` als lokale Arbeitsartefakte bestehen bleiben oder wieder entfernt werden sollen.