# Technical Precheck: Sync Constraints

Datum: 2026-03-25

Scope:
- lokale SSH-/rsync-/Upload-Strecke fuer Produktions-Syncs
- nur technische Tragfaehigkeit, Randbedingungen, Workarounds, Altlasten
- keine Aenderung an Deploy- oder Sync-Skripten
- Befunde basieren auf aktivem Code, Repo-Doku und historischen Operator-Logs im Repo

Einschraenkungen:
- Es wurde kein echter End-to-End-Lauf gegen die Produktionsgegenstelle ausgefuehrt.
- Aussagen zu VPN-, Uni-Netz- oder Firewall-Bedingungen sind nur dann als repo-belegt behandelt, wenn sie im Repo selbst nachweisbar sind.
- Wo nur Indizien vorliegen, ist das explizit markiert.

## A. Executive Summary

Kurzurteil:

- Die lokale Produktions-Sync-Strecke ist technisch grundsaetzlich tragfaehig, aber nur innerhalb eines engen Operator-Profils.
- Dieses Profil ist nicht generisch, sondern implizit auf eine Windows-PowerShell-Senderseite mit OpenSSH, cwRsync-Kompatibilitaet, passwortlosem Deploy-Key und direkter Netz-Erreichbarkeit des Zielhosts zugeschnitten.
- Data- und Media-Sync sind klar als rsync-dominierte Delta-Lane gebaut; BlackLab-Publish ist bewusst eine eigene Lane mit anderem Transfermodell, eigener Validierung und atomischem Swap.
- Mehrere heute unschoene Details sind wahrscheinlich keine zufaelligen Codegeraeusche, sondern Reaktionen auf reale Windows-/Transportprobleme: Cygwin-Pfadkonvertierung, 8.3-Key-Pfad, tar+base64-Fallback, Manifest-Migration, Abort-Marker und SCP-/tar-Fallbacks.
- Gleichzeitig gibt es echte technische Schwaechen, die nicht als notwendige Altlast verklart werden duerfen: `StrictHostKeyChecking=no`, Root-SSH als Default, inkonsistente SSH-Implementierung, `rsync --delete` ohne Empty-Source-Guard und unzureichende serverseitige Audit-Spuren.

Praezise Gesamtbewertung:

- Data-Lane: technisch benutzbar, aber historisch driftbehaftet und dokumentarisch widerspruechlich.
- Media-Lane: fuer grosse Datenmengen erkennbar optimiert, aber stark von rsync/cwRsync-Verhalten und stabiler Verbindung abhaengig.
- BlackLab-Lane: architektonisch am saubersten getrennt, aber im eigentlichen Uploadpfad inkonsistent, weil der tar|ssh-Datenpfad den SSH-Helper umgeht.

Wichtigster Meta-Befund:

- Die Strecke darf nicht aggressiv "aufgeraeumt" werden, bevor sie auf einer echten Operator-Maschine mit realer Netzstrecke validiert wurde.
- Vor allem die haesslichen Windows-/SSH-/Fallback-Elemente sind zuerst als betriebliche Kompatibilitaetsmassnahmen zu behandeln, nicht als reine Stilprobleme.

## B. Gefundene technische Transferwege und Varianten

### 1. Aktive Hauptwege

1. Data/Media via rsync
- Implementiert in `app/scripts/deploy_sync/sync_core.ps1` und aufgerufen durch `sync_data.ps1` bzw. `sync_media.ps1`.
- Bevorzugtes Modell: rsync mit Delta-Transfer, Manifesten und `--partial --progress --delete`.
- Windows-seitig wird cwRsync erwartet; Pfade werden in Cygwin-Form konvertiert.

2. Data/Media via tar+base64+SSH-Fallback
- Ebenfalls in `sync_core.ps1` vorgesehen.
- Aktiv, wenn rsync lokal nicht verfuegbar oder nicht lauffaehig ist.
- Das ist ein deutlicher Hinweis auf historisch reale Tool- oder Kompatibilitaetsprobleme auf Operator-Maschinen.

3. BlackLab via tar-over-SSH-Streaming
- Implementiert in `app/scripts/deploy_sync/publish_blacklab_index.ps1`.
- Primaerer Uploadpfad fuer den Index-Staging-Ordner.
- Danach folgen Remote-Verifikation, Validierungscontainer und atomischer Swap.

