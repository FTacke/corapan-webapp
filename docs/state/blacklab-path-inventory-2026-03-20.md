# BlackLab Path Inventory 2026-03-20

Datum: 2026-03-20
Umgebung: Production live, read-only Voranalyse fuer eine moegliche spaetere BlackLab-Konsolidierung
Scope: Bestandsaufnahme, Verbraucher-Matrix, Zielbild und Risikodokumentation fuer BlackLab-relevante Pfade; keine Aenderung an Live-Pfaden, Mounts, Containern, Compose oder Daten

## 1. Anlass / Ziel der Analyse

BlackLab ist in CORAPAN produktiv aktiv, aber weiterhin ein Sonderfall ausserhalb des Compose-V2-gemanagten Web/DB-Stacks. Der laufende BlackLab-Container liest den Suchindex produktiv aus dem Top-Level-Pfad `/srv/webapps/corapan/data/blacklab_index`, haengt gleichzeitig an zwei Docker-Netzen und verwendet zusaetzlich ein anonymes Docker-Volume auf Containerpfad `/data`.

Parallel existieren weitere BlackLab-nahe Pfade unter:

- `/srv/webapps/corapan/data/*`
- `/srv/webapps/corapan/runtime/corapan/data/*`
- Repo-lokalen Build- und Deploy-Skripten
- der produktiven BlackLab-Konfiguration unter `/srv/webapps/corapan/app/config/blacklab`

Ziel dieser Analyse ist nicht eine Migration oder Bereinigung, sondern eine belastbare Antwort auf vier Fragen:

1. Welche BlackLab-relevanten Pfade existieren heute wirklich auf Host, im Container und im Repo?
2. Wer liest und wer schreibt diese Pfade nach aktueller Evidenz?
3. Welche Pfade sind produktiv massgeblich, welche nur dupliziert, historisch oder offen?
4. Wie koennte eine spaetere Konsolidierung unter `/data/blacklab` prinzipiell aussehen, ohne heute schon eine falsche Zielentscheidung zu treffen?

## 2. Methodik / Read-only-Grenzen

### 2.1 Quellenprioritaet

Bei widerspruechlichen Quellen galt strikt diese Reihenfolge:

1. Live-Realitaet auf dem Produktionshost
2. kanonische Produktionskonfiguration und laufender Containerzustand
3. relevante Implementierung und Skripte
4. Dokumentation
5. historisches Material

### 2.2 Read-only-Grenzen

Durchgefuehrt wurden ausschliesslich:

- `docker inspect`, `docker logs`, `docker exec` mit lesenden Kommandos
- Verzeichnis- und Dateiinventur per `find`, `stat`, `du`, `df`, `sha256sum`
- Repo-Analyse per Dateilesen und Suchlaeufen
- Host-Ops-Suche in `systemd`- und `cron`-Verzeichnissen

Nicht durchgefuehrt wurden:

- keine Container-Neustarts
- keine Mount- oder Netzwerk-Aenderungen
- kein Compose- oder Deploy-Run
- keine Datenbewegung
- kein `chmod`, `chown`, `mv`, `rm`, `ln`
- keine Korrektur der BlackLab-Pfade

### 2.3 Evidenzklassen

- `SICHER_BELEGT`: direkt aus laufendem Container, Hostinventur oder kanonischem Script ableitbar
- `PLAUSIBEL_WAHRSCHEINLICH`: durch mehrere Indizien gestuetzt, aber nicht als aktiver Lauf zur Beobachtungszeit gesehen
- `UNKLAR_OFFEN`: moeglich oder historisch referenziert, aber aktuell nicht hart belegbar

## 3. Aktueller produktiver BlackLab-Zustand

### Befund 3A - Der produktive Leserpfad ist eindeutig top-level

- Beobachtung:
  Der laufende Container `corapan-blacklab` mountet `/srv/webapps/corapan/data/blacklab_index` read-only nach `/data/index/corapan`. Die BlackLab-Logs melden fortlaufend `Scanning collectionsDir: /data/index` und `Index found: corapan (/data/index/corapan)`.
- Bewertung:
  Der aktive produktive Leserpfad fuer den Suchindex ist sicher belegt: Top-Level Hostpfad `/srv/webapps/corapan/data/blacklab_index`.
- Risiko:
  sehr hoch bei jeder spaeteren Fehlannahme, weil dies der Live-Leser ist
- Empfehlung:
  diesen Pfad bis zu einer vollstaendig vorbereiteten Migrationswelle als Tabuzone behandeln

### Befund 3B - BlackLab hat eine zusaetzliche interne `/data`-Realitaet

- Beobachtung:
  Der Container hat zusaetzlich ein anonymes Docker-Volume nach `/data` gemountet. Darin ist mindestens `/data/user-index` vorhanden, aktuell leer. Gleichzeitig liegt der aktive Index als separater bind mount unter `/data/index/corapan`.
