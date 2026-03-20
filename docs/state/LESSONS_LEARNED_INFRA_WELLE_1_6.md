# Lessons Learned Infra Welle 1-6

Datum: 2026-03-20
Umgebung: konsolidierte read-only Auswertung aus den bisherigen Infra-, Deploy- und Pfadwellen
Scope: normalisierte Lessons Learned aus Welle 1-6 fuer Architektur, Deploy, Docker/Compose, Datenpersistenz, Filesystem-Design sowie Risiko- und Safety-Prinzipien

## 1. Architektur

### Lesson A1 - Single Source of Truth fuer operative Pfade ist Pflicht

- Problem:
  App-Module, Skripte und Routen hielten konkurrierende Pfadableitungen fuer Metadata, Statistics, docmeta, Logs und Media-Unterpfade.
- Ursache:
  Pfade wurden teils lokal im Modul, teils indirekt aus Config-Werten und teils ueber implizite Strukturannahmen zusammengesetzt.
- Konsequenz:
  Gleichartige Funktionen konnten in Dev und Prod unterschiedliche Dateibaeume benutzen, obwohl sie logisch dieselbe Ressource meinten.
- Regel:
  Jeder operative Datenpfad muss ueber einen zentralen Resolver oder einen expliziten kanonischen Infrastruktur-Helper laufen. Implizite lokale Ableitungen sind zu entfernen oder als Legacy offenzulegen.

### Lesson A2 - Spezialrealitaeten duerfen nicht in allgemeine Defaults eingemischt werden

- Problem:
  BlackLab folgte produktiv einem anderen Pfadmodell als data/media-Deploys, wurde aber ueber denselben allgemeinen Remote-Pfadhelper mitgezogen.
- Ursache:
  Ein Spezialfall wurde an einen allgemeinen Default angehaengt, statt als eigene produktive Wahrheit modelliert zu werden.
- Konsequenz:
  Der Standard-Writer von BlackLab lief auf einen anderen Pfad als der Live-Reader.
- Regel:
  Wenn ein Spezial-Deploy bewusst nicht demselben Zielmodell folgt wie andere Deploys, braucht er einen eigenen expliziten Default. Gemeinsame Helper duerfen Spezialziele nicht still mitschleifen.

### Lesson A3 - Produktionsrealitaet schlaegt Repo-Annahme

- Problem:
  Aus Repo-Struktur, Compose-Datei und Doku allein liess sich kein eindeutiges produktives Strukturmodell ableiten.
- Ursache:
  Web-App, Secrets und BlackLab nutzten gleichzeitig unterschiedliche aktive Pfadmodelle.
- Konsequenz:
  Eine falsche Vereinheitlichung haette aktive Reader, Writer oder Secrets-Pfade brechen koennen.
- Regel:
  Architekturentscheidungen fuer PROD duerfen nie auf Repo-Annahmen allein beruhen. Live-Mounts, ENV-Werte, Container und echte Dateibaeume sind die bindende Quelle.

## 2. Deploy / CI/CD

### Lesson D1 - Deterministische Deploys brauchen den realen Ausfuehrungsort als Ausgangspunkt

- Problem:
  Der Fehler `KeyError: 'ContainerConfig'` konnte zunaechst als allgemeiner Workflow- oder Runner-Fehler fehlklassifiziert werden.
- Ursache:
  Der reale Deploy lief lokal auf dem Zielserver ueber den self-hosted Runner und nicht als fern ausgefuehrte GitHub-Operation.
- Konsequenz:
  Die falsche Toolchain auf dem Zielhost blieb zu lange unsichtbar.
- Regel:
  Bei jedem Deploy-Fehler muss zuerst der reale Ausfuehrungsort bestimmt werden: Runner-Host, Ziel-Checkout, verwendetes Skript, Compose-Kommando und Versionskontext.

### Lesson D2 - Self-updating Deploy-Skripte sind nicht self-applying

- Problem:
  Eine bereits implementierte Compose-Guard-Logik griff im ersten betroffenen Deploy-Lauf nicht.
- Ursache:
  Das Deploy startete zuerst die alte on-disk-Version von `scripts/deploy_prod.sh` und aktualisierte den Checkout erst innerhalb dieses Skripts.