4. BlackLab via SCP-Fallback
- Ebenfalls in `publish_blacklab_index.ps1` vorhanden.
- Greift, wenn lokal kein `tar` verfuegbar ist.
- Explizit als langsamer und weniger elegant dokumentiert.

### 2. Hilfs- und Sicherungsmechaniken

1. Verzeichnisspezifische Manifeste
- Fuer `transcripts`, `mp3-full`, `mp3-split` und Data-Lane-Verzeichnisse.
- Werden lokal erzeugt und remote gespeichert.
- Dienen der Aenderungserkennung und reduzieren unnötige Uebertragungen.

2. Manifest-Migration
- `sync_core.ps1` migriert alte globale Manifest-Dateien in neue verzeichnisspezifische Pfade.
- Das ist klarer Beleg fuer eine evolutionaere Umbauphase statt Greenfield-Design.

3. Abort-Erkennung per `.sync_start`
- Vor einem Lauf wird ein Marker gesetzt, danach wieder entfernt.
- Wenn Marker neuer als Manifest ist, wird ein vorheriger Abbruch vermutet.
- Das ist ein praktischer Hinweis darauf, dass unterbrochene Laeufe real eingeplant wurden.

4. Ownership-Nachzug auf dem Server
- Nach erfolgreichen Syncs wird Ownership remote vereinheitlicht.
- Das kompensiert die reale Mischung aus `root`-Transport und `hrzadmin`-Runtime-Eigentuemer.

### 3. Historisch belegte Varianten aus Repo-Logs

Die UTF-16-Logdateien unter `maintenance_pipelines/_2_deploy/_logs/` belegen echte Laeufe des Data-Orchestrators.

Dabei fallen zwei Dinge auf:

1. Fruehe Logdatei `deploy_data_20260117_133610.log` zeigt einen Lauf mit `counters`.
- Das passt nicht mehr zum heutigen Schutzmodell, in dem produktiver Runtime-State bewusst ausgeschlossen ist.
- Das ist starker Hinweis auf eine fruehere, breitere Data-Lane oder auf inzwischen entfernte Override-Pfade.

2. Mehrere Logdateien enthalten weiterhin einen Eintrag `blackl...`.
- Zusammen mit alter Doku zu `blacklab_export` ist das ein belastbares Indiz fuer eine fruehere Kopplung zwischen Data-Sync und BlackLab-Exportwelle.
- Heutiger aktiver Code trennt BlackLab explizit aus der Data-Lane heraus.

## C. Historisch erkennbare Workarounds und warum sie vermutlich entstanden sind

### 1. cwRsync- und Cygwin-Pfadlogik

Befund:
- `sync_core.ps1` konvertiert Windows-Pfade nach `/cygdrive/...`.
- Das Script erwartet ein lokales cwRsync-Binary unter `tools/cwrsync/bin`.

Plausibler Ursprung:
- Windows-Operator-Maschinen mit rsync, das keine nativen Win32-Pfade sauber akzeptiert.
- Wahrscheinlich entstanden, weil OpenSSH allein fuer Data/Media nicht ausreichend performant oder nicht resume-faehig genug war.

Bewertung:
- Sehr wahrscheinlich echter Betriebs-Workaround, nicht nur Altlast.

### 2. 8.3-Key-Pfad `C:\Users\FELIXT~1\...`

Befund:
- `_lib/ssh.ps1` fuehrt parallel einen normalen Key-Pfad und einen 8.3-Kurzpfad.
- `sync_core.ps1` verwendet fuer cwRsync explizit den Kurzpfad.

Plausibler Ursprung:
- Probleme von cwRsync/Cygwin mit Windows-Benutzernamen, Leerzeichen oder HOME-Aufloesung.
- Der hart kodierte Kurzpfad ist fast sicher aus einer realen lokalen Kompatibilitaetsstoerung entstanden.

Bewertung:
- Hohe Wahrscheinlichkeit fuer echten Sender-Kompatibilitaetszwang.
- Gleichzeitig untragbar als dauerhaft unparametrisierter Repo-Standard.

### 3. tar+base64-Fallback fuer Data/Media

Befund:
- `sync_core.ps1` faellt auf tar+base64 ueber SSH zurueck, wenn rsync fehlt.