- Bewertung:
  `/data` im Container ist keine reine Sicht auf einen Hostpfad. Es existiert eine Ueberlagerung aus anonymem Docker-Volume und spezifischem bind mount fuer den Produktivindex.
- Risiko:
  hoch fuer jede spaetere Zielstruktur unter `/data/blacklab`, wenn Host- und Container-Pfade gedanklich gleichgesetzt werden
- Empfehlung:
  eine spaetere Zielarchitektur muss Container-Mount-Topologie und Host-Dateibaum getrennt modellieren

### Befund 3C - Die produktive BlackLab-Konfiguration bleibt repo-/app-seitig getrennt vom Datenbaum

- Beobachtung:
  `/srv/webapps/corapan/app/config/blacklab` wird read-only nach `/etc/blacklab` gemountet. `blacklab-server.yaml` setzt `indexLocations` auf `/data/index`.
- Bewertung:
  Die aktuelle Architektur trennt Datenpfad und Konfigurationspfad: Daten liegen unter Top-Level `data`, Konfiguration unter `app/config/blacklab`.
- Risiko:
  mittel, wenn spaeter versucht wird, Konfiguration still in eine neue Datenwurzel hineinzumischen
- Empfehlung:
  `/data/blacklab` spaeter nur als moegliche Datenwurzel betrachten, nicht automatisch auch als neue Config-Heimat

## 4. Inventarisierte BlackLab-relevante Pfade

### 4.1 Host-Pfade

| Pfad | Existenz | Typ | Groesse / Plausibilitaet | Owner / Mode | Status | Evidenz |
|---|---|---|---|---|---|---|
| `/data` | nein | moegliche kuenftige Host-Wurzel | nicht vorhanden | n/a | `SICHER_BELEGT` fehlend | Hostinventur |
| `/data/blacklab` | nein | hypothetisches Ziel | nicht vorhanden | n/a | `SICHER_BELEGT` fehlend | Hostinventur |
| `/srv/webapps/corapan/data` | ja | Top-Level-Datenwurzel | produktiv relevant | `root:root 755` | aktiv, gemischt | Hostinventur, Live-Mounts |
| `/srv/webapps/corapan/data/blacklab_index` | ja | aktiver Suchindex | `279M`, `74` Dateien | `hrzadmin:hrzadmin 755` | produktiv aktiv | Live-Mount, Logs, Dateizaehlung |
| `/srv/webapps/corapan/data/blacklab_index.bak_2026-01-16_003920` | ja | Backup | `279M` | `hrzadmin:hrzadmin 755` | historisch, aber bewusst aufbewahrt | Hostinventur |
| `/srv/webapps/corapan/data/blacklab_index.bad_2026-01-19_104135` | ja | Fehler-/Quarantaene-Pfad | `279M` | `hrzadmin:hrzadmin 777` | historisch | Hostinventur |
| `/srv/webapps/corapan/data/blacklab_index.new.leftover_2026-01-15_193558` | ja | Leftover / Staging-Rest | vernachlaessigbar, leerer Eindruck | `root:root` | historisch / offen | Hostinventur |
| `/srv/webapps/corapan/data/blacklab_export` | ja | Exportdaten / docmeta / TSV-Basis | `1.5G` | `hrzadmin:hrzadmin 770` | dupliziert, Nutzung offen | Hostinventur, Hashvergleich |
| `/srv/webapps/corapan/data/tsv` | ja | Inputdaten | `730M` | `hrzadmin:hrzadmin 755` | historisch oder manuell genutzt | Hostinventur, build-in-prod Skript |
| `/srv/webapps/corapan/data/tsv_for_index` | ja | vorbereitete Index-Inputs | `365M` | `hrzadmin:hrzadmin 755` | historisch oder manuell genutzt | Hostinventur, build-in-prod Skript |
| `/srv/webapps/corapan/data/logs` | nein | moeglicher BlackLab-Logpfad | fehlt | n/a | offen | Hostinventur |
| `/srv/webapps/corapan/runtime/corapan/data` | ja | Runtime-Datenwurzel der Web-App | produktiv relevant fuer App | `hrzadmin:hrzadmin 775` | aktiv, gemischt | Web-Mounts |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index` | ja | paralleler Indexbaum | `279M`, `74` Dateien | `hrzadmin:hrzadmin 775` | dupliziert, kein Live-Leser belegt | Hostinventur, Hashvergleich |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bak_2026-01-16_003920` | ja | Backup-Duplikat | vorhanden | `hrzadmin:hrzadmin 775` | historisch | Hostinventur |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.bad_2026-01-19_104135` | ja | Fehler-/Quarantaene-Duplikat | vorhanden | `hrzadmin:hrzadmin 777` | historisch | Hostinventur |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_index.new.leftover_2026-01-15_193558` | ja | Leftover / Staging-Rest | leerer Eindruck | `hrzadmin:hrzadmin 775` | historisch / offen | Hostinventur |
| `/srv/webapps/corapan/runtime/corapan/data/blacklab_export` | ja | Runtime-export / docmeta | `1.5G` | `hrzadmin:hrzadmin 770` | produktiv fuer Web-App aktiv | Runtime-Resolver, Hashvergleich |
| `/srv/webapps/corapan/runtime/corapan/data/tsv` | ja | Runtime-Inputdaten | `730M` | `hrzadmin:hrzadmin 775` | offen / wahrscheinlich Deploy-Duplikat | Hostinventur |
| `/srv/webapps/corapan/runtime/corapan/data/tsv_for_index` | ja | Runtime-vorbereitete Index-Inputs | `365M` | `hrzadmin:hrzadmin 775` | offen / wahrscheinlich Deploy-Duplikat | Hostinventur |
| `/srv/webapps/corapan/app/config/blacklab` | ja | produktive BlackLab-Konfiguration | wenige KB, 5 Dateien | `root:root 755/644` | produktiv aktiv | Live-Mount, Hostinventur |
| `/srv/webapps/corapan/logs` | ja | allgemeiner Top-Level-Logbaum | vorhanden, nicht BlackLab-spezifisch belegt | nicht vertieft | offen / legacy | fruehere Wellen, Hostinventur |
| `/srv/webapps/corapan/runtime/corapan/logs` | ja | Runtime-Logbaum der Web-App | aktiv fuer Web-App | nicht BlackLab-spezifisch | aktiv fuer App, nicht fuer BlackLab selbst | Post-deploy-Diagnose |