- Konsequenz:
  Ein Fix im Deploy-Skript selbst konnte im ersten Lauf weiter durch die alte Version blockiert werden.
- Regel:
  Wenn ein Workflow ein Skript aus einem persistenten Server-Checkout startet und dieses Skript sich selbst per Git aktualisiert, muss der Checkout vor dem Skriptstart auf den Trigger-Commit gesetzt werden.

### Lesson D3 - Tool-Auswahl im Deploy muss explizit und hart validiert werden

- Problem:
  Ein moderner Docker-Stand lief mit Compose v1 weiter und scheiterte spaet mit einem undurchsichtigen Fehler.
- Ursache:
  Der Deploy-Pfad nutzte historisch `docker-compose`, ohne moderne Kompatibilitaet serverseitig abzusichern.
- Konsequenz:
  Ein CLI-Kompatibilitaetsproblem wurde erst mitten im Deploy sichtbar.
- Regel:
  Deploy-Skripte muessen das effektive Tool explizit aufloesen, Versionen sichtbar loggen und inkompatible Altpfade hart blockieren, statt still weiterzufallen.

### Lesson D4 - Deploy-Orchestratoren sind Teil der produktiven Wahrheit

- Problem:
  Doppelpfade wirkten zunaechst wie blosse Dateibaum-Altlasten.
- Ursache:
  Deploy-Sync, Runner-Workflow und Unterbau-Skripte wurden nicht von Anfang an als aktive Writer mitmodelliert.
- Konsequenz:
  Ein Pfad konnte live aktiv sein, obwohl kein Container ihn direkt las, weil der Standard-Deploy weiterhin dorthin schrieb.
- Regel:
  Workflows, Runner, Sync-Skripte und Publish-Helfer muessen in jeder produktiven Pfadanalyse als vollwertige Reader/Writer erfasst werden.

## 3. Docker / Compose

### Lesson C1 - Compose V1 und moderner Docker sind kein sicherer Produktionspfad

- Problem:
  `docker-compose 1.29.2` lief neben modernem Docker weiter und fuehrte zu `KeyError: 'ContainerConfig'`.
- Ursache:
  Die Produktionsumgebung hatte modernisierten Docker, aber keinen gleichwertig modernisierten Compose-Pfad.
- Konsequenz:
  Der Deploy konnte an einer veralteten CLI scheitern, obwohl die Stack-Definition selbst plausibel war.
- Regel:
  Moderne Docker-Hosts brauchen einen explizit validierten Compose-V2-Pfad. Compose v1 darf in produktiven Deploys nicht still toleriert werden.

### Lesson C2 - Bei Compose-V2-Konflikten muessen Realname, Projektname und logische Compose-ID getrennt geprueft werden

- Problem:
  Compose V2 lehnte ein bereits aktiv genutztes Netzwerk ab.
- Ursache:
  Realer Netzwerkname und Projektname passten bereits, der logische Compose-Netzwerk-Key im Repo aber nicht zum gespeicherten Legacy-Label des bestehenden Netzes.
- Konsequenz:
  Ein scheinbar korrektes Produktionsnetzwerk wurde von Compose V2 als inkonsistent bewertet.
- Regel:
  Bei Compose-Ressourcenkonflikten sind drei Ebenen getrennt zu prüfen: realer Ressourcenname, Compose-Projektlabel und logische Compose-ID. Ein passender Realname allein ist kein Ownership-Beweis.

### Lesson C3 - Repo-Fix vor Server-Fix bei aktiven Compose-Ressourcen

- Problem:
  Ein aktives Produktionsnetzwerk stand im Konflikt zur aktuellen Compose-V2-Sicht.
- Ursache:
  Die Inkonsistenz lag in der Repo-Metadaten-ID und nicht im realen Produktionsnetzwerk.
- Konsequenz:
  Ein vorschneller Server-Fix haette laufende Container an einem aktiven Netz gefaehrdet.
- Regel:
  Wenn aktive Compose-Ressourcen nur an logischen Metadaten abweichen, ist zuerst die Repo-seitige Schluesselangleichung zu waehlen. Server-Bereinigung ist nur Reservepfad.

### Lesson C4 - Legacy-Compose-Artefakte koennen Ownership-Konflikte auch im gestoppten Zustand ausloesen