Plausibler Ursprung:
- Nicht jede Operator-Maschine hatte rsync sauber installiert oder funktionierend im PATH.
- Man wollte trotzdem Syncs ohne kompletten Tooling-Stillstand ermoeglichen.

Bewertung:
- Klarer Robustheits-Workaround fuer heterogene lokale Setups.

### 4. SCP-Fallback und tar|ssh bei BlackLab

Befund:
- `publish_blacklab_index.ps1` bevorzugt Streaming via `tar | ssh`, kann aber auf SCP ausweichen.

Plausibler Ursprung:
- Der Index ist gross genug, dass Streaming ohne Zwischenarchive attraktiv ist.
- Gleichzeitig musste eine Option bleiben, wenn `tar` lokal nicht verfuegbar oder nicht brauchbar ist.

Bewertung:
- Betriebliche Redundanz, kein ueberfluessiger Ballast.

### 5. Manifest-Migration und Abort-Marker

Befund:
- Altes globales Manifest-Layout wird in neue Zielpfade migriert.
- `.sync_start` dient als Abbruch-Indikator.

Plausibler Ursprung:
- Fruehere Sync-Generation hatte zu grobe Zustandsverwaltung.
- Es gab reale Unterbrechungen oder teilweise inkonsistente Laeufe.

Bewertung:
- Eindeutig historisch gewachsene Stabilisierung, die man erst nach echten Migrations- und Recovery-Tests entfernen darf.

### 6. Passphrase-loser Deploy-Key und `StrictHostKeyChecking=no`

Befund:
- Der Code setzt automatisierbaren Key-Einsatz voraus.
- Host-Key-Pruefung ist in allen relevanten Pfaden deaktiviert.

Plausibler Ursprung:
- Minimierung manueller Reibung auf einer einzelnen Operator-Maschine.
- Vermeidung von Erstkontakt-, Known-Hosts- und cwRsync/OpenSSH-Mischproblemen.

Bewertung:
- Technisch nachvollziehbar entstanden, aber kein Workaround, der als dauerhaft akzeptabel gelten sollte.

## D. Risiken bei zu aggressiver Bereinigung

1. Entfernen der 8.3-Pfadunterstuetzung ohne reale Windows-Validierung
- Risiko: cwRsync-basierte rsync-Laeufe brechen sofort auf der Operator-Maschine.

2. Entfernen des tar+base64-Fallbacks vor gesicherter rsync-Kanonisierung
- Risiko: Data/Media-Syncs werden komplett von lokalem cwRsync-Setup abhaengig und damit fragiler.

3. Entfernen der Manifest-Migration zu frueh
- Risiko: vorhandene Remote-Zustaende oder Alt-Manifeste werden nicht mehr sauber weitergefuehrt; Delta-Logik kann kippen.

4. Entfernen des Abort-Markers
- Risiko: unterbrochene Laeufe verlieren ihren letzten deutlichen Zustandshinweis; Resume-Szenarien werden schwerer zu deuten.

5. Vereinheitlichung aller Lanes in ein einziges Transfermodell
- Risiko: BlackLab verliert seine abweichenden Anforderungen an Staging, Verifikation, atomischen Swap und Backup-Retention.

6. "Security cleanup" ohne Betriebsmodell
- Beispiel: sofortiges Erzwingen von Host-Key-Pinning oder User-Wechsel ohne Migrationspfad.
- Risiko: die Strecke wird sicherer auf Papier, aber unbenutzbar auf der realen Operator-Maschine.

7. Loeschen alter Docs und Logs ohne Auswertung
- Risiko: historische Betriebsannahmen verschwinden, bevor ihre noch aktiven Reste aus dem Code entfernt wurden.

## E. Lane-Analyse: Data

### 1. Aktive technische Funktion

Heutige aktive Data-Lane umfasst:
- `data/db/public`
- `data/public/metadata`
- `data/exports`
- einzelne Stats-DBs `stats_files.db` und `stats_country.db`
- Statistik-Dateien `corpus_stats.json` und `viz_*.png`

Explizit ausgeschlossen:
- `data/blacklab/*`
- `data/stats_temp`
- `data/db/auth.db`
- weitere produktive DBs

### 2. Technische Staerken

