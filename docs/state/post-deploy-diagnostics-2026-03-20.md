# Post-Deploy Diagnostics 2026-03-20

Datum: 2026-03-20
Umgebung: Production-nahe Live-Diagnose nach erfolgreichem Deploy und gruener funktionaler Smoke-Pruefung
Scope: read-only technische Nachpruefung von Containerzustand, Compose-Orchestrierung, Persistenz, Runtime-Konfiguration, BlackLab-Anbindung, Logs und verbleibenden Altlasten

## 1. Anlass / Scope

Nach dem erfolgreichen Produktionsdeploy und bestandenen funktionalen Smoke-Tests wurde eine konservative technische Nachdiagnose auf dem Live-System durchgefuehrt. Ziel war nicht die erneute funktionale Fachpruefung, sondern die Frage, ob der aktuelle Zustand auch infrastrukturell sauber, konsistent und fuer den naechsten Betriebszeitraum belastbar ist.

Geprueft wurden ausschliesslich read-only:

- laufende Container, Health und Restart-Zustaende
- Compose-Projektlage und Compose-Metadaten
- Netzwerke und Volumes inklusive Labelzustand
- Mounts und Runtime-ENV der CORAPAN-Web-App
- DB-Plausibilitaet auf Schema- und Betriebsniveau
- BlackLab-Live-Anbindung
- aktuelle und historische relevante Logsignale im Kontext des Deploy-Fensters

## 2. Gepruefte Systembereiche

### 2.1 Container- und Compose-Zustand

Geprueft wurden:

- `corapan-web-prod`
- `corapan-db-prod`
- `corapan-blacklab`
- `docker compose ls`
- Docker-Netzwerke und Docker-Volumes der CORAPAN-Instanz

### 2.2 Persistenz und DB-Plausibilitaet

Geprueft wurden:

- Volume `corapan_postgres_prod`
- DB-Container-ENV
- read-only SQL-Abfragen auf Tabellenbestand und Alembic-Plausibilitaet
- DB-Logs im Start- und Post-Deploy-Fenster

### 2.3 Runtime-Konfiguration und Integrationen

Geprueft wurden:

- Runtime-Mounts der Web-App
- produktive ENV der Web-App in redigierter Form
- BLS/BlackLab-Zielwerte
- Runtime-Logs der Web-App
- BlackLab-Container-Logs

## 3. Ist-Zustand

### 3.1 Web und DB sind aktuell gesund

- `corapan-web-prod` laeuft im Compose-Projekt `infra`, ist `healthy` und hat `RestartCount=0`.
- `corapan-db-prod` laeuft im Compose-Projekt `infra`, ist `healthy` und hat `RestartCount=0`.
- `docker compose ls` zeigt fuer CORAPAN `infra running(2)` und damit genau die aktuell compose-gemanagten Services `web` und `db`.
- Es existieren keine `exited`-Container der CORAPAN-Produktionsinstanz mehr.

### 3.2 BlackLab ist live, aber weiterhin Sonderfall ausserhalb des Compose-V2-Stacks

- `corapan-blacklab` laeuft stabil ohne Restart.
- Der Container ist aelter als der neu deployte Web/DB-Teil und traegt keine Compose-V2-Labels.
- BlackLab ist gleichzeitig an `corapan-network-prod` und an dem zusaetzlichen Netz `corapan-network` angeschlossen.
- BlackLab liest weiterhin produktiv aus `/srv/webapps/corapan/data/blacklab_index` und damit aus dem bekannten top-level-first-Modell.

### 3.3 Runtime-ENV und Mounts der Web-App sind konsistent

Die Web-App ist aktuell intern konsistent konfiguriert:

- `CORAPAN_RUNTIME_ROOT=/app`
- `CORAPAN_MEDIA_ROOT=/app/media`
- `PUBLIC_STATS_DIR=/app/data/public/statistics`
- `STATS_TEMP_DIR=/app/data/stats_temp`
- `DATABASE_URL` und `AUTH_DATABASE_URL` zeigen auf `db:5432/corapan_auth`
- `BLS_BASE_URL=http://corapan-blacklab:8080/blacklab-server`
- `BLS_CORPUS=corapan`