- Problem:
  Ein alter V1-DB-Container blieb als gestopptes Artefakt vorhanden, waehrend Compose V2 denselben Service neu erwarten konnte.
- Ursache:
  Historische V1-Ressourcen blieben mit Compose-Labels und altem Namensschema auf dem Host liegen.
- Konsequenz:
  Selbst ohne laufenden Konflikt kann ein stale Container kuenftige Ownership- oder Recreate-Probleme ausloesen.
- Regel:
  Vor Compose-V2-Deploys muessen stale V1-Container, Netzwerke und andere label-tragende Artefakte forensisch geprueft und isoliert bewertet werden.

## 4. Datenpersistenz und Volumes

### Lesson V1 - Volumes sind die schutzwuerdigste Persistenzgrenze

- Problem:
  Ein DB-Konflikt konnte leicht als Containerproblem behandelt werden, obwohl die eigentliche Datenpersistenz im Volume lag.
- Ursache:
  Container und Volume wurden nicht sauber getrennt betrachtet.
- Konsequenz:
  Ein unvorsichtiger Cleanup haette das Risiko einer Datenbeschaedigung oder eines Datenverlusts getragen, obwohl nur ein stale Container stoerte.
- Regel:
  Bei Datenbankkonflikten muessen Container, Volume und Service-Definition getrennt forensisch bewertet werden. Volumes sind tabu, solange nicht zweifelsfrei belegt ist, dass nur ein Containerartefakt stoert.

### Lesson V2 - Persistente Datenpfade brauchen Schutzregeln im Deploy-Unterbau

- Problem:
  Produktive Teilpfade wie `data/db`, `stats_temp`, `blacklab_index` und Auth-Daten sind schreibsensibel, waehrend andere Datenverzeichnisse regulär synchronisiert werden.
- Ursache:
  Nicht alle Daten unter einem gemeinsamen Root haben dieselbe Kritikalitaet oder denselben Writer.
- Konsequenz:
  Ein zu grober Sync oder Cleanup koennte hochkritische Persistenzbereiche ueberschreiben.
- Regel:
  Deploy-Unterbau braucht explizite Hard-Blocks, Allow-Lists und Schutzpfade fuer persistente Kernbereiche. Ein gemeinsamer Datenroot ist kein Freibrief fuer gleichfoermige Behandlung.

## 5. Pfad- und Filesystem-Design

### Lesson F1 - runtime und top-level sind keine Alias-Pfade

- Problem:
  runtime- und top-level-Baeume koennen aehnlich aussehen oder identische Inhalte tragen, obwohl sie inode-getrennte Realitaeten sind.
- Ursache:
  Parallelstrukturen entstanden schrittweise fuer verschiedene Verbraucher, ohne spaetere Abschaltung der Altpfade.
- Konsequenz:
  Verwechslungen bleiben lange unentdeckt und spaetere Bereinigung wird hochriskant.
- Regel:
  Unterschiedliche Wurzeln duerfen nie als funktionale Alias-Struktur behandelt werden, solange ihre Reader, Writer und Deploy-Ziele nicht vollstaendig belegt sind.

### Lesson F2 - Live-Leser und Default-Schreiber muessen auf denselben operativen Pfad zeigen

- Problem:
  BlackLab las top-level, waehrend der Standard-Publish auf runtime schrieb.
- Ursache:
  Writer-Defaults wurden aus einem allgemeinen runtime-first Modell abgeleitet, das fuer BlackLab nicht galt.
- Konsequenz:
  Der Standard-Deploy konnte still an einer produktiv irrelevanten Kopie arbeiten.
- Regel:
  Ein Live-Leser darf nicht stillschweigend durch einen neuen Deploy-Default ersetzt werden. Reader- und Default-Writer-Pfad muessen fuer dieselbe Ressource kongruent sein.

### Lesson F3 - Legacy darf nicht versteckt, sondern muss explizit klassifiziert werden

- Problem:
  Repo-lokale oder top-level Altpfade blieben in Betrieb oder als Restrealitaet erhalten.
- Ursache:
  Nicht jede Legacy-Nutzung konnte im selben Run vereinheitlicht werden.
- Konsequenz:
  Ungenannte Legacy erzeugt Drift; explizit klassifizierte Legacy bleibt steuerbar.
