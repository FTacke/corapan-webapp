# Storage Cleanup Inventory 2026-03-20

Datum: 2026-03-20
Umgebung: Production live, strikt read-only
Scope: Kapazitaets- und Cleanup-Inventur fuer CORAPAN mit Fokus auf BlackLab-nahe Daten, Parallelbaeume und belegbare Speicherpotenziale; keine Loeschung, keine Verschiebung, keine Container-Neustarts, keine Deploys

## 1. Anlass / Ziel

Die vorangegangene BlackLab-Pfadinventur hat gezeigt:

- mehrere parallele Datenbaeume unter Top-Level und Runtime existieren gleichzeitig
- BlackLab liest produktiv Top-Level `data/blacklab_index`
- BlackLab-nahe Export-, Input- und Backup-Pfade liegen parallel in beiden Baeumen
- der freie Speicher liegt nur noch bei rund `6.3G`

Ziel dieser Analyse ist eine belastbare read-only Antwort auf vier Fragen:

1. Welche Verzeichnisse verbrauchen aktuell den meisten Speicher?
2. Welche BlackLab-nahen Pfade sind identisch, dupliziert, aktiv, historisch oder offen?
3. Welche Cleanup-Kandidaten lassen sich konservativ ueberhaupt diskutieren?
4. Reicht das realistische Cleanup-Potenzial aus, um eine spaetere Migrationswelle freizuschalten?

## 2. Gesamt-Speicheruebersicht

### Befund 2A - Die Instanz hat nur noch geringen operativen Puffer

- Beobachtung:
  `df -h` zeigt auf `/` und `/srv` jeweils `50G` Gesamtgroesse, `43G` benutzt, `6.3G` frei, also `88%` Belegung.
- Bewertung:
  Der freie Speicher ist fuer eine produktive Instanz mit parallelen Datenbaeumen, BlackLab-Build-/Publish-Artefakten und moeglicher Spaetermigration knapp.
- Risiko:
  hoch
- Empfehlung:
  Kapazitaet als harte Freigabebedingung behandeln, nicht als Spaetthema

### Befund 2B - Die beiden relevanten Datenbaeume sind jeweils gross

- Beobachtung:
  Sowohl `/srv/webapps/corapan/data` als auch `/srv/webapps/corapan/runtime/corapan/data` belegen jeweils `3.4G`.
- Bewertung:
  Die Parallelrealitaet betrifft nicht nur Einzelverzeichnisse, sondern zwei fast gleich grosse Oberbaeume.
- Risiko:
  hoch
- Empfehlung:
  Cleanup immer auf Oberbaum-Ebene mitdenken, nicht nur auf Einzelverzeichnis-Ebene

## 3. Top-Verbraucher nach Verzeichnis

### 3.1 Top-Level `/srv/webapps/corapan/data`

| Pfad | Groesse | Kurzbewertung |
|---|---:|---|
| `/srv/webapps/corapan/data/blacklab_export` | `1.5G` | gross, BlackLab-nah, Nutzung nicht voll geklaert |
| `/srv/webapps/corapan/data/tsv` | `730M` | gross, Inputdaten, nur legacy/manuell belegt |
| `/srv/webapps/corapan/data/tsv_for_index` | `365M` | vorbereitete Inputdaten, nur legacy/manuell belegt |
| `/srv/webapps/corapan/data/blacklab_index` | `279M` | aktiver Live-Index, nicht cleanup-faehig |
| `/srv/webapps/corapan/data/blacklab_index.bak_2026-01-16_003920` | `279M` | Backup |
| `/srv/webapps/corapan/data/blacklab_index.bad_2026-01-19_104135` | `279M` | Quarantaene / bad |
| `/srv/webapps/corapan/data/tsv_json_test` | `9.3M` | kleine Testausgaben |
| `/srv/webapps/corapan/data/blacklab_index.new.leftover_2026-01-15_193558` | `0` | leerer Leftover-Pfad |

### 3.2 Runtime `/srv/webapps/corapan/runtime/corapan/data`

