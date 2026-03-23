# Welle 4 PROD Inventory Summary

Datum: 2026-03-20
Umgebung: Production live, read-only
Scope: reale aktive Pfadnutzung unter /srv/webapps/corapan, laufende Container, Mounts, ENV-Secrets-Einbindung, Logs und sichere Smoke-Requests
Methodik: nur lesende Pruefung, keine Deploys, keine Restarts, keine Migrationen, keine Datenaenderungen

## 8.1 Zusammenfassung

Die produktive Web-App ist live eindeutig runtime-first.

Belegt aktiv fuer die Web-App sind die Mounts:

- /srv/webapps/corapan/runtime/corapan/data -> /app/data
- /srv/webapps/corapan/runtime/corapan/media -> /app/media
- /srv/webapps/corapan/runtime/corapan/logs -> /app/logs
- /srv/webapps/corapan/runtime/corapan/config -> /app/config

Die produktive BlackLab-Instanz ist dagegen live nicht runtime-first, sondern nutzt weiterhin Top-Level-Pfade:

- /srv/webapps/corapan/data/blacklab_index -> /data/index/corapan
- /srv/webapps/corapan/app/config/blacklab -> /etc/blacklab

Damit gibt es in PROD derzeit zwei reale Pfadmodelle gleichzeitig:

- Web-App: runtime/corapan/... ist aktiv und gewinnt
- BlackLab: Top-Level data/app/config ist aktiv und gewinnt

Wichtige Entscheidung aus Live-Evidenz:

- runtime/corapan ist in PROD nicht historisch, sondern fuer die Web-App aktiv
- Top-Level media ist fuer die Web-App nicht aktiv
- Top-Level config ist fuer Secrets-Einbindung aktiv
- Top-Level BlackLab-Pfade sind fuer BlackLab aktiv

Die Produktion enthaelt ausserdem mehrere nicht inode-identische Doppelstrukturen. Diese sind nicht nur dokumentarische Altlasten, sondern echte parallele Dateibaeume mit eigenem Risiko.

## 8.2 Quellen und Belege

Geprueft wurden:

- live Host-Dateibaeume unter /srv/webapps/corapan
- laufende Container und deren Mounts
- redaktierte Web-Container-ENV-Werte
- produktive Compose- und Deploy-Quellen auf dem Host
- sichere Smoke-Requests gegen Web-App und BlackLab
- Docker- und Dateilogs read-only

Live belegte Web-ENV-Werte:

- FLASK_ENV=production
- CORAPAN_RUNTIME_ROOT=/app
- CORAPAN_MEDIA_ROOT=/app/media
- PUBLIC_STATS_DIR=/app/data/public/statistics
- STATS_TEMP_DIR=/app/data/stats_temp
- BLS_BASE_URL=http://corapan-blacklab:8080/blacklab-server
- BLS_CORPUS=corapan
- AUTH_DATABASE_URL=postgresql+psycopg2://...@db:5432/corapan_auth

Live Smoke-Ergebnisse:

- /health -> 200
- /api/v1/atlas/files -> 200
- /corpus/metadata/download/json -> 200
- /corpus/api/statistics/corpus_stats.json -> 200
- /search/advanced/data?q=casa&mode=lemma&draw=1&start=0&length=1 -> 200
- /media/full/... -> 302 auf Login
- /media/transcripts/... -> 302 auf Login
- BlackLab /blacklab-server/ -> 200
- BlackLab sample hits auf corapan -> 200

## 8.3 Pfadklassifikation

