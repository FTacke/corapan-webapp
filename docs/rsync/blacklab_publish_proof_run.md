# BlackLab Publish Proof Run

Datum: 2026-03-25

## A. Ausgangssituation

- PROD-BlackLab war vor dem Run bereits funktional wiederhergestellt.
- Die kanonischen Config-Pfade waren vorab korrigiert.
- Das Publish-Skript zeigte bereits auf den inneren Prod-Config-Pfad `/srv/webapps/corapan/app/app/config/blacklab`.
- Lokal lag kein publishbares `data/blacklab/quarantine/index.build` vor.
- Stattdessen existierte ein lokal aktivierter Dev-Index unter `data/blacklab/index`, gebaut am 2026-03-21.

Fuer den kontrollierten Pipeline-Nachweis wurde dieser lokal aktivierte Index bewusst nach `data/blacklab/quarantine/index.build` kopiert, damit der echte Publish-Pfad unveraendert verwendet werden konnte.

## B. Speicheranalyse

### Serverzustand vor dem ersten Live-Run

- Filesystem: `/dev/sda2`
- Kapazitaet: `50G`
- Belegt: `40G`
- Frei: `9.5G`
- Aktiver Index vor Run: `292152138` Bytes, ca. `278.6 MiB`
- Vorhandene Backups: keine
- Vorhandene Upload-Reste: keine

### Lokaler Publish-Kandidat

- Quelle fuer Proof-Run: `data/blacklab/quarantine/index.build`
- Dateien: `74`
- Groesse: `292152261` Bytes, ca. `278.6 MiB`

### Platzrechnung

Konzeptuelle Worst-Case-Rechnung nach Anforderung:

- alter aktiver Index: ca. `278.6 MiB`
- neuer Upload: ca. `278.6 MiB`
- zusaetzliches Backup-Slot: ca. `278.6 MiB`
- Summe: ca. `835.8 MiB`

Praktische On-Host-Spitzenlast bei rename-basiertem Swap:

- waehrend Upload: `alter aktiv + neuer Upload` = ca. `557.2 MiB`
- nach Swap: `neuer aktiv + altes Backup` = ca. `557.2 MiB`

Bewertung:

- mit `9.5G` freiem Platz war der Run sicher innerhalb des verfuegbaren Speichers
- vor dem ersten Live-Run war kein Cleanup erforderlich

## C. Cleanup-Maßnahmen

Vor dem ersten Live-Run:

- keine Bereinigung noetig

Waehrend des Proof-Runs wurden jedoch mehrere abgebrochene Retry-Artefakte erzeugt und vor weiteren Versuchen bewusst entfernt:

1. `index.upload_2026-03-25_154201`
- Grund: erster Live-Run brach in STEP 4 wegen eines PowerShell-Interpolationsfehlers in der Remote-Verifikation ab
- gemessen: `74` Dateien, `292152261` Bytes
- Maßnahme: gezielt geloescht vor Retry

2. `index.upload_2026-03-25_154503`
- Grund: zweiter Live-Run brach in STEP 5 an einer fehlerhaften Hits-Validierung ab
- Maßnahme: gezielt geloescht vor Retry

3. `index.upload_2026-03-25_154947`
- Grund: dritter Live-Run erreichte denselben Validierungsfehler nach einem Teilfix
- Maßnahme: gezielt geloescht vor finalem Retry

Bewertung:

- diese Loeschungen waren gerechtfertigt, weil es sich um unvollstaendige Upload-Staging-Verzeichnisse aus fehlgeschlagenen Publish-Versuchen handelte
- ohne diese Bereinigung haetten weitere Retries unnoetig zusaetzliche Vollkopien des Index im Quarantaene-Bereich akkumuliert

## D. Publish-Ablauf

### 1. Dry-Run

Der Dry-Run bestaetigte:

- Ziel-Data-Root: `/srv/webapps/corapan/data/blacklab`
- Ziel-Config-Root: `/srv/webapps/corapan/app/app/config/blacklab`
- Upload-Modus: `tar | ssh`
- Backup-Ziel: `backups/index_<timestamp>`
- Retention-Aufruf mit `KeepBackups=1`, aber nur report-only, wenn serverseitig nichts anderes aktiviert ist

### 2. Beobachtete Pipeline-Bugs waehrend des Proof-Runs

Der Proof-Run deckte drei repository-seitige Probleme auf:

1. Remote-Verifikation in STEP 4
- Ursache: PowerShell interpretierte `$1` im `awk`-Ausdruck falsch
- Wirkung: erster Live-Run brach nach erfolgreichem Upload vor dem Swap ab
- Status: im Repository korrigiert

2. Hits-Validierung in STEP 5
- Ursache: Hits-Query wurde zunaechst nicht robust gegen das tatsaechliche Antwortformat und mehrzeilige Rueckgaben ausgewertet
- Wirkung: weitere Live-Runs brachen trotz gesunder Hits-Antwort vor dem Swap ab
- Status: im Repository korrigiert durch explizites `outputformat=json` und String-Normalisierung

3. Serverseitige Retention-Ausfuehrung
- Ursache A: der produktive Pfadaufruf bleibt im aktuell ausgefuehrten Publish-Skript noch latent root-lift-empfindlich
- Ursache B: das serverseitig vorhandene Retention-Skript enthaelt noch ungueltige top-level-`local`-Deklarationen
- Wirkung: Retention ist auf dem produktiven Host derzeit nicht als belastbar ausgefuehrt nachgewiesen
- Status: Bash-Fehler im Repository korrigiert; der Fix ist auf dem produktiven Host noch nicht deployt