1. Klare Blockade fuer Auth-/Produktionszustand im aktiven Code.
2. Stats-Dateien werden allowlist-basiert hochgeladen, nicht als blindes Verzeichnis.
3. Stats-Lane nutzt kein `--delete`.
4. Delta-Transfer und Manifeste reduzieren Uebertragungsvolumen.

### 3. Historische Drift

1. Repo-Doku und Logs deuten auf eine fruehere breitere Lane mit `counters` und BlackLab-Naehe.
2. `maintenance_pipelines/_2_deploy/README_STATISTICS_DEPLOY.md` beschreibt Override-Flags, die im heutigen Orchestrator nicht existieren.
3. Der Orchestrator beschreibt alte Pfade (`data/metadata`) unpraezise, waehrend der aktive Code `data/public/metadata` nutzt.

### 4. Technische Schwaechen

1. `deploy_data.ps1` deployed Statistik-Dateien doppelt.
2. Teile des Stats-rsync-Outputs werden unterdrueckt; echte Aenderungslisten fehlen.
3. `data/exports` ist im Sync-Modell vorgesehen, aber serverseitig historisch/operativ nicht stabil belegt.
4. Die Lane ist fachlich heute schmaler als ihre Doku und ihre aelteren Logspuren.

### 5. Urteil

- Die Data-Lane ist technisch verwendbar.
- Sie ist aber die Lane mit der staerksten historischen Begriffs- und Scope-Verschiebung.
- Vor Refactor muss zuerst sauber zwischen aktivem Data-Scope, historischen Resten und nur dokumentierten Altannahmen getrennt werden.

## F. Lane-Analyse: Media

### 1. Aktive technische Funktion

Heutige aktive Media-Lane umfasst:
- `media/transcripts`
- `media/mp3-full`
- `media/mp3-split`

Bewusst ausgeschlossen:
- `media/mp3-temp`

### 2. Technische Tragfaehigkeit fuer grosse Daten

Repo-belegt vorhanden sind:

1. `--partial`
- Resume-Unterstuetzung fuer unterbrochene grosse Transfers.

2. `--progress`
- Fortschrittsanzeige pro Datei, offenbar wichtig fuer lange Audio-Laeufe.

3. Delta-Modell plus Manifeste
- Reduziert den Zwang zu Vollsyncs bei grossen Bestaenden.

4. `-ForceMP3`
- Erlaubt grossen Neuabgleich nur fuer Audio-Zweige.

### 3. Was nicht belegt ist

Nicht repo-belegt sind:

1. automatische Wiederholversuche mit Backoff fuer Media-rsync
2. harte Verbindungsrekonnektion bei Netzabbruechen
3. Bandbreiten-Drosselung
4. Checkpointing jenseits von rsync-Partial-Dateien
5. formale Integritaetspruefung nach dem Transfer ausser rsync-Exitcode und Manifest-Aktualisierung

### 4. Operatives Risikoprofil

1. Die Lane ist am staerksten von stabiler Netzverbindung abhaengig.
2. `rsync --delete` ist bei grossen Verzeichnisbaeumen besonders riskant, wenn die Quelle versehentlich leer oder falsch gemountet ist.
3. Die technische Sicherheit stammt primar aus rsync-Verhalten und nicht aus zusaetzlichen Guardrails.

### 5. Urteil

- Media ist die glaubwuerdigste Begruendung dafuer, warum die rsync-basierte Strecke ueberhaupt existiert.
- Gerade diese Lane sollte vor jeder Vereinfachung auf einer echten Operator-Maschine mit grossem MP3-Bestand validiert werden.
- Hier sind die haesslichen Kompatibilitaetsdetails am ehesten produktionsrelevant.

## G. Lane-Analyse: BlackLab

### 1. Aktive technische Funktion

BlackLab ist keine Untermenge der Data-Lane, sondern eine eigenstaendige Publish-Welle:

1. lokaler Staging-Ordner `data/blacklab/quarantine/index.build`
2. Upload nach remote `data/blacklab/quarantine/index.upload_<timestamp>`
3. Remote-Dateizaehlung und Groessencheck
4. Validierung mit temporaerem BlackLab-Container
5. atomischer Swap auf den aktiven Indexpfad
6. anschliessende Backup-Retention

### 2. Technische Staerken