- Regel:
  Nicht entfernbarer Legacy-Pfad ist als `ACTIVE_LEGACY`, `DUPLICATED`, `UNUSED` oder gleichwertig explizit zu markieren. Verdeckte Legacy ist verboten.

### Lesson F4 - Alte Prozesse und Caches koennen Path-Fixes verdecken

- Problem:
  In Dev konnten alte Serverprozesse und Route-Caches neue Path-Fixes unsichtbar machen.
- Ursache:
  Verifikation lief gegen nicht eindeutig frische Prozesse.
- Konsequenz:
  Korrekte Fixes konnten wie Fehlfixes wirken oder umgekehrt.
- Regel:
  Pfad- und Resolver-Verifikation muss gegen einen frischen Prozess oder einen isolierten Port erfolgen, wenn alte Caches oder Altinstanzen noch im Umlauf sein koennen.

## 6. Risiko- und Safety-Prinzipien

### Lesson R1 - Erster sicherer Eingriff korrigiert meist die Schreiberseite, nicht die Leserseite

- Problem:
  Bei parallelen Dateibaeumen ist unklar, welcher Reader oder Writer wo noch aktiv ist.
- Ursache:
  Legacy-Drift fuehrt oft dazu, dass der Live-Leser stabil laeuft, waehrend der Standard-Writer bereits falsch zeigt.
- Konsequenz:
  Ein vorschneller Leser-Umbau trifft sofort den laufenden Betrieb.
- Regel:
  Bei parallelen produktiven Dateibaeumen ist der sicherste erste Eingriff fast immer die Korrektur des Schreibpfads, nicht die Migration des Lesepfads.

### Lesson R2 - Keine Bereinigung ohne Verbraucher-Matrix

- Problem:
  Doppelte Baeume wie `logs`, `blacklab_export` und `blacklab_index` wirken wie offensichtliche Cleanup-Kandidaten.
- Ursache:
  Externe Operator-Routinen, Runner, Skripte oder manuelle Prozesse koennen weiter daran haengen, ohne im App-Code sichtbar zu sein.
- Konsequenz:
  Ein vermeintlicher Cleanup kann produktive Diagnose-, Publish- oder Wiederherstellungswege zerstoeren.
- Regel:
  Kein Pfad darf entfernt, umgehaengt oder vereinheitlicht werden, bevor alle Leser, Schreiber und Deploy-Ziele explizit belegt oder ausgeschlossen sind.

### Lesson R3 - Produktive Sonderzonen muessen explizit tabu sein

- Problem:
  Secrets, PostgreSQL/Auth, Analytics und BlackLab-Live-Pfade haben andere Risikoprofile als allgemeine App-Dateien.
- Ursache:
  Diese Bereiche verbinden Betriebszustand, Persistenz, Authentifizierung und externe Systeme.
- Konsequenz:
  Ein allgemeiner Vereinheitlichungs- oder Cleanup-Run kann dort unverhaeltnismaessig hohen Schaden erzeugen.
- Regel:
  `passwords.env`, Datenbank-Volumes, aktive BlackLab-Leserpfade und produktive Analytics-/Stats-Kernpfade muessen in Migrations- und Cleanup-Wellen als eigene Tabuzonen gefuehrt werden.

### Lesson R4 - Begrenzter Disk Space ist kein Randthema, sondern Migrationsbedingung

- Problem:
  Der Host lief waehrend der Infra-Forensik nur mit begrenztem freiem Speicher.
- Ursache:
  Images, Build-Cache und produktive Datenbaeume teilen denselben begrenzten Plattenraum.
- Konsequenz:
  Rebuild-, Recreate- oder Publish-Runs koennen an Speicherknappheit scheitern oder unvollstaendige Zwischenzustaende erzeugen.
- Regel:
  Freier Speicherplatz ist vor jedem produktiven Rebuild-, Publish- oder Recreate-Run als harte Nebenbedingung zu prüfen und zu dokumentieren.

## 7. Anti-Patterns