### 4.2 Container-Sicht des laufenden BlackLab-Dienstes

| Containerpfad | Hostquelle | Mount-Typ | RW | Funktion | Status |
|---|---|---|---|---|---|
| `/data` | anonymes Docker-Volume | `volume` | rw | interne BlackLab-Datenwurzel / Zusatzdaten | aktiv, aber teilweise unklar |
| `/data/index/corapan` | `/srv/webapps/corapan/data/blacklab_index` | `bind` | ro | produktiver Suchindex | produktiv aktiv |
| `/etc/blacklab` | `/srv/webapps/corapan/app/config/blacklab` | `bind` | ro | BlackLab-Server- und Corpus-Konfiguration | produktiv aktiv |
| `/data/user-index` | Teil des anonymen `/data`-Volumes | intern | rw | Zusatzpfad, aktuell leer | unklar / offen |

### 4.3 Driftgrad der Duplikate

- `blacklab_index` top-level und runtime haben aktuell jeweils `74` Dateien.
- Der Manifest-Hash beider Indexbaeume ist identisch: `53de42cc47f488dd8a1383bd6afc6fba387075a4d6d3bd08a6a014961abdaed8`.
- `blacklab_export/docmeta.jsonl` ist top-level und runtime ebenfalls identisch: `6b00b8b7a32765c43ebebbf50596dc3f466f485cd7e7f604ec208b01b5c57db7`.

Bewertung:
Aktuell liegt kein inhaltlicher Driftbeleg zwischen diesen Duplikaten vor. Das macht die Parallelpfade aber nicht harmlos, sondern nur aktuell inhaltlich deckungsgleich.

## 5. Verbraucher-Matrix