1. Saubere Trennung vom normalen Data-Sync.
2. Eigene Preflight-Checks fuer Dateianzahl und Mindestgroesse.
3. Staging plus atomischer Swap senken das Risiko halbfertiger Aktivbestuende.
4. Backup-Modell ist vorhanden.

### 3. Technische Schwaechen

1. Der eigentliche tar|ssh-Uploadpfad umgeht den SSH-Helper.
2. Die Validierung prueft Corpora-Endpunkte, aber keine echte Hits-Query.
3. Default-Konfigpfad zeigt auf `app/config/blacklab` im Checkout und damit auf deploy-ueberschreibbare Konfiguration.
4. Die Lane haengt nicht nur von SSH, sondern zusaetzlich von `docker`, `curl` und `tar` auf dem Zielhost ab.

### 4. Urteil

- BlackLab ist architektonisch die eigenstaendigste und in Teilen robusteste Lane.
- Sie hat aber ihren kritischsten Bruch genau im Uploadpfad: der Datenkanal ist weniger kanonisiert als der Rest des Skripts.
- Diese Lane braucht vor allem haertere Validierung, nicht Vereinfachung auf Kosten ihrer Sonderlogik.

## H. SSH-/rsync-technische Known Constraints

### 1. Repo-belegte Constraints

1. Windows-PowerShell als Senderumgebung
- Alle aktiven Operator-Skripte sind PowerShell-zentriert.

2. OpenSSH lokal erforderlich
- `_lib/ssh.ps1` nimmt `C:\Windows\System32\OpenSSH\ssh.exe` als Default an.

3. cwRsync-Kompatibilitaet fuer Data/Media praktisch mitgedacht
- Eigener cwRsync-Pfad, Cygwin-Pfadkonvertierung, 8.3-Key-Pfad.

4. Passphrase-loser Key ist faktisch vorausgesetzt
- Sonst wuerden die nichtinteraktiven Laeufe und cwRsync-Aufrufe nicht sauber funktionieren.

5. Root-SSH als Default-Gegenstelle
- Technisch tief in Scripts und Doku verdrahtet.

6. Host-Key-Pruefung ist deaktiviert
- Das macht die Strecke tolerant gegen Erstkontakt und wechselnde lokale Known-Hosts-Zustaende, aber unsicher.

7. Remote Linux-Tooling ist erforderlich
- fuer Data/Media mindestens Standard-Shell-Werkzeuge
- fuer BlackLab zusaetzlich `docker`, `curl`, `tar`

8. Verzeichnisspezifische Manifeste und `.sync_state` gehoeren zur Strecke dazu
- Diese Remote-Dateien sind kein Beiwerk, sondern Teil des Betriebsmodells.

### 2. Nicht repo-belegte, aber sehr plausible Constraints

1. VPN- oder Uni-Netz-Abhaengigkeit
- Im Repo selbst konnte dafuer kein harter Beleg gefunden werden.
- Aufgrund Host-Charakter, manueller Operator-Strecke und Nutzerhinweis ist das sehr plausibel, aber im Bericht nicht als repo-Fakt zu behandeln.

2. einzelne Operator-Maschine als de-facto Referenzsystem
- Die harten Pfade und Defaults sprechen stark dafuer.
- Technisch belegt ist jedoch nur die starke Ausrichtung auf genau ein Windows-Setup, nicht die Organisation dahinter.

## I. Was kanonisiert werden kann

Folgende Punkte wirken stabil genug, um sie spaeter bewusst zu kanonisieren:

1. Drei getrennte Produktions-Lanes
- Data
- Media
- BlackLab

2. Runtime-Zielwurzel
- `/srv/webapps/corapan`
- darunter getrennt `data`, `media`, `logs`, `config`

3. BlackLab als separate Publish-Welle
- kein Mischen mit normalem Data-Sync

4. Manifest-basiertes Delta-Modell fuer Data/Media
- inklusive verzeichnisspezifischer `.sync_state`

5. Resume-freundliche Media-Uebertragung
- `--partial` sollte als Vertragsbestandteil gelten

6. Stats-Dateien als allowlist-basierte Sonderbehandlung
- kein rekursiver Blind-Sync

7. Runtime-first-Mount-Guard
- vor Media/Data sinnvoll, um Drift zwischen Compose und Sync-Zielpfaden zu erkennen