| Pfad | Groesse | Kurzbewertung |
|---|---:|---|
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_export` | `1.5G` | aktiv fuer Web-App-docmeta, nicht cleanup-faehig |
| `/srv/webapps/corapan/runtime/corapan/data/tsv` | `730M` | grosses Duplikat, aktive Nutzung nicht belegt |
| `/srv/webapps/corapan/runtime/corapan/data/tsv_for_index` | `365M` | Duplikat, aktive Nutzung nicht belegt |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index` | `279M` | Duplikat, kein Live-Leser belegt |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bak_2026-01-16_003920` | `279M` | Backup-Duplikat |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bad_2026-01-19_104135` | `279M` | Quarantaene-Duplikat |
| `/srv/webapps/corapan/runtime/corapan/data/tsv_json_test` | `9.3M` | kleine Testausgaben |
| `/srv/webapps/corapan/runtime/corapan/data/public` | `7.2M` | aktive Runtime-Daten |
| `/srv/webapps/corapan/runtime/corapan/data/db` | `56K` | aktive Runtime-Daten |
| `/srv/webapps/corapan/runtime/corapan/data/counters` | `32K` | aktive Runtime-Daten |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.new.leftover_2026-01-15_193558` | `0` | leerer Leftover-Pfad |

## 4. BlackLab-relevante Datenmengen (detailliert)

### Befund 4A - Die groessten BlackLab-nahen Blöcke sind Export und Inputs, nicht der Live-Index selbst

- Beobachtung:
  Die eigentlichen Live- und Schatten-Indizes liegen jeweils nur bei `279M`. Deutlich groesser sind:
  - `blacklab_export`: je `1.5G`
  - `tsv`: je `730M`
  - `tsv_for_index`: je `365M`
- Bewertung:
  Das Speicherthema wird nicht primaer vom aktiven Live-Index bestimmt, sondern von Export- und Input-Artefakten sowie deren Duplikaten.
- Risiko:
  hoch
- Empfehlung:
  Cleanup-Priorisierung zuerst an grossen Doppelpfaden ausrichten, nicht am Live-Index

### 4.1 Detaillierte BlackLab-nahe Pfade

| Pfad | Groesse | Dateien | Manifest-/Hashlage | Bemerkung |
|---|---:|---:|---|---|
| `/srv/webapps/corapan/data/blacklab_index` | `279M` | `74` | Manifest `53de42cc47f488dd8a1383bd6afc6fba387075a4d6d3bd08a6a014961abdaed8` | aktiver Live-Index |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index` | `279M` | `74` | identischer Manifest-Hash | Duplikat des Live-Index |
| `/srv/webapps/corapan/data/blacklab_index.bak_2026-01-16_003920` | `279M` | `74` | Manifest `182f143adde6e240c5cfe7d0ef6be0474a1b7952a1663794dfb0c544d6016bad` | Backup |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bak_2026-01-16_003920` | `279M` | `74` | identischer Manifest-Hash | Backup-Duplikat |
| `/srv/webapps/corapan/data/blacklab_index.bad_2026-01-19_104135` | `279M` | `74` | Manifest `b820ced47baf3183a7b8eff4545046d224a0f3f9399b99f8e23613f1eff71917` | Quarantaene |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bad_2026-01-19_104135` | `279M` | `74` | identischer Manifest-Hash | Quarantaene-Duplikat |
| `/srv/webapps/corapan/data/blacklab_export` | `1.5G` | `738` | Manifest `38d354fd0bb38cbad32b67d43bf06ebd51f38c884f1f6adaabc7a16dccdc3a8d` | Top-Level-Export |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_export` | `1.5G` | `738` | identischer Manifest-Hash; `docmeta.jsonl`-Hash identisch `6b00b8b7a32765c43ebebbf50596dc3f466f485cd7e7f604ec208b01b5c57db7` | Runtime-Export, aktiv fuer Web-App |
| `/srv/webapps/corapan/data/tsv` | `730M` | `293` | Manifest `ed336742a192d46c15f1ce29331c7ea7bcb1c47183aa9ed9e1feccf6264d82fa` | Top-Level-Input |
| `/srv/webapps/corapan/runtime/corapan/data/tsv` | `730M` | `293` | identischer Manifest-Hash | Runtime-Duplikat |
| `/srv/webapps/corapan/data/tsv_for_index` | `365M` | `146` | Manifest `8c3cedbebca5ad17d3f0408bd74328b27d975c5af0a4811acb868f44a86ab6b2` | Top-Level-vorbereitete Inputs |
| `/srv/webapps/corapan/runtime/corapan/data/tsv_for_index` | `365M` | `146` | identischer Manifest-Hash | Runtime-Duplikat |
| `/srv/webapps/corapan/data/tsv_json_test` | `9.3M` | `5` | Manifest `0da43810a951764de5608caf4c27295fb02bffc78f0681e59cbf980031913262` | Testausgaben |
| `/srv/webapps/corapan/runtime/corapan/data/tsv_json_test` | `9.3M` | `5` | identischer Manifest-Hash | Test-Duplikat |
| `/srv/webapps/corapan/data/blacklab_index.new.leftover_2026-01-15_193558` | `0` | `0` | leer | Leftover |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.new.leftover_2026-01-15_193558` | `0` | `0` | leer | Leftover-Duplikat |