| Verbraucher / Dienst | Liest | Schreibt | Klasse | Sicherheit |
|---|---|---|---|---|
| laufender Container `corapan-blacklab` | `/srv/webapps/corapan/data/blacklab_index` via `/data/index/corapan`; `/srv/webapps/corapan/app/config/blacklab` via `/etc/blacklab` | kein Host-Schreibpfad belegt; internes `/data`-Volume ist rw | Live-Leser | `SICHER_BELEGT` |
| BlackLab Server intern | `/data/index` laut `blacklab-server.yaml` und Logs | moeglich intern nach `/data/user-index`, aktuell leer | interner Serverpfad | Lesen `SICHER_BELEGT`, Schreiben `UNKLAR_OFFEN` |
| CORAPAN Web-App | BlackLab nur indirekt ueber `BLS_BASE_URL=http://corapan-blacklab:8080/blacklab-server`; `docmeta` aus `runtime/corapan/data/blacklab_export/docmeta.jsonl` | kein BlackLab-Index-Schreibpfad | Leser ueber HTTP plus lokaler docmeta-Leser | `SICHER_BELEGT` |
| `scripts/deploy_sync/publish_blacklab_index.ps1` | lokal `data/blacklab_index.new`; remote Validation gegen `ConfigDir` und temporaren Remote-Index | standardmaessig remote `${BlackLabDataRoot}/blacklab_index.new` und danach `${BlackLabDataRoot}/blacklab_index` | Standard-Publish-Unterbau | `SICHER_BELEGT` im Repo |
| `scripts/deploy_sync/_lib/ssh.ps1` | n/a | definiert `BlackLabDataRoot=/srv/webapps/corapan/data` | kanonische Remote-Pfadauflosung | `SICHER_BELEGT` |
| `scripts/blacklab/run_bls_prod.sh` | prueft `/srv/webapps/corapan/data/blacklab_index` und `/srv/webapps/corapan/app/config/blacklab` | startet Container mit diesen Mounts | manueller Betriebshelfer | `SICHER_BELEGT` im Repo, aktueller Aufruf nicht beobachtet |
| `scripts/blacklab/retain_blacklab_backups_prod.sh` | liest Backup-Verzeichnisse unter `${DATA_ROOT:-/srv/webapps/corapan/data}` | loggt und loescht optional `blacklab_index.bak_*` oder `blacklab_index.backup_*` | manueller / Publish-naher Ops-Helfer | `SICHER_BELEGT` im Repo |
| `scripts/blacklab/build_blacklab_index_prod.sh` | referenziert top-level `data/tsv`, `data/tsv_for_index`, `data/blacklab_index`, `config/blacklab` | waere Top-Level-Schreiber, beendet aber sofort mit `exit 1` | deaktivierter Legacy-Helfer | `SICHER_BELEGT` als deaktiviert |
| `scripts/blacklab/build_blacklab_index.ps1` | lokal oder runtime-root `data/blacklab_export/tsv` und `docmeta.jsonl`; `config/blacklab/corapan-tsv.blf.yaml` | lokal oder runtime-root `data/blacklab_index.new`, optional `data/blacklab_index.backup` | lokaler Builder | `SICHER_BELEGT` im Repo |
| `src/scripts/blacklab_index_creation.py` | standardmaessig repo-relativ `media/transcripts` | repo-relativ `data/blacklab_export/tsv` und `data/blacklab_export/docmeta.jsonl` | Export-/Vorstufe | `SICHER_BELEGT` im Repo |
| `scripts/deploy_sync/sync_data.ps1` | lokal/runtime `data` | synchronisiert `blacklab_export`, aber blockt `blacklab_index` explizit aus | Data-Deploy-Helfer | `SICHER_BELEGT` |
| GitHub Actions Runner via systemd | `/srv/webapps/corapan/runner` und Repo-Checkout | schreibt indirekt `/srv/webapps/corapan/app` und damit `app/config/blacklab` bei Code-Deploys fort | Host-Ops | `SICHER_BELEGT` |
| Cron / systemd BlackLab-spezifisch | kein BlackLab-spezifischer Cron-/systemd-Job belegt | n/a | Host-Ops | `SICHER_BELEGT` negativ |
| externer Wrapper `LOKAL/_2_deploy/publish_blacklab.ps1` | in Repo-Doku referenziert, aber im Workspace nicht vorhanden | unklar, ausserhalb des Workspace | externer Orchestrator | `UNKLAR_OFFEN` |

## 6. Schreib- vs. Lese-Pfade

### Befund 6A - Der Live-Leser ist sicher, der aktuelle Standard-Schreiber ist repo-seitig ebenfalls top-level ausgerichtet

- Beobachtung:
  Der aktive Leser ist top-level `/srv/webapps/corapan/data/blacklab_index`. Im aktuellen Repo setzt `_lib/ssh.ps1` `BlackLabDataRoot` auf `/srv/webapps/corapan/data`, und `publish_blacklab_index.ps1` verwendet diesen Wert standardmaessig fuer den Remote-Publish.
- Bewertung:
  Auf Standard-Repo-Ebene besteht aktuell kein offensichtlicher Default-Drift mehr zwischen Live-Leser und Standard-Publish-Ziel.
- Risiko:
  mittel, weil Standardpfad und tatsaechlicher letzter Schreibvorgang nicht dasselbe sind
- Empfehlung:
  vor jeder spaeteren Migration zusaetzlich read-only verifizieren, ob kein externer Wrapper oder manueller Override weiterhin andere `-DataDir`-Ziele nutzt

### Befund 6B - Es existieren mehrere potenzielle Schreiberklassen

- Beobachtung:
  Es gibt mindestens vier unterschiedliche Schreibkontexte:
  1. lokaler Builder `build_blacklab_index.ps1` schreibt `data/blacklab_index.new`
  2. Exporttool `blacklab_index_creation.py` schreibt `data/blacklab_export/*`
  3. Publisher `publish_blacklab_index.ps1` schreibt und aktiviert remote `blacklab_index.new` und `blacklab_index`
  4. Retention-Skript kann Backup-Verzeichnisse unter Top-Level `data` loeschen
- Bewertung:
  "Der Schreiber" ist kein einzelner Prozess, sondern eine Kette aus lokaler Vorstufe, lokaler Build-Stufe, Remote-Publish und optionaler Backup-Retention.