Die aktiven Web-Mounts zeigen weiterhin sauber auf den Runtime-Baum:

- `/srv/webapps/corapan/runtime/corapan/data -> /app/data`
- `/srv/webapps/corapan/runtime/corapan/media -> /app/media`
- `/srv/webapps/corapan/runtime/corapan/logs -> /app/logs`
- `/srv/webapps/corapan/runtime/corapan/config -> /app/config`

### 3.4 DB-Persistenz ist plausibel intakt

- `corapan-db-prod` verwendet weiter das benannte Volume `corapan_postgres_prod`.
- PostgreSQL meldet beim Start korrekt, dass bereits ein bestehendes Datenverzeichnis vorliegt und keine Neuinitialisierung erfolgt.
- Die Datenbank startet sauber und meldet `database system is ready to accept connections`.
- Read-only-Pruefung des `public`-Schemas ergab aktuell genau vier Tabellen:
  - `analytics_daily`
  - `refresh_tokens`
  - `reset_tokens`
  - `users`

Diese Tabellenlage passt zur laufenden Auth- und Analytics-Nutzung der Anwendung und ist damit betrieblich plausibel.

## 4. Befunde

### Befund A - Der eigentliche Deploy-Zustand ist aktuell stabil

- Beobachtung:
  Web und DB sind gesund, ohne Restarts, und die Web-App verarbeitet nach dem Deploy wieder erfolgreiche Admin-Logins und Suchanfragen.
- Bewertung:
  Der aktuelle Live-Zustand ist nicht nur funktional, sondern auch auf Container- und Runtime-Ebene belastbar.
- Risiko:
  kurzfristig niedrig
- Empfehlung:
  keine Sofortmassnahme erforderlich

### Befund B - Es gab ein historisches Fehlerfenster waehrend des Restart-/Umschaltmoments, aber keinen aktuell fortlaufenden Defekt

- Beobachtung:
  Im Web-Log liegen um ca. `13:35` bis `13:36` Fehler mit `server closed the connection unexpectedly` sowie `Temporary failure in name resolution` fuer Host `db`. Spaeter folgen jedoch erfolgreiche App-Starts, erfolgreiche Admin-Logins und wieder normale Query-Aktivitaet.
- Bewertung:
  Das Muster passt zu einem kurzen Umschalt- oder Restart-Fenster der Datenbank bzw. des Netznamens waehrend des Deploys und nicht zu einem weiterhin anhaltenden Fehlerzustand.
- Risiko:
  aktuell niedrig, historisch nachvollziehbar
- Empfehlung:
  im Bericht als normales Deploy-Begleitfenster dokumentieren, aber nicht als gegenwaertigen Incident fehlklassifizieren

### Befund C - BlackLab ist funktional angebunden, bleibt aber infrastrukturell ein Altfall

- Beobachtung:
  BlackLab verarbeitet Anfragen erfolgreich, ist aber weder Teil des aktuellen Compose-V2-Projekts `infra` noch sauber auf ein einziges Produktionsnetz reduziert.
- Bewertung:
  Funktional ist die Integration derzeit in Ordnung. Operativ bleibt sie jedoch eine separate Legacy-Insel mit eigener Ownership- und Netzrealitaet.
- Risiko:
  mittel
- Empfehlung:
  in einer naechsten Welle BlackLab-Ownership, Netzzuordnung und Lifecycle explizit bereinigen, aber nicht ad hoc im laufenden Zustand anfassen

### Befund D - Compose-V1-Metadaten leben auf aktiven Ressourcen weiter