8. Post-Sync-Ownership-Schritt
- solange Root-Transport und hrzadmin-Runtime getrennt sind

## J. Was vorerst bewusst nicht angefasst werden sollte

1. 8.3-Keypfad-Unterstuetzung
- erst nach realem Test auf der Operator-Maschine entfernen

2. tar+base64-Fallback in `sync_core.ps1`
- erst entfernen, wenn rsync/cwRsync auf allen realen Sendern nachweislich standardisiert ist

3. SCP-Fallback in BlackLab-Publish
- erst entfernen, wenn tar-Streaming auf allen relevanten Sendern sicher vorhanden ist

4. Manifest-Migration und Abort-Marker
- erst nach explizitem Altzustands-Cutover und Recovery-Test entfernen

5. Lane-Trennung selbst
- kein Zusammenfalten in einen generischen "sync everything"-Pfad

6. `--partial` fuer Media
- nicht aus Vereinfachungsgruenden streichen

## K. Was auf echter Operator-Maschine/VPN zwingend getestet werden muss

1. Data-Sync mit aktivem cwRsync
- funktioniert der 8.3-Keypfad wirklich noch?
- greifen PATH-Injektion und Cygwin-Pfadkonvertierung sauber?

2. Data-Sync ohne cwRsync
- greift der tar+base64-Fallback wirklich noch end-to-end?

3. Media-Sync mit grosser Datei und Abbruch/Wiederaufnahme
- realer Test mit Mehr-GB-Datei
- Verbindungsabbruch simulieren
- naechsten Lauf auf Resume pruefen

4. Media-Sync mit grossem Dateibaum und No-Change-Lauf
- pruefen, ob Logs und Laufzeit fuer Alltag tragbar bleiben

5. Verhalten bei leerer oder falsch gesetzter Quelle
- derzeit nur kontrolliert in nichtproduktiver Gegenstelle testen
- wichtig fuer Bewertung des `--delete`-Risikos

6. BlackLab tar|ssh-Upload auf echter Senderumgebung
- pruefen, ob PATH-`ssh` identisch zum Helper-Verhalten ist oder abweicht

7. BlackLab SCP-Fallback
- einmal bewusst validieren, damit klar ist, ob der Fallback real nutzbar oder nur theoretisch ist

8. Host-Key- und Known-Hosts-Verhalten
- sobald Haertung geplant ist, Migrationspfad auf echter Operator-Maschine testen

9. reale Netz-Erreichbarkeit unter den tatsaechlichen Betriebsbedingungen
- VPN/Uni-Netz, falls tatsaechlich erforderlich
- dieser Punkt ist fachlich wichtig, aber derzeit nicht repo-belegt

## L. Konkrete Empfehlungen fuer Refactor-Reihenfolge

### Phase 1: Erst verstehen und dokumentieren

1. Eine kurze kanonische Sync-Architektur-README anlegen
- Rollen der drei Lanes
- Sender-Voraussetzungen
- aktive vs. historische Fallbacks

2. Historische Log- und Dokuabweichungen klassifizieren
- was ist aktiv
- was ist legacy
- was ist gefaehrlich falsche Referenz

### Phase 2: Nur eindeutige Fehler bereinigen

1. Doppeltes Statistik-Deployment in `deploy_data.ps1` beseitigen
2. Orchestrator-Doku an aktive Pfade und aktiven Scope anpassen
3. BlackLab-Validierung auf echte Hits-Query erweitern

### Phase 3: SSH- und Logging-Kanonisierung ohne Funktionsverlust

1. Alle Uploadpfade auf einen echten gemeinsamen SSH-Aufrufvertrag bringen
2. persistente Lauf-Logs und maschinenlesbare Summarys pro Sync einfuehren
3. `--delete` mit Empty-Source-Guard, Sentinel oder explizitem Safe-Mode absichern

### Phase 4: Sicherheitshaertung mit Operator-Test

1. Host-Key-Pinning und `known_hosts`-Strategie einfuehren
2. Root-SSH abloesen oder zumindest restriktiver machen
3. harte lokale Pfade parametrisierbar machen

### Phase 5: Erst dann Legacy abbauen