## 5. Duplikat-Analyse

### Befund 5A - Die BlackLab-nahen Hauptverzeichnisse sind top-level und runtime jeweils inhaltlich identisch

- Beobachtung:
  Fuer alle grossen BlackLab-nahen Verzeichnisse wurden identische Dateizaehlungen, identische Groessenordnungen und identische Manifest-Hashes zwischen Top-Level und Runtime belegt:
  - `blacklab_index`
  - `blacklab_export`
  - `tsv`
  - `tsv_for_index`
  - `tsv_json_test`
  - `blacklab_index.bak_*`
  - `blacklab_index.bad_*`
- Bewertung:
  Es liegt aktuell kein Driftbeleg vor. Die Parallelbaeume sind echte Duplikate, nicht nur aehnliche Verzeichnisse.
- Risiko:
  hoch, weil identische Inhalte die Verwechslungsgefahr erhoehen
- Empfehlung:
  vor jedem Cleanup erst pro Datenklasse einen kanonischen Pfad benennen und dann nur die Nicht-Kanonik ins Cleanup-Fenster nehmen

### Befund 5B - Identisch heisst nicht loeschbar

- Beobachtung:
  Einige identische Verzeichnisse sind trotz Duplikatcharakter produktiv gebunden:
  - Top-Level `blacklab_index` ist aktiver Live-Leserpfad
  - Runtime `blacklab_export` ist aktiver Web-App-docmeta-Pfad
- Bewertung:
  Inhaltliche Gleichheit ist nur ein Duplikatbeleg, kein Freigabesignal fuer Loeschung.
- Risiko:
  sehr hoch
- Empfehlung:
  Cleanup-Entscheidungen immer mit Verbraucher-Matrix koppeln

## 6. Klassifikation je Pfad