- Beobachtung:
  Das aktive Produktionsnetz `corapan-network-prod` und das aktive PostgreSQL-Volume `corapan_postgres_prod` tragen weiterhin Legacy-Labels mit `com.docker.compose.version=1.29.2`, waehrend die laufenden Web- und DB-Container bereits Compose V2 (`2.37.1`) tragen.
- Bewertung:
  Der produktive Betrieb funktioniert damit aktuell, aber die Ressourcenmetadaten sind nicht vollstaendig auf denselben Orchestrierungszustand gehoben.
- Risiko:
  mittel, vor allem fuer kuenftige Ownership- und Reconcile-Situationen
- Empfehlung:
  als bekannte Altlast bestehen lassen, bis eine geplante kontrollierte Metadaten-/Ressourcenbereinigung mit Wartungsfenster vorbereitet ist

### Befund E - Das Auth-Schema ist betrieblich plausibel, aber migrationsgovernance-seitig unscharf

- Beobachtung:
  Das `public`-Schema enthaelt genau die vier aktuell benoetigten Tabellen. Die Abfrage `to_regclass('public.alembic_version')` liefert leer, also keine Alembic-Tabelle. Gleichzeitig prueft die App beim Start explizit auf das Vorhandensein von `users`, und produktive Logins funktionieren.
- Bewertung:
  Es gibt derzeit keinen Hinweis auf ein kaputtes produktives Auth-Schema. Es gibt aber auch keinen Beleg fuer eine klassisch nachverfolgbare Alembic-Migrationshistorie in dieser Produktionsdatenbank.
- Risiko:
  mittel, aber eher Governance-/Nachvollziehbarkeitsrisiko als akuter Betriebsfehler
- Empfehlung:
  in einer separaten Welle klaeren, welches Schema-Regime fuer PROD kanonisch sein soll: explizite Migrationen, Bootstrap-Schema oder dokumentierter Hybridzustand

### Befund F - Ein echter historischer App-Fehler ist im File-Log sichtbar und sollte nicht ignoriert werden

- Beobachtung:
  Im Web-File-Log erscheint ein `sqlalchemy.exc.DataError` mit `value too long for type character varying(36)` vor dem spaeteren erfolgreichen Neustartfenster.
- Bewertung:
  Das ist kein reiner Deploy-Restart-Effekt, sondern ein echter fachlich-technischer Fehlerpfad im Anwendungscode oder in den eingehenden Daten.
- Risiko:
  mittel, weil der Fehler nicht akut dauerhaft ansteht, aber prinzipiell wieder ausloesbar sein kann
- Empfehlung:
  separat im Application-Layer nachverfolgen: betroffener Request, betroffenes Feld und zugehoerige Validierungs-/Schema-Regel identifizieren

### Befund G - Das aktuelle Log-Ende wirkt unauffaellig

- Beobachtung:
  Im aktuellen Tail nach dem erfolgreichen Redeploy sind normale App-Starts, erfolgreiche Admin-Authentifizierung und normale Suchaktivitaet sichtbar. Im DB-Log sind nach dem Neustart hauptsaechlich meine eigenen fehlerhaften Diagnoseabfragen als SQL-Fehler sichtbar; diese sind kein Produktionsdefekt.
- Bewertung:
  Der gegenwaertige Endzustand ist logseitig stabil. Die in den DB-Logs sichtbaren SQL-Syntax-/Referenzfehler duerfen nicht als Systemproblem fehlgedeutet werden.
- Risiko:
  niedrig
- Empfehlung:
  DB-Logfehler aus diesem Diagnosefenster explizit als agenteninduzierte Pruefartefakte klassifizieren

### Befund H - Freier Speicher bleibt knapp

- Beobachtung:
  Auf `/` und damit praktisch auch fuer `/srv` verbleiben nur rund `6.2` bis `6.3` GB frei; die Belegung liegt bei etwa `88%`.
- Bewertung:
  Das ist kein akuter Incident, aber eine systemische Betriebsgrenze. Bei weiteren Backups, Logwachstum oder Index-Artefakten kann daraus schnell ein echtes Betriebsrisiko werden.