- Blind `docker rm` auf DB-Container ausfuehren, ohne zuerst Laufstatus, Labels, Mounts und Volumes zu trennen.
- Compose-v1 still weiterverwenden, nur weil der Befehl auf dem Host vorhanden ist.
- Repo-Pfade und Live-Pfade als identisch annehmen, ohne Container-Mounts zu belegen.
- runtime- und top-level-Baeume als harmlose Duplikate behandeln, nur weil Inhalte gleich aussehen.
- Live-Leserpfade migrieren, bevor der Standard-Writer korrigiert ist.
- `external: true` oder Netzwerk-Neuanlage als ersten Fix fuer aktive Compose-Netzwerke verwenden, wenn die Inkonsistenz im Repo-Schluessel liegt.
- Ein Deploy-Skript so aendern, dass es sich selbst erst waehrend des Laufs aktualisiert.
- Alte Prozesse oder Altinstanzen bei Verifikation ignorieren.
- BlackLab wie einen normalen data/media-Deploy behandeln.
- Legacy-Pfade verdeckt weiterlaufen lassen statt sie explizit zu klassifizieren.
- Secrets-, Volume- oder Auth-Pfade in allgemeine Cleanup- oder Vereinheitlichungsruns einmischen.

## 8. Guard-Rules fuer kuenftige Agentenlaeufe

- Verifiziere bei Deploy-Problemen zuerst den realen Ausfuehrungsort, die konkrete Skriptversion und das effektive CLI auf dem Zielhost.
- Blockiere Compose v1 in produktiven Deploy-Pfaden hart, wenn Docker modern ist und Compose V2 erwartet wird.
- Aktualisiere einen persistenten Ziel-Checkout vor dem Start eines Deploy-Skripts auf den Trigger-Commit, wenn das Skript sich sonst selbst erst spaet aktualisiert.
- Trenne bei Compose-Ressourcenkonflikten immer Realname, Projektlabel und logische Compose-ID.
- Entferne oder bereinige keine produktive Ressource, solange nicht belegt ist, dass sie weder aktiver Reader noch aktiver Writer noch Deploy-Ziel ist.
- Behandle Volumes, `passwords.env`, aktive BlackLab-Leserpfade und Auth-Daten als Hochrisiko-Zonen mit gesonderter Pruefpflicht.
- Wenn ein Spezial-Deploy vom allgemeinen Zielmodell abweicht, gib ihm einen eigenen expliziten Pfaddefault statt Wiederverwendung eines allgemeinen Helpers.
- Verifiziere Pfadfixes gegen frische Prozesse oder isolierte Ports, wenn Altinstanzen oder Caches Ergebnisse verdecken koennen.
- Dokumentiere verbleibende Legacy immer explizit als aktive, duplizierte, ungenutzte oder blockierte Realitaet.
- Fuehre erste Produktiveingriffe minimal-invasiv aus: erst Schreiberseite korrigieren, dann Restverbraucher inventarisieren, erst zuletzt Leser- oder Strukturmigration.
- Pruefe freien Speicherplatz vor jedem produktiven Rebuild-, Recreate- oder Publish-Run als harte Go/No-Go-Bedingung.

## 9. Priorisierte Infra-Regeln

1. Deterministische Deploys gehen vor bequemen Deploys.
2. Single Source of Truth geht vor lokaler Bequemlichkeitslogik.
3. Live-Realitaet geht vor Repo-Annahme.
4. Schreiberkorrektur geht vor Leser-Migration.
5. Volumeschutz geht vor Container-Cleanup.
6. Explizite Legacy-Klassifikation geht vor stiller Drift.
7. Repo-Fix geht vor Server-Fix, wenn der Konflikt in Metadaten statt in Live-Ressourcen liegt.

## 10. Weiterfuehrende Dokumente

- [docs/architecture/infra-lessons.md](../architecture/infra-lessons.md) kondensiert die Lessons in Architektur- und Systemdesign-Prinzipien.
- [docs/architecture/infra-guardrails.md](../architecture/infra-guardrails.md) uebersetzt die Lessons in operative Guardrails und explizite Anti-Patterns.
- [docs/architecture/agent-rules.md](../architecture/agent-rules.md) leitet Safety- und Stop-Regeln fuer kuenftige Agentenlaeufe ab.
- [docs/state/Welle_7_lessons_integration_summary.md](Welle_7_lessons_integration_summary.md) dokumentiert diese Integrationswelle und den Uebergang von Forensik zu dauerhaften Regeln.