1. 8.3-Sonderpfade nur entfernen, wenn real unnoetig
2. tar+base64- und SCP-Fallback nur entfernen, wenn echte Sender-Validierung vorliegt
3. Manifest-Migration erst nach Altzustands-Cutover streichen

## M. Vorschlag fuer Agent-/Skill-Integration

### 1. Was stabil genug fuer Agent-Wissen ist

Folgende Regeln wirken stabil und sollten nicht nur in Einzel-Dokumenten stehen:

1. Produktions-Sync ist nicht eine Lane, sondern drei getrennte Lanes.
2. Data/Media sind operatorseitige Windows-PowerShell-Syncs, nicht GitHub-Actions-Deploys.
3. BlackLab-Publish ist betrieblich eigenstaendig und darf nicht wie normaler Data-Sync behandelt werden.
4. `--delete` in Data/Media ist Hochrisiko und braucht Guardrails.
5. Grossen Media-Bestand nicht ohne Resume-/Abbruchbetrachtung refactoren.
6. BlackLab-Validierung braucht echte Query-Pruefung, nicht nur Root-/Corpora-Readiness.
7. VPN-/Uni-Netz-Abhaengigkeit ist als moegliche Betriebsrealitaet zu respektieren, aber derzeit nicht repo-belegt.

### 2. Beste Integrationsform

Empfehlung:
- kein Ueberladen einer bestehenden Skill-Datei als alleinige Loesung
- stattdessen eine neue eigenstaendige Skill fuer produktive Sync-Lanes

Vorgeschlagener neuer Skill:
- `.github/skills/server-sync-production-lanes/SKILL.md`

Begruendung:
- Das Thema ist nicht nur BlackLab-Sicherheit.
- Es ist auch nicht nur Maintenance-Scripting.
- Es betrifft operative Pfadwahl, Lane-Trennung, Sender-Voraussetzungen, Logging, Delete-Risiko und Refactor-Sicherheitsregeln.

### 3. Inhalte des vorgeschlagenen Skills

Der Skill sollte Agenten vor Arbeiten an `app/scripts/deploy_sync/**`, `maintenance_pipelines/_2_deploy/**`, `docs/operations/runtime_statistics_deploy.md` und `docs/rsync/**` mindestens zu folgenden Prueffragen zwingen:

1. Welche Lane ist betroffen: Data, Media oder BlackLab?
2. Ist das eine echte Sender-seitige Aenderung oder nur Doku?
3. Wird ein historischer Workaround entfernt?
4. Ist die Aenderung auf echter Operator-Maschine validiert?
5. Wird `--delete`, Resume, Manifest oder Fallback-Verhalten beeinflusst?
6. Wird BlackLab-Validierung auf echte Query-Ebene geprueft?
7. Ist die Annahme ueber VPN/Netz erreichbar belegt oder nur geraten?

### 4. Zusaetzliche kleine Repo-Regel

Neben dem neuen Skill waere ein kurzer Querverweis in der Governance sinnvoll:

- in `.github/instructions/devops.instructions.md`
- knappe Regel: keine Aenderung an produktiven Sync-Lanes ohne Lane-Klassifikation, Operator-Voraussetzungspruefung und Delete-/Fallback-Bewertung

### 5. Was ich nicht empfehlen wuerde

1. Alles nur in `blacklab-operational-safety` abzulegen
- deckt Data/Media und Windows-Senderrealitaet nicht ab

2. Alles nur in `maintenance-script` abzulegen
- dort geht die Produktions- und Lane-Spezifik unter

3. VPN-/Uni-Netz-Zwang schon jetzt als harte Repo-Regel festzuschreiben
- dafuer fehlt im Repo derzeit der belastbare Beleg

## Schlussfazit

Die Produktions-Sync-Strecke ist nicht elegant, aber in ihrer jetzigen Form technisch erklaerbar.
Der Kernfehler waere, repo-sichtbare Workarounds vorschnell als entbehrliche Altlast zu behandeln.

Zuerst kanonisieren:
- Lane-Modell
- aktive Sender-Voraussetzungen
- Logging- und Guardrail-Vertrag

Erst danach vereinfachen:
- SSH-Aufrufe
- Fallbacks
- historische Migrationspfade

Und erst ganz zum Schluss entfernen:
- alles, was auf echter Operator-Maschine nachweislich nicht mehr gebraucht wird.