- Risiko:
  hoch, wenn spaeter nur auf den Live-Leser geschaut wird, ohne diese Schreibkette als Ganzes zu modellieren
- Empfehlung:
  die spaetere Migrationsplanung muss Writer-Kette statt Einzelpfad modellieren: Export -> Build -> Publish -> Retention -> Live-Leser

### Befund 6C - Runtime-Pfade bleiben fuer BlackLab-Export aktiv, nicht aber als Live-Indexleser

- Beobachtung:
  Die Web-App liest `docmeta` explizit aus `runtime/corapan/data/blacklab_export/docmeta.jsonl`. `sync_data.ps1` deployt `blacklab_export`, schliesst `blacklab_index` aber bewusst aus.
- Bewertung:
  Runtime ist fuer BlackLab-nahe Metadaten aktiv, aber nicht der produktive Indexlesepfad des BlackLab-Servers.
- Risiko:
  hoch bei pauschaler Konsolidierung unter der Annahme, alles BlackLab-relevante muesse zwingend in denselben Baum umziehen
- Empfehlung:
  spaetere Migrationsplanung strikt zwischen Suchindex, Export/docmeta und Web-App-Runtime-Verbrauch trennen

### Befund 6D - Der echte letzte Live-Schreibvorgang ist nicht direkt beobachtet worden

- Beobachtung:
  Im Beobachtungsfenster lief kein BlackLab-Publish. Es wurde also kein aktueller realer Schreiblauf auf Hostebene beobachtet.
- Bewertung:
  Die Standard-Schreiberseite ist im Repo klar, der zuletzt tatsaechlich ausgefuehrte Live-Schreibvorgang bleibt aber als historischer Vorgang unbeobachtet.
- Risiko:
  mittel
- Empfehlung:
  in einer spaeteren Migrationsfreigabe nicht nur die Repo-Defaults, sondern auch die effektiv genutzten Orchestratoren ausserhalb des Workspace verifizieren

## 7. Bewertete Zielstruktur unter /data/blacklab

### 7.1 Vorbemerkung

`/data/blacklab` ist derzeit kein existierender Hostpfad. Jede spaetere Struktur unter diesem Ziel waere daher keine blosse Umbenennung, sondern ein neues Host-Level-Zielmodell.

Zusaetzlich ist `/data` bereits ein Containerpfad mit anonymem Docker-Volume. Das kuenftige Hostziel `/data/blacklab` darf deshalb nicht mit dem heutigen Containerpfad `/data` verwechselt werden.

### 7.2 Logisch denkbare Zielstruktur

Falls spaeter ueberhaupt eine Konsolidierung unter einer neuen Hostwurzel beschlossen wird, waere logisch eher eine Datenstruktur dieser Art denkbar:

- `/data/blacklab/index/live`
- `/data/blacklab/index/staging`
- `/data/blacklab/index/backups`
- `/data/blacklab/index/quarantine`
- `/data/blacklab/export/docmeta.jsonl`
- `/data/blacklab/export/tsv/`
- `/data/blacklab/export/tsv_for_index/`

Bewertung:
Das ist nur ein prinzipielles Datenmodell. Es ist keine unmittelbar umsetzbare Zielentscheidung.

### 7.3 Welche heutigen Pfade darin prinzipiell aufgehen koennten

Potenziell aufgehend, aber nur nach spaeterer Freigabe:

- `/srv/webapps/corapan/data/blacklab_index`
- `/srv/webapps/corapan/data/blacklab_index.bak_*`
- `/srv/webapps/corapan/data/blacklab_index.bad_*`
- `/srv/webapps/corapan/data/blacklab_export`
- `/srv/webapps/corapan/data/tsv`
- `/srv/webapps/corapan/data/tsv_for_index`
- eventuell entsprechende runtime-Duplikate, aber nur nach sauberer Verbraucher-Abschaltung

Nicht automatisch unter `/data/blacklab` aufgehoben:

- `/srv/webapps/corapan/app/config/blacklab`
  - das ist heute repo-/deploy-gemanagte Konfiguration, kein reiner Datenbaum
- die BlackLab-HTTP-Nutzung der Web-App ueber `BLS_BASE_URL`
  - das ist Integrationskonfiguration, kein Dateipfad
- das anonyme Docker-Volume auf Containerpfad `/data`
  - das ist Container-Lifecycle, kein Host-Zieldirectory

### Befund 7A - Eine Zielstruktur unter /data/blacklab waere eine echte Umverdrahtung, keine kosmetische Bereinigung

- Beobachtung:
  Der Hostpfad `/data` existiert heute nicht. Gleichzeitig ist `/data` im Container bereits intern belegt.
- Bewertung:
  Eine Migration nach `/data/blacklab` waere kein "Pfad aufraeumen", sondern eine neue Hostwurzel plus neue Mount- und Ownership-Entscheidung.