| Pfad | Klasse | Begruendung |
|---|---|---|
| `/srv/webapps/corapan/data/blacklab_index` | `ACTIVE_CANONICAL` | aktiver BlackLab-Live-Leserpfad |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_export` | `ACTIVE_CANONICAL` | aktiver Runtime-docmeta-Pfad der Web-App |
| `/srv/webapps/corapan/runtime/corapan/data/public` | `ACTIVE_CANONICAL` | aktive Runtime-Daten |
| `/srv/webapps/corapan/runtime/corapan/data/db` | `ACTIVE_CANONICAL` | aktive Runtime-Daten |
| `/srv/webapps/corapan/runtime/corapan/data/counters` | `ACTIVE_CANONICAL` | aktive Runtime-Daten |
| `/srv/webapps/corapan/data/blacklab_export` | `ACTIVE_LEGACY` | kein aktiver Leser belegt, aber Legacy-/Ops-Nutzung nicht ausgeschlossen |
| `/srv/webapps/corapan/data/tsv` | `ACTIVE_LEGACY` | nur legacy/manuelle Build-Bezuege belegt |
| `/srv/webapps/corapan/data/tsv_for_index` | `ACTIVE_LEGACY` | nur legacy/manuelle Build-Bezuege belegt |
| `/srv/webapps/corapan/runtime/corapan/data/tsv` | `DUPLICATE` | identischer Runtime-Duplikatbaum ohne belegten aktiven Verbraucher |
| `/srv/webapps/corapan/runtime/corapan/data/tsv_for_index` | `DUPLICATE` | identischer Runtime-Duplikatbaum ohne belegten aktiven Verbraucher |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index` | `DUPLICATE` | identischer Index-Duplikatbaum, kein Live-Leser belegt |
| `/srv/webapps/corapan/data/blacklab_index.bak_2026-01-16_003920` | `BACKUP` | Top-Level-Backup mit benannter Rollback-Semantik |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bak_2026-01-16_003920` | `BACKUP` | Runtime-Backup-Duplikat |
| `/srv/webapps/corapan/data/blacklab_index.bad_2026-01-19_104135` | `QUARANTINE` | Top-Level-bad-Pfad |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bad_2026-01-19_104135` | `QUARANTINE` | Runtime-bad-Duplikat |
| `/srv/webapps/corapan/data/blacklab_index.new.leftover_2026-01-15_193558` | `UNCLEAR` | leerer Leftover-Pfad, aber ohne formale Freigabe |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.new.leftover_2026-01-15_193558` | `UNCLEAR` | leerer Leftover-Pfad, aber ohne formale Freigabe |
| `/srv/webapps/corapan/data/tsv_json_test` | `UNCLEAR` | Testausgaben, nur Dokumentationsbeleg, kein aktiver Verbraucher belegt |
| `/srv/webapps/corapan/runtime/corapan/data/tsv_json_test` | `UNCLEAR` | Testausgaben-Duplikat, kein aktiver Verbraucher belegt |
| `/srv/webapps/corapan/data/public` | `UNCLEAR` | leer/klein, keine aktuelle BlackLab-Relevanz belegt |
| `/srv/webapps/corapan/data/stats_temp` | `UNCLEAR` | leer/klein, keine aktuelle BlackLab-Relevanz belegt |
| `/srv/webapps/corapan/runtime/corapan/data/stats_temp` | `ACTIVE_CANONICAL` | Runtime-Temp fuer App und Deploy-Write-Tests |

## 7. Sofort loeschbare Kandidaten (nur Vorschlag, nicht ausfuehren)

### Befund 7A - Wirklich konservative Sofortkandidaten sind derzeit klein

- Beobachtung:
  Sicher leer und ohne belegten aktiven Inhalt sind nur:
  - `/srv/webapps/corapan/data/blacklab_index.new.leftover_2026-01-15_193558`
  - `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.new.leftover_2026-01-15_193558`
- Bewertung:
  Diese Kandidaten sind zwar plausibel entbehrlich, bringen aber praktisch keinen Speichergewinn.
- Risiko:
  niedrig
- Empfehlung:
  selbst solche Kandidaten nur im Rahmen einer formalen Cleanup-Welle anfassen; sie loesen das Kapazitaetsproblem nicht

### 7.1 Vorschlagsliste konservativ

| Kandidat | Groesse | Warum ueberhaupt Kandidat | Restrisiko |
|---|---:|---|---|
| `/srv/webapps/corapan/data/blacklab_index.new.leftover_2026-01-15_193558` | `0` | leerer Leftover-Pfad | niedrig |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.new.leftover_2026-01-15_193558` | `0` | leerer Leftover-Pfad | niedrig |
| eine der beiden `tsv_json_test`-Kopien | `9.3M` | identische Testausgaben, kein aktiver Verbraucher belegt | mittel |

## 8. Riskante Loeschkandidaten

### Befund 8A - Die grossen Kandidaten sind fast alle riskant

- Beobachtung:
  Die grossen Speicherbloecke sind zugleich an aktive oder nicht abschliessend geklaerte Verbraucher gekoppelt.
- Bewertung:
  Das eigentliche Cleanup-Potenzial sitzt fast nur in riskanten oder mindestens pruefpflichtigen Pfaden.
- Risiko:
  sehr hoch
- Empfehlung:
  riskante Kandidaten nur nach separater Verbraucher- und Rollback-Freigabe anfassen

### 8.1 Riskante Kandidatenliste