| Pfad | Klassifikation | Gewinner | Live-Beleg | Bewertung |
|---|---|---|---|---|
| /srv/webapps/corapan/runtime/corapan | ACTIVE_CANONICAL | Web-App | direkt in Live-Mounts des Web-Containers | nicht historisch |
| /srv/webapps/corapan/runtime/corapan/data | ACTIVE_CANONICAL | Web-App | /app/data Mount, Atlas/Metadata/Statistics/Search live erfolgreich | aktive operative Datenbasis der Web-App |
| /srv/webapps/corapan/runtime/corapan/media | HIGH_RISK_ACTIVE | Web-App | /app/media Mount, Verzeichnis gross und gefuellt, Media-Routen reagieren konsistent | aktive geschuetzte Medienbasis |
| /srv/webapps/corapan/runtime/corapan/logs | HIGH_RISK_ACTIVE | Web-App | /app/logs Mount, Datei-Log aktiv | aktive Log-Senke der Web-App |
| /srv/webapps/corapan/runtime/corapan/config | ACTIVE_CANONICAL | Web-App-Mountflaeche | /app/config Mount vorhanden, Verzeichnis aber leer | aktiv gemountet, derzeit nicht die Secrets-Quelle |
| /srv/webapps/corapan/runtime/corapan/data/public/metadata/latest | ACTIVE_CANONICAL | Web-App | Metadata-Download 200 | aktiv fuer Metadaten |
| /srv/webapps/corapan/runtime/corapan/data/public/statistics | ACTIVE_CANONICAL | Web-App | corpus_stats.json 200 | aktiv fuer oeffentliche Statistikartefakte |
| /srv/webapps/corapan/runtime/corapan/data/stats_temp | HIGH_RISK_ACTIVE | Web-App | STATS_TEMP_DIR zeigt live darauf | aktive Schreibflaeche fuer Statistik-Cache/Temp |
| /srv/webapps/corapan/runtime/corapan/data/db/public | HIGH_RISK_ACTIVE | Web-App | stats_country.db und stats_files.db vorhanden | aktive Side-DB-Flaeche |
| /srv/webapps/corapan/runtime/corapan/data/db/restricted | UNCLEAR | derzeit keine klare aktive Nutzung belegt | Verzeichnis vorhanden, leer | nicht loeschen, aber aktuell ohne Nutzungsbeleg |
| /srv/webapps/corapan/runtime/corapan/data/blacklab_export | DUPLICATED | unklar | 1.5G vorhanden, anderer Inode als Top-Level Export | Parallelrealitaet mit hohem Verwechslungsrisiko |
| /srv/webapps/corapan/runtime/corapan/data/blacklab_export/docmeta.jsonl | HIGH_RISK_ACTIVE | wahrscheinlich Web-App | Advanced Search 200, Datei vorhanden im aktiven Web-App-Datenbaum | keine harte Einzel-Leseprobe, aber hochrelevant |
| /srv/webapps/corapan/runtime/corapan/data/blacklab_index | DUPLICATED | unklar | 279M vorhanden, anderer Inode als Top-Level Index | nicht der live BlackLab-Mount |
| /srv/webapps/corapan/config/passwords.env | HIGH_RISK_ACTIVE | Deploy/Compose | env-file live aus Top-Level config eingebunden | aktive Secrets-Quelle |
| /srv/webapps/corapan/config | ACTIVE_CANONICAL | Deploy/Compose | enthaelt passwords.env | gewinnt fuer Secrets, nicht fuer /app/config |
| /srv/webapps/corapan/data | ACTIVE_LEGACY | BlackLab-Topologie | BlackLab-Index und Export liegen hier aktiv | Top-Level Datenbaum bleibt produktiv relevant |
| /srv/webapps/corapan/data/blacklab_index | HIGH_RISK_ACTIVE | BlackLab | direkter Live-Mount in corapan-blacklab | aktiver Suchindex |
| /srv/webapps/corapan/data/blacklab_export | HIGH_RISK_ACTIVE | BlackLab-nahe Exportrealitaet | 1.5G vorhanden, docmeta vorhanden | aktiv relevant, auch wenn direkter Container-Mount nicht belegt |
| /srv/webapps/corapan/app/config/blacklab | HIGH_RISK_ACTIVE | BlackLab | direkter Live-Mount in corapan-blacklab | aktive BlackLab-Konfiguration |
| /srv/webapps/corapan/app | ACTIVE_LEGACY | Code/BlackLab-Konfig | produktiver Checkout liegt hier | fuer Web-Code-Deploy aktiv, strukturell legacy zum Zielmodell |
| /srv/webapps/corapan/media | INACTIVE | niemand | leer | fuer Web-Medien nicht aktiv |
| /srv/webapps/corapan/logs | DUPLICATED | unklar | anderer Inode als runtime logs, corapan.log vorhanden | Parallel-Logrealitaet, nicht Web-Container-Mount |
| /srv/webapps/corapan/runner | HIGH_RISK_ACTIVE | Deploy-Automation | gross, produktionsrelevant, Runner-Pfad | nicht in diese Welle eingreifen |
| Docker volume corapan_postgres_prod | HIGH_RISK_ACTIVE | PostgreSQL/Auth/Core | live DB-Mount auf /var/lib/postgresql/data | kritisch, ausserhalb der Pfadvereinheitlichung |