- Risiko:
  sehr hoch
- Empfehlung:
  erst ein Architekturziel schriftlich festlegen, bevor ueber irgendeinen physischen Move gesprochen wird

### Befund 7B - Nicht alle BlackLab-relevanten Pfade gehoeren logisch in dieselbe Zielwurzel

- Beobachtung:
  Suchindex, Export/docmeta, App-Konfiguration und containerinterne `/data`-Zusatzpfade haben unterschiedliche Rollen.
- Bewertung:
  Eine saubere Zielstruktur muss zwischen Daten, Konfiguration und Container-internem State unterscheiden.
- Risiko:
  hoch
- Empfehlung:
  ein spaeteres Zielbild mit getrennten Klassen modellieren: `data`, `config`, `container-internal`

## 8. Migrationsrisiken

### Befund 8A - Live-Leser-Unterbrechung

- Beobachtung:
  BlackLab scannt laufend `/data/index` und verwendet `/data/index/corapan` aktiv.
- Bewertung:
  Jeder falsche Schritt am Hostpfad `/srv/webapps/corapan/data/blacklab_index` oder an seinem Mount kann Suchverfuegbarkeit sofort unterbrechen.
- Risiko:
  sehr hoch
- Empfehlung:
  keine Leser-Migration ohne vorherigen Nachweis, dass Schreiberkette, Staging, Validierung und Rollback funktionieren

### Befund 8B - Falscher Schreiber bleibt alt oder extern

- Beobachtung:
  Das Repo zeigt heute auf Top-Level `data`, aber ein externer Wrapper ausserhalb des Workspace ist in der Doku referenziert und nicht live verifiziert.
- Bewertung:
  Eine Migration kann formal sauber vorbereitet sein und trotzdem scheitern, wenn ein externer oder manueller Publisher weiter den alten Pfad benutzt.
- Risiko:
  hoch
- Empfehlung:
  vor Freigabe alle effektiven Publish-Einstiegspunkte einschliesslich externer Workstations und Operator-Routinen inventarisieren

### Befund 8C - Stille Duplikate und Drift

- Beobachtung:
  Top-Level und Runtime enthalten aktuell identische Index- und docmeta-Staende, dazu Backup-, Bad- und Leftover-Pfade.
- Bewertung:
  Gerade weil sie heute identisch sind, ist die Verwechslungsgefahr gross. Ein spaeterer Drift kann dann unbemerkt auf dem falschen Baum entstehen.
- Risiko:
  hoch
- Empfehlung:
  vor jeder spaeteren Konsolidierung eine kanonische Quelle pro Datenklasse benennen und alle Nebenziele explizit als `legacy`, `backup` oder `quarantine` klassifizieren

### Befund 8D - Backup-/Restore-Verwechslungen

- Beobachtung:
  Es existieren `blacklab_index.bak_*`, `blacklab_index.bad_*` und `blacklab_index.new.leftover_*` in mehreren Baeumen.
- Bewertung:
  Die Restore-Logik ist ohne saubere Namens- und Pfadgovernance leicht fehlleitbar.
- Risiko:
  hoch
- Empfehlung:
  vor einer spaeteren Welle eine eindeutige Semantik fuer `live`, `staging`, `backup`, `bad/quarantine` definieren

### Befund 8E - Inkonsistente Repo-Doku und historische Restreferenzen

- Beobachtung:
  Der aktuelle Repo-Default fuer Publish ist top-level, aber aeltere State-Dokumente und historische Legacy-Doku referenzieren noch das fruehere runtime-Ziel.
- Bewertung:
  Dokumentation allein ist hier nicht vertrauenswuerdig genug, wenn sie nicht nach Stichtag und Geltungsbereich gelesen wird.
- Risiko:
  mittel
- Empfehlung:
  spaeter eine kanonische BlackLab-Betriebsdoku bestimmen und historische Wellen klar als zeitgebundene Befunde markieren

### Befund 8F - Disk-Space-Risiko fuer Copy-then-switch

- Beobachtung:
  Frei sind auf `/srv` nur rund `6.3G`. Bereits heute belegen allein die gemessenen BlackLab-nahen Baeume mindestens grob:
  - aktive und duplizierte `blacklab_export`: `3.0G`
  - duplizierte `tsv`: `1.46G`
  - duplizierte `tsv_for_index`: `730M`
  - duplizierte aktive Indizes: `558M`
  - dazu weitere Backup-/Bad-Pfade ausserhalb dieser Minimalrechnung
- Bewertung:
  Ein klassisches `copy-then-switch` waere unter aktueller Kapazitaet nur mit sehr wenig Puffer moeglich und kann schnell an Platzgrenzen scheitern.
- Risiko:
  sehr hoch
- Empfehlung:
  keine Migrationswelle vor separater Kapazitaets- oder Cleanup-Welle planen