- Risiko:
  mittel bis hoch auf Sicht
- Empfehlung:
  Kapazitaets- und Bereinigungswelle priorisieren, bevor erneut groessere Daten- oder Indexoperationen erfolgen

### Befund I - `START_ADMIN_PASSWORD` ist leer, derzeit aber kein akuter Defektbeleg

- Beobachtung:
  In der Web-Runtime-ENV ist `START_ADMIN_PASSWORD=` leer, waehrend produktive Admin-Authentifizierung trotzdem funktioniert.
- Bewertung:
  Das spricht dafuer, dass der Wert im aktuellen Betriebsmodell nicht fuer jeden Start zwingend gebraucht wird oder nur im Bootstrap relevant ist. Ohne gegenteilige Code-Evidenz ist das vorerst eine Beobachtung, kein Vorfall.
- Risiko:
  derzeit niedrig
- Empfehlung:
  bei Gelegenheit dokumentieren, ob dieser Wert absichtlich leer bleiben darf oder ob die Produktionsdoku hier geschaerft werden sollte

## 5. Risiken / Altlasten

Die wesentlichen verbleibenden Risiken nach dem erfolgreichen Deploy sind nicht der aktuelle Web/DB-Livebetrieb selbst, sondern die noch vorhandenen Infrastrukturaltlasten:

1. BlackLab bleibt ausserhalb des Compose-V2-gemanagten Produktivstacks und haengt an zwei Netzen.
2. Aktive Produktionsressourcen tragen weiter Compose-V1-Metadaten, obwohl der operative Deploy bereits auf Compose V2 laeuft.
3. Das DB-Schema wirkt betriebsfaehig, ist aber nicht ueber eine sichtbare Alembic-Historie nachvollziehbar.
4. Im Anwendungscode existiert mindestens ein echter historischer `varchar(36)`-Fehlerpfad.
5. Die freie Plattenkapazitaet ist fuer eine produktive Instanz mit Daten- und Indexartefakten zu knapp.

## 6. Sofortmassnahmenbedarf

Es besteht nach aktuellem Befund kein akuter Sofortmassnahmenbedarf.

Nicht erforderlich sind derzeit:

- kein erneuter Redeploy
- kein Container-Neustart
- keine Ad-hoc-Netzwerkoperation an `corapan-network-prod`
- keine Ad-hoc-Volume-Operation an `corapan_postgres_prod`
- keine spontane BlackLab-Migration im laufenden Betrieb

Sofort reagieren sollte man nur, wenn sich eines der folgenden Signale veraendert:

- steigende Restart-Zahlen bei `corapan-web-prod` oder `corapan-db-prod`
- erneute `db`-Name-Resolution-Fehler ausserhalb eines Deploy-Fensters
- neue haeufige 500er beim Login oder Auth-Pfad
- schnelles weiteres Absinken des freien Speichers

## 7. Empfohlene naechste Wellen

### Welle P1 - BlackLab-Ownership und Netzrealitaet bereinigen

Ziel:
BlackLab aus dem legacyartigen Sonderzustand in einen klar dokumentierten und kontrollierten Betriebszustand ueberfuehren.

Inhalt:

- entscheiden, ob BlackLab kuenftig compose-gemanagt oder bewusst separat betrieben wird
- duale Netzzuordnung `corapan-network` plus `corapan-network-prod` aufraeumen
- Container-Ownership, Healthcheck und Lifecycle dokumentieren oder vereinheitlichen

### Welle P2 - Compose-Metadaten-Altlasten kontrolliert abbauen

Ziel:
Netz- und Volume-Metadaten an den realen Compose-V2-Betrieb angleichen, ohne laufende Produktion unkontrolliert zu beruehren.

Inhalt:

- Wartungsfenster fuer geplante Ressourcenbereinigung vorbereiten
- genaue Recreate- und Rollback-Sequenz fuer Netzwerk-/Volume-Metadaten dokumentieren
- vorab erneut pruefen, welche Labels fuer Compose-V2-Reconcile wirklich noch relevant stoeren