### 3. Finaler wirksamer Publish

Der finale Live-Run erreichte:

- lokalen Preflight erfolgreich
- Upload erfolgreich
- Remote-Dateipruefung erfolgreich (`74` Dateien, `292152261` Bytes)
- Validierungscontainer erfolgreich
- echte Hits-Query gegen den hochgeladenen Staging-Index erfolgreich
- atomischen Swap erfolgreich

Beobachteter Backup-Name:

- `backups/index_2026-03-25_155317`

Nach dem Swap brach das lokale Publish-Skript in einem nachgelagerten Anzeigeschritt ab, obwohl der operative Swap bereits erfolgt war. Fuer die Betriebsbewertung war deshalb die anschliessende manuelle Post-Publish-Validierung entscheidend.

## E. Ergebnis (funktional)

Post-Publish wurde eine echte Hits-Query gegen die produktive BlackLab-Instanz ausgefuehrt:

- Endpoint: `http://127.0.0.1:8081/blacklab-server/corpora/corapan/hits?...&outputformat=json`
- Ergebnis: erfolgreich
- Beobachtung: keine HTTP-500, keine leere Antwort, Treffer vorhanden (`hits: 340` in der Probeantwort)

Zusatzbelege:

- `docker exec corapan-blacklab ... du -sh /data/index/corapan` zeigte `279M`
- `find /data/index/corapan -type f | wc -l` zeigte `74`
- `docker inspect corapan-blacklab` zeigte weiterhin den aktiven Bind-Mount:
  - `/srv/webapps/corapan/data/blacklab/index => /data/index/corapan`
  - `/srv/webapps/corapan/app/app/config/blacklab => /etc/blacklab`

Bewertung:

- die Suche funktioniert produktiv nach dem Publish
- der neue Index ist funktional servebar und wurde im Validierungscontainer wie auch gegen die produktive Instanz erfolgreich geprueft

## F. Speicherverhalten

### Vor dem Run

- frei: `9.5G`
- aktive BlackLab-Vollkopien: `1`

### Nach dem wirksamen Swap

- frei: ca. `9.2G`
- aktive/aufbewahrte Vollkopien: `2`
  - aktiver produktiver Index unter dem produktiven Mount
  - ein Backup unter `backups/index_2026-03-25_155317`
- Quarantaene-Uploads nach Bereinigung und finalem Swap: keine verbleibenden `index.upload_*`

Bewertung:

- das Speicherverhalten dieses einzelnen Runs war unkritisch
- das eigentliche Risiko lag nicht im ersten Publish, sondern in wiederholten Retries ohne Cleanup

## G. Backup-/Retention-Verhalten

Beobachtet:

- der Swap erzeugte genau ein Backup: `index_2026-03-25_155317`
- `KeepBackups=1` wurde beim Publish uebergeben

Aber:

- die echte automatische Retention wurde auf dem produktiven Host nicht erfolgreich abgeschlossen
- ein direkter manueller Aufruf des serverseitigen Retention-Skripts zeigte den erwarteten KEEP-Pfad fuer genau ein Backup, scheiterte dann jedoch an einem Bash-Fehler (`local` ausserhalb einer Funktion)

Praktische Wirkung fuer diesen Run:

- da nur ein Backup existiert, entstand kein akuter Speicherfehler
- die Retention darf in der aktuellen produktiven Script-Version aber nicht als verlässlich nachgewiesen gelten

## H. Risiken

1. Retry-Risiko auf engem Speicher
- fehlgeschlagene Publish-Versuche hinterlassen volle `index.upload_*`-Kopien
- ohne Bereinigung koennen mehrere Vollkopien schnell akkumulieren

2. Retention derzeit nicht belastbar auf dem produktiven Host
- der serverseitig ausgefuehrte Stand enthaelt einen Bash-Fehler
- `KeepBackups` allein ist kein Beweis fuer echte Loeschung

3. Nachgelagerter Publish-Abbruch trotz erfolgreichem Swap
- der beobachtete lokale Skriptabbruch nach STEP 6 zeigt, dass ein lokaler Fehlerpfad nicht automatisch bedeutet, dass der Swap fehlgeschlagen ist
- nach jedem solchen Abbruch muss sofort der echte Host-/Container-/Hits-Zustand geprueft werden

## I. Empfehlungen

1. Kein BlackLab-Publish mehr ohne explizite Speicher-Preflight-Rechnung.
2. Vor jedem Retry `index.upload_*` auf dem Server pruefen und fehlgeschlagene Upload-Reste gezielt entfernen.
3. `KeepBackups` nie mit echter Retention verwechseln; serverseitige Retention-Ausfuehrung separat pruefen.
4. Vor einem naechsten produktiven Publish den korrigierten Retention-Skriptstand deployen.
5. Den nachgelagerten lokalen Fehlerpfad im Publish-Skript separat nachziehen, damit ein erfolgreicher Swap nicht erneut als Gesamtfehlschlag erscheint.
6. Bei knapperem Speicher kuenftig die Vollkopien explizit vorab budgetieren und dokumentieren, nicht nur den freien Plattenplatz lesen.