### Befund 8G - Compose-/Ownership-/Netz-Nebeneffekte

- Beobachtung:
  BlackLab ist nicht Teil des Compose-V2-Stacks `infra`, haengt an zwei Netzen und benutzt ein anonymes Docker-Volume.
- Bewertung:
  Eine Pfadmigration laesst sich nicht sauber isolieren, wenn Container-Lifecycle, Netzwerkzuordnung und Mount-Ownership nicht mitgedacht werden.
- Risiko:
  hoch
- Empfehlung:
  eine spaetere Welle muss BlackLab als eigene Infrastruktur-Komponente behandeln, nicht als blossen Datenordner

### Befund 8H - Rollback-Komplexitaet

- Beobachtung:
  Rollback muesste im Ernstfall nicht nur Dateien, sondern Leserpfad, Mountmodell, Backup-Namensschema und moegliche externe Publisher beruecksichtigen.
- Bewertung:
  Ohne vorher definierte Rollback-Mechanik ist jede Konsolidierung riskant.
- Risiko:
  hoch
- Empfehlung:
  Rollback-Szenario vor einer Freigabe als eigenen Schritt planen und nicht erst waehrend der Migrationswelle erfinden

## 9. Voraussetzungen vor einer spaeteren Migrationswelle

### Befund 9A - Vollstaendige Verbraucher-Matrix ist noch nicht absolut abgeschlossen

- Beobachtung:
  Die internen Repo- und Live-Verbraucher sind weitgehend belegt. Offen bleibt, ob ausserhalb des Workspace weitere reale Publish-Wrapper oder manuelle Operator-Routinen aktiv sind.
- Bewertung:
  Die Matrix ist fuer Voranalyse belastbar, aber fuer Freigabe einer Migrationswelle noch nicht vollstaendig genug.
- Risiko:
  hoch
- Empfehlung:
  vor einer echten Migrationsfreigabe die externen Publish-Einstiege und Operator-Routinen explizit bestaetigen oder ausschliessen

### Befund 9B - Zielmodell und Rollengrenzen muessen vorab entschieden werden

- Beobachtung:
  Unklar ist noch, ob `/data/blacklab` nur Daten aufnehmen soll oder ob spaeter auch Config-/Container-Aspekte miterfasst werden sollen.
- Bewertung:
  Ohne klares Zielmodell werden spaeter Daten-, Config- und Containerfragen vermischt.
- Risiko:
  hoch
- Empfehlung:
  zuerst ein Architekturblatt fuer die Zielklassen erstellen: `index`, `staging`, `backup`, `quarantine`, `export`, `config`, `container-internal`

### Befund 9C - Kapazitaet muss vorgezogen werden

- Beobachtung:
  Der freie Speicher ist fuer eine vorsichtige Copy-/Switch-/Rollback-Strategie knapp.
- Bewertung:
  Die Kapazitaet ist nicht nur ein Nebenaspekt, sondern eine harte Freigabebedingung.
- Risiko:
  sehr hoch
- Empfehlung:
  vor jeder Konsolidierungswelle zuerst eine Kapazitaets-/Cleanup-Welle planen und durchfuehren

### Befund 9D - BlackLab-Lifecycle und Netzmodell muessen vorab geklaert werden

- Beobachtung:
  BlackLab wird aktuell ausserhalb von `infra` betrieben, mit dualer Netzzuordnung und eigenem Startskript.
- Bewertung:
  Eine reine Pfadmigration ohne Lifecycle-Entscheidung waere operativ unsauber.
- Risiko:
  hoch
- Empfehlung:
  vorab festlegen, ob BlackLab separat bleibt oder spaeter bewusst in ein kanonisches Betriebsmodell ueberfuehrt wird

## 10. Empfohlene naechste Schritte

### Befund 10A - Naechster Schritt ist keine Migration, sondern Freigabevorbereitung

- Beobachtung:
  Die heutige Analyse zeigt genug Risiko und genug offene Flanken, um eine sofortige Konsolidierungsplanung als operative Welle noch nicht freizugeben.
- Bewertung:
  Ein weiterer read-only Vorlauf ist sinnvoller als verfruehter Aktionismus.
- Risiko:
  niedrig fuer weiteres Analysevorgehen, hoch fuer vorschnelle Umsetzung
- Empfehlung:
  als naechstes eine Vorbereitungswelle mit vier Arbeitspaketen ansetzen:

1. externe Publish-/Ops-Einstiegspunkte abschliessen
2. Kapazitaets- und Cleanup-Optionen fuer BlackLab-nahe Duplikate bewerten
3. Zielmodell `/data/blacklab` architektonisch scharfziehen
4. Rollback- und Reihenfolgemodell fuer eine spaetere Migrationswelle entwerfen

### Befund 10B - Vor jeder spaeteren Konsolidierung gilt eine sichere Grundreihenfolge