### Welle P3 - DB-Schema-Governance explizit machen

Ziel:
die produktive Auth-/Analytics-DB nicht nur betriebsfaehig, sondern auch revisionssicher nachvollziehbar machen.

Inhalt:

- pruefen, ob PROD bewusst ohne Alembic-Tabelle betrieben wird
- falls nein: kanonischen Migrationspfad definieren
- falls ja: dokumentierten Bootstrap-/Schema-Contract fuer PROD erstellen

### Welle P4 - Application-Fehler `varchar(36)` isolieren

Ziel:
den im Log sichtbaren echten Datenfehler reproduzierbar und ursachensauber absichern.

Inhalt:

- Request-Kontext und betroffenes Feld identifizieren
- Modell- oder Validierungsregel gegen die realen Eingabedaten pruefen
- entscheiden, ob Schema, Validation oder Upstream-Daten begrenzt werden muessen

### Welle P5 - Speicher- und Datenartefakt-Hygiene

Ziel:
genug operativen Puffer fuer Backups, Logs und Indexbewegungen schaffen.

Inhalt:

- Backups, alte Index-Artefakte und veraltete Runtime-Duplikate inventarisieren
- Loesch- und Archivierungsstrategie definieren
- minimale freie Betriebsreserve festlegen

## 8. Belege / relevante Kommandos / Outputs

Die Diagnose stuetzt sich auf folgende Live-Befunde:

- `docker ps --format ...`
  - `corapan-web-prod` healthy, restart count `0`
  - `corapan-db-prod` healthy, restart count `0`
  - `corapan-blacklab` laufend, ohne Compose-V2-Labels
- `docker compose ls`
  - Projekt `infra running(2)`
- `docker inspect` auf Container, Netz und Volume
  - `corapan-network-prod` mit Legacy-Label `com.docker.compose.version=1.29.2`
  - `corapan_postgres_prod` mit Legacy-Label `com.docker.compose.version=1.29.2`
  - BlackLab an zwei Netzen angeschlossen
- read-only `psql`-Abfragen im DB-Container
  - `public` enthaelt `analytics_daily`, `refresh_tokens`, `reset_tokens`, `users`
  - `to_regclass('public.alembic_version')` liefert leer
- Web-Log-Tail
  - erfolgreiche App-Starts, erfolgreicher Admin-Login, normale Suchaktivitaet nach dem Deploy
- DB-Log-Tail
  - sauberer Start des DB-Servers
  - spaetere SQL-Fehler stammen aus fehlerhaften Diagnoseabfragen waehrend dieser Analyse
- BlackLab-Logs
  - aktive Scans von `/data/index`
  - erfolgreiche Suchanfragen auf dem Corpus `corapan`

## 9. Executive Summary

Der Produktionszustand nach dem Deploy ist aktuell technisch tragfaehig. Web und DB laufen gesund unter Compose V2, die Runtime-Konfiguration ist konsistent, produktive Logins funktionieren und BlackLab beantwortet Anfragen. Es gibt keinen Hinweis auf einen gegenwaertigen akuten Produktionsdefekt.

Die verbleibenden Probleme liegen vor allem in den Altlasten rund um Orchestrierung und Betriebsmodell: BlackLab ist weiterhin ein separater Legacy-Sonderfall, aktive Ressourcen tragen noch Compose-V1-Metadaten, die produktive DB ist schema-seitig nur betrieblich, nicht migrationshistorisch sauber eingeordnet, und die freie Speicherkapazitaet bleibt knapp.

Fazit: kein Hotfix-Bedarf, aber klarer Bedarf fuer gezielte Folgearbeiten in den Bereichen BlackLab-Ownership, Compose-Metadatenbereinigung, DB-Schema-Governance, Fehlerpfad `varchar(36)` und Speicherkapazitaet.