## 8.4 Gewinner je Bereich

### Web-App

Gewinner ist klar runtime/corapan.

Die laufende Web-App liest und schreibt effektiv ueber /app auf:

- runtime/corapan/data
- runtime/corapan/media
- runtime/corapan/logs
- runtime/corapan/config

### Secrets und ENV

Gewinner ist nicht runtime/corapan/config, sondern Top-Level config/passwords.env.

Die ENV-Secrets werden ueber den Deploy-/Compose-Pfad aus:

- /srv/webapps/corapan/config/passwords.env

geladen.

### BlackLab

Gewinner sind weiter Top-Level-Pfade.

BlackLab nutzt live:

- /srv/webapps/corapan/data/blacklab_index
- /srv/webapps/corapan/app/config/blacklab

runtime/corapan/data/blacklab_index gewinnt fuer BlackLab gerade nicht.

### Medien

Gewinner ist runtime/corapan/media.

Top-Level /srv/webapps/corapan/media ist leer und verliert klar.

### Logs

Gewinner fuer den Web-Container ist runtime/corapan/logs.

Top-Level /srv/webapps/corapan/logs existiert separat und ist daher keine harmlose Alias-Struktur.

## 8.5 Konflikte zwischen Live-System, Compose und Skripten

| Konflikt | Live-System | Compose/Skript | Klassifikation | Bewertung |
|---|---|---|---|---|
| Web-App-Struktur | runtime/corapan/* aktiv | infra/docker-compose.prod.yml bestaetigt runtime-first | ACTIVE_CANONICAL | konsistent |
| Secrets-Struktur | Top-Level config/passwords.env aktiv | scripts/deploy_prod.sh und Compose referenzieren Top-Level config | ACTIVE_CANONICAL | konsistent, aber getrennt vom /app/config-Mount |
| BlackLab-Struktur | Top-Level data/app config aktiv | scripts/blacklab/run_bls_prod.sh bestaetigt Top-Level-Nutzung | ACTIVE_LEGACY | absichtlich oder historisch fortgeschrieben, aber live aktiv |
| Gesamtmodell PROD | Web-App runtime-first, BlackLab top-level-first | Zielmodell will eine Wurzel ohne Parallelrealitaet | DANGEROUS | strukturell nicht vereinheitlicht |
| data vs runtime/data | beide vorhanden, verschiedene Inodes | Docs/Zielmodell duldet keine parallelen Wahrheiten | DANGEROUS_DUPLICATION | hohes Fehlleitungsrisiko |
| blacklab_index vs runtime/.../blacklab_index | beide vorhanden, verschiedene Inodes | BlackLab nutzt nur Top-Level-Mount | DANGEROUS_DUPLICATION | spaetere Bereinigung hochriskant |
| blacklab_export vs runtime/.../blacklab_export | beide vorhanden, verschiedene Inodes | keine einheitliche Live-Quelle klar fuer alle Verbraucher | DANGEROUS_DUPLICATION | docmeta-/Export-Verwechslungsrisiko |
| logs vs runtime/logs | beide vorhanden, verschiedene Inodes | Web-Container schreibt in runtime/logs | DANGEROUS_DUPLICATION | Diagnose- und Retention-Risiko |

## 8.6 Risikokarte

### Zone A: Sofort als HIGH_RISK_ACTIVE behandeln

- Docker volume corapan_postgres_prod
- /srv/webapps/corapan/config/passwords.env
- /srv/webapps/corapan/data/blacklab_index
- /srv/webapps/corapan/app/config/blacklab
- /srv/webapps/corapan/runtime/corapan/media
- /srv/webapps/corapan/runtime/corapan/logs
- /srv/webapps/corapan/runtime/corapan/data/stats_temp
- /srv/webapps/corapan/runtime/corapan/data/db/public
- /srv/webapps/corapan/runner

Begruendung:

- direkte Auth/Core/Secrets-Relevanz
- aktive Live-Mounts
- aktive Schreibpfade
- BlackLab-Kernfunktion
- Deployment- und Betriebsrelevanz

### Zone B: Parallelrealitaeten mit Bereinigungsrisiko

- /srv/webapps/corapan/data
- /srv/webapps/corapan/runtime/corapan/data
- /srv/webapps/corapan/data/blacklab_export
- /srv/webapps/corapan/runtime/corapan/data/blacklab_export
- /srv/webapps/corapan/data/blacklab_index
- /srv/webapps/corapan/runtime/corapan/data/blacklab_index
- /srv/webapps/corapan/logs
- /srv/webapps/corapan/runtime/corapan/logs

Begruendung:

- reale Duplikate statt Symlink/Alias
- unterschiedlicher Aktivstatus je Verbraucher
- Loeschung oder Umhaengen ohne explizite Verbraucher-Matrix waere gefaehrlich

### Zone C: derzeit klar inaktiv oder nachrangig

- /srv/webapps/corapan/media

Begruendung:

- leer
- keine Live-Mount-Gewinnerrolle
- keine Smoke- oder Container-Evidenz fuer aktive Nutzung

## 8.7 Wichtige Folgerungen fuer spaetere Wellen

1. PROD hat aktuell kein einheitliches Strukturmodell.
2. Die Web-App ist bereits runtime-first.
3. BlackLab ist noch nicht auf dasselbe Modell gehoben.
4. Top-Level config/passwords.env bleibt eine separate produktive Wahrheit fuer Secrets.
5. Jede spaetere Vereinheitlichung muss Web-App, BlackLab und Secrets-Fluss getrennt klassifizieren.
6. Eine pauschale Aussage wie runtime/corapan ist nur historisch waere in PROD sachlich falsch.

## 8.8 Empfehlung fuer Folgearbeit

Keine direkte Bereinigung in der naechsten Welle ohne vorgelagerte Verbraucher-Matrix.

Empfohlene Reihenfolge:

1. BlackLab-Pfadwelle separat planen.
2. Fuer jeden doppelten PROD-Baum explizit festhalten, wer liest und wer schreibt.
3. Secrets-Pfad als eigenen Sonderfall behandeln; Top-Level config gewinnt aktuell bewusst.
4. Erst danach Migrations- oder Abschaltplan fuer einzelne Legacy-Pfade formulieren.

## 8.9 Lessons Learned – Run 2026-03-20 (PROD Inventory)

- Problem:
  Die Produktionsstruktur liess sich aus Repo, Compose und Doku allein nicht sicher auf eine einzige aktive Pfadrealitaet reduzieren.
- Ursache:
  Web-App, Secrets-Einbindung und BlackLab folgen in PROD derzeit unterschiedlichen aktiven Pfadmodellen. Zusaetzlich existieren mehrere echte Doppelbaeume mit unterschiedlichen Inodes statt nur symbolischer Altverweise.
- Fix:
  Kein Eingriff in Funktion oder Daten. Stattdessen wurde die Live-Realitaet direkt ueber Host-Dateibaeume, Container-Mounts, ENV-Werte, Logs und sichere Smoke-Requests inventarisiert und je Pfad als active, legacy, duplicated, inactive oder high-risk eingeordnet.
- Neue Regel:
  Produktive Pfadvereinheitlichung darf nie auf Repo-Annahmen beruhen; Live-Laufzeit und reale Mounts schlagen Compose- und Doku-Annahmen.