- Beobachtung:
  Die Risiken liegen nicht nur im Zielpfad, sondern in Reihenfolge und Abhaengigkeiten.
- Bewertung:
  Eine spaetere sichere Reihenfolge waere prinzipiell eher:
  1. externe Writer verifizieren
  2. Kapazitaet schaffen
  3. Zielarchitektur und Rollback festziehen
  4. erst dann ueber Staging-/Reader-/Mount-Umzug sprechen
- Risiko:
  hoch bei Reihenfolgefehlern
- Empfehlung:
  keine eigentliche Migrationswelle freigeben, bevor diese Reihenfolge dokumentiert und abgenommen ist

## 11. Belege / Kommandos / Outputs

Wesentliche read-only Belege dieser Analyse:

- `docker inspect corapan-blacklab --format '{{json .Mounts}}'`
  - bind mount `/srv/webapps/corapan/data/blacklab_index -> /data/index/corapan`
  - bind mount `/srv/webapps/corapan/app/config/blacklab -> /etc/blacklab`
  - anonymes Docker-Volume auf `/data`
- `docker logs corapan-blacklab`
  - `Scanning collectionsDir: /data/index`
  - `Index found: corapan (/data/index/corapan)`
- `docker exec corapan-blacklab sh -lc 'ls -ld /data /data/index /data/index/corapan /etc/blacklab'`
  - bestaetigt die Container-Sicht und das interne `/data`-Layout
- Hostinventur mit `stat`, `du`, `find`, `sha256sum`
  - `/data` und `/data/blacklab` fehlen auf dem Host
  - aktive und parallele BlackLab-Baeume unter Top-Level und Runtime existieren
  - `blacklab_index` und `docmeta` sind derzeit top-level und runtime inhaltlich identisch
- Repo-Analyse der Primarquellen:
  - `infra/docker-compose.prod.yml`
  - `src/app/config/__init__.py`
  - `src/app/runtime_paths.py`
  - `scripts/deploy_sync/_lib/ssh.ps1`
  - `scripts/deploy_sync/publish_blacklab_index.ps1`
  - `scripts/deploy_sync/sync_data.ps1`
  - `scripts/blacklab/run_bls_prod.sh`
  - `scripts/blacklab/retain_blacklab_backups_prod.sh`
  - `scripts/blacklab/build_blacklab_index_prod.sh`
  - `scripts/blacklab/build_blacklab_index.ps1`
  - `src/scripts/blacklab_index_creation.py`
- Host-Ops-Suche in `/etc/systemd/system`, `/lib/systemd/system`, `/etc/cron*`, `/var/spool/cron`
  - belegt wurde der GitHub Actions Runner fuer CORAPAN
  - kein BlackLab-spezifischer Cron- oder systemd-Job wurde gefunden
- `df -h / /srv /var/lib/docker`
  - freie Kapazitaet ca. `6.3G`

## 12. Executive Summary

Die produktive BlackLab-Realitaet ist aktuell klarer als das Gesamtbild der Pfade: Der Live-Leser ist eindeutig `/srv/webapps/corapan/data/blacklab_index`, die Konfiguration liegt eindeutig unter `/srv/webapps/corapan/app/config/blacklab`, und der Server benutzt im Container `/data/index` als Sammlungswurzel. Gleichzeitig existieren mehrere parallele BlackLab-nahe Datenbaeume unter Top-Level und Runtime, inklusive aktiver Duplikate, Backups, Bad-Pfade und Leftovers.

Repo-seitig zeigt der aktuelle Standard-Publish-Unterbau heute wieder auf den Top-Level-Datenbaum und nicht mehr auf runtime. Damit ist der fruehere Default-Drift zwischen Standard-Writer und Live-Leser auf Repo-Ebene nicht mehr der Hauptkonflikt. Nicht geklaert ist aber abschliessend, ob ausserhalb des Workspace weitere reale Publish-Wrapper oder manuelle Operator-Routinen aktiv sind.

Eine spaetere Zielstruktur unter `/data/blacklab` ist grundsaetzlich vorstellbar, aber sie waere keine harmlose Bereinigung. Der Hostpfad `/data` existiert heute nicht, waehrend `/data` im Container bereits ein eigenes Volume plus bind-mount-Ueberlagerung darstellt. Dazu kommt knapper freier Speicher: eine klassische Copy-then-switch-Migration ist unter den aktuellen Platzverhaeltnissen kaum verantwortbar.

Fazit: Die heutige Voranalyse ist belastbar genug, um eine spaetere Migrationswelle vorzubereiten. Sie ist nicht belastbar genug, um diese Welle schon freizugeben. Vor einer eigentlichen Konsolidierung sind mindestens noch eine Kapazitaets-/Cleanup-Welle, die Absicherung aller echten Writer-Einstiege und ein schriftlich fixiertes Zielmodell erforderlich.