| Kandidat | Groesse | Risiko |
|---|---:|---|
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index` | `279M` | Duplikat, aber historisch Teil der BlackLab-Schattenrealitaet |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bak_2026-01-16_003920` | `279M` | Backup-Duplikat; Rollback-Semantik vor Loeschung klaeren |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bad_2026-01-19_104135` | `279M` | Quarantaene-Duplikat; Fehlerhistorie vor Loeschung klaeren |
| `/srv/webapps/corapan/data/blacklab_export` | `1.5G` | kein aktiver Leser belegt, aber Legacy-/Ops-Nutzung nicht ausgeschlossen |
| `/srv/webapps/corapan/runtime/corapan/data/tsv` | `730M` | kein aktiver Verbraucher belegt, aber Input-/Buildbezug nicht formal abgeklemmt |
| `/srv/webapps/corapan/data/tsv` | `730M` | Legacy-/Manuell-Build-Bezug im Repo belegt |
| `/srv/webapps/corapan/runtime/corapan/data/tsv_for_index` | `365M` | vorbereitetes Input-Duplikat ohne klare Stilllegung |
| `/srv/webapps/corapan/data/tsv_for_index` | `365M` | Legacy-/Manuell-Build-Bezug im Repo belegt |
| `/srv/webapps/corapan/data/blacklab_index.bak_2026-01-16_003920` | `279M` | Top-Level-Backup mit naheliegender Rollback-Rolle |
| `/srv/webapps/corapan/data/blacklab_index.bad_2026-01-19_104135` | `279M` | Top-Level-Quarantaene mit moeglicher Diagnose-/Restore-Rolle |

## 9. Speicherpotenzial (wie viel frei machbar waere)

### Befund 9A - Das sichere Sofortpotenzial ist praktisch null

- Beobachtung:
  Die wirklich konservativen Sofortkandidaten sind zwei leere Leftover-Verzeichnisse und eventuell eine Testkopie im Bereich `9.3M`.
- Bewertung:
  Der sofort, konservativ und ohne tieferen Vorlauf erzielbare Effekt liegt praktisch bei `0.0G` bis `0.01G`.
- Risiko:
  niedrig
- Empfehlung:
  diesen Effekt nicht mit echtem Kapazitaetsgewinn verwechseln

### Befund 9B - Das konservativ realistische Potenzial einer geplanten Cleanup-Welle liegt nur im Teilbereich unter 1 GB

- Beobachtung:
  Wenn in einer geplanten Cleanup-Welle wenigstens folgende Runtime-Duplikate freigegeben wuerden:
  - `runtime/.../blacklab_index.bak_*` (`279M`)
  - `runtime/.../blacklab_index.bad_*` (`279M`)
  - optional eine `tsv_json_test`-Kopie (`9.3M`)
  dann liegt das konservativ realistische Potenzial bei rund `567M`, also etwa `0.55G`.
- Bewertung:
  Das ist das erste halbwegs belastbare Cleanup-Potenzial, aber es bleibt fuer eine spaetere Migration zu klein.
- Risiko:
  mittel
- Empfehlung:
  dieses Potenzial nur als Zwischenschritt sehen, nicht als Migrationsfreigabe

### Befund 9C - Das groessere Potenzial sitzt in Pfaden, die noch blockiert sind

- Beobachtung:
  Zusaetzlich groesseres Potenzial laege in:
  - `data/blacklab_export` (`1.5G`)
  - `runtime/.../tsv` (`730M`)
  - `runtime/.../tsv_for_index` (`365M`)
  - eventuell weiteren Legacy-/Top-Level-Inputpfaden
- Bewertung:
  Das waere nominell viel groesser, ist aber nicht ohne weitere Freigabe als realistischer Cleanup-Effekt zu verbuchen.
- Risiko:
  hoch
- Empfehlung:
  hier erst Verbraucherabschaltung und Rollback-Konzept schaffen, dann ueber Cleanup reden

## 10. Risiken eines falschen Cleanup

### Befund 10A - Live-Suche koennte indirekt oder direkt ausfallen

- Beobachtung:
  Top-Level `blacklab_index` ist aktiver Live-Leserpfad des BlackLab-Containers.
- Bewertung:
  Jede Verwechslung zwischen aktivem und dupliziertem Indexpfad waere kritisch.
- Risiko:
  sehr hoch
- Empfehlung:
  aktive und Schatten-Indizes vor einer Cleanup-Welle unmissverstaendlich markieren

### Befund 10B - Web-App-Funktionen koennten still beschaedigt werden

- Beobachtung:
  Runtime `blacklab_export` ist aktiver docmeta-Pfad der Web-App.
- Bewertung:
  Ein Cleanup aus der Perspektive "BlackLab braucht das nicht" waere hier fachlich falsch.
- Risiko:
  hoch
- Empfehlung:
  Suchindex und Web-App-docmeta im Cleanup strikt getrennt behandeln

### Befund 10C - Rollback- und Diagnosepfade koennten zu frueh verschwinden

- Beobachtung:
  `bak_*` und `bad_*` sind nicht nur Speicherverbraucher, sondern tragen erkennbar Rollback- bzw. Quarantaene-Semantik.
- Bewertung:
  Ein falsches Cleanup kann die eigene Rueckfallstrategie vernichten.
- Risiko:
  hoch
- Empfehlung:
  Backup- und bad-Pfade erst nach expliziter Retentionsentscheidung anfassen

### Befund 10D - Build-/Input-Pfade koennten manuelle Sonderprozesse treffen

- Beobachtung:
  `tsv` und `tsv_for_index` haben weiterhin Repo-Bezuege in Build- und Legacy-Skripten.
- Bewertung:
  Auch wenn kein aktiver Lauf beobachtet wurde, sind diese Pfade nicht als frei disponibel nachgewiesen.
- Risiko:
  hoch
- Empfehlung:
  vor Cleanup alle manuellen BlackLab- oder Ops-Routinen abschliessend inventarisieren

## 11. Voraussetzungen fuer sichere Cleanup-Welle

### Befund 11A - Eine sichere Cleanup-Welle braucht mehr als eine Groessenliste

- Beobachtung:
  Die Groessenlage ist jetzt belegt, aber fuer mehrere grosse Kandidaten fehlt noch die formale Freigabe der Verbraucher- und Rollback-Seite.
- Bewertung:
  Ein sicherer Cleanup ist derzeit vorbereitbar, aber noch nicht freigabefaehig fuer die groessten Bloecke.
- Risiko:
  hoch
- Empfehlung:
  vor einer Cleanup-Welle mindestens diese Punkte abschliessen:

1. kanonischen Pfad pro Datenklasse festlegen
2. Legacy-/Ops-Verbraucher fuer `blacklab_export`, `tsv`, `tsv_for_index` final pruefen
3. Rollback-/Quarantaene-Regeln fuer `bak_*` und `bad_*` schriftlich festlegen
4. Cleanup-Reihenfolge mit Stop-Kriterien dokumentieren
5. Kapazitaetsziel definieren, ab wann Migration wieder realistisch wird

## 12. Executive Summary

Die Speicherlage von CORAPAN ist angespannt: Auf `/srv` sind nur noch rund `6.3G` frei, waehrend allein die beiden relevanten Datenbaeume jeweils `3.4G` belegen. Die groessten Speicherverbraucher sind nicht der Live-Index selbst, sondern parallele Export- und Inputpfade wie `blacklab_export`, `tsv` und `tsv_for_index`.

Die read-only Inventur belegt, dass die grossen BlackLab-nahen Pfade zwischen Top-Level und Runtime aktuell inhaltlich identisch sind. Das gilt fuer aktive Indizes, Backups, bad-Pfade, Exporte, TSV-Inputs, vorbereitete Input-Mengen und sogar die kleinen Testausgaben. Diese Gleichheit macht die Lage nicht einfacher, sondern gefaehrlicher: Verwechslung und falsches Cleanup werden wahrscheinlicher.

Wirklich konservative Sofortkandidaten bringen praktisch keinen Speichergewinn. Das erste halbwegs realistische, aber immer noch vorsichtige Cleanup-Potenzial liegt nur bei rund `0.55G` und sitzt in Runtime-Duplikaten von Backup-/bad-Pfaden. Das groessere Speicherpotenzial steckt in deutlich riskanteren Legacy- und Input-Pfaden, fuer die Verbraucher- und Rollback-Fragen noch nicht final geklaert sind.

Fazit: Eine spaetere Migration bleibt aktuell kapazitiv und organisatorisch blockiert. Vorher braucht CORAPAN eine geplante Cleanup-Welle mit formaler Pfadklassifikation, Verbraucher-Abschluss und Retentions-/Rollback-Regeln.