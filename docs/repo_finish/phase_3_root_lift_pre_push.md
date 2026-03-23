# Phase 3 - Root Lift Pre-Push

## 1. Kurzurteil

Der Root-Lift ist fachlich vorbereitbar, aber im aktuellen Zustand noch **kein Push-Go** fuer einen echten Wechsel auf `C:\dev\corapan` mit gleichzeitigem physischem Rename `webapp -> app`.

Der wichtigste Grund ist nicht die Laufzeit der App, sondern der noch nicht abgeschlossene **Versions- und Workflow-Vertrag**:

- echtes Git-Root liegt weiterhin unter `C:\dev\corapan\webapp`
- die aktuelle versionierte CI-/Deploy-Wahrheit liegt weiterhin unter `webapp/.github/workflows`
- der kuenftige Root-Workflow-Layer unter `C:\dev\corapan\.github\workflows` war vorbereitet, ist aber noch nicht die aktive versionierte Wahrheit

Deshalb war in diesem Run die sichere Strategie:

- alle app-/root-kritischen Resolver und Wrapper auf das Zielbild vorbereiten
- Root-README und Root-.gitignore kanonisieren
- den harten Pre-Push-Impact fuer Deploy, CI, Maintenance und Rename dokumentieren
- den physischen Rename **noch nicht** erzwingen, weil er ohne gleichzeitigen Git-Root-Wechsel keinen push-sicheren Endzustand erzeugt

## 2. Zielstruktur: Root vs App

| Datei/Gruppe | Soll-Ort | Ist-Ort | Handlung |
|---|---|---|---|
| `README.md` | `C:\dev\corapan\README.md` | fehlte am Root | **angelegt**; Root-Systembeschreibung statt App-only README |
| `.gitignore` | `C:\dev\corapan\.gitignore` | vorhanden, aber zu schmal | **kanonisiert** fuer Root-Repo und Zielstruktur |
| `.github/` | `C:\dev\corapan\.github` | bereits am Root | **behalten**, aber klar als lokaler/prep Layer von aktueller Deploy-Wahrheit getrennt |
| `docs/` | `C:\dev\corapan\docs` | bereits am Root | **behalten** |
| `maintenance_pipelines/` | `C:\dev\corapan\maintenance_pipelines` | bereits am Root | **behalten** |
| Root `scripts/` | `C:\dev\corapan\scripts` | bereits am Root | **behalten** als Workspace-/Wrapper-Layer |
| Root Dev Compose | `C:\dev\corapan\docker-compose.dev-postgres.yml` | bereits am Root | **behalten**, rename-vorbereitet |
| App-Code, Tests, Templates, Static, Dockerfile, Infra, Migrations | `C:\dev\corapan\app\...` | aktuell `C:\dev\corapan\webapp\...` | **spaeter physisch verschieben/umbenennen** |
| Runtime-Web-Config | `C:\dev\corapan\data\config` | vorbereitet unter Root-Data | **behalten**, nicht nach `app/` ziehen |
| versionierte BlackLab-Config | `C:\dev\corapan\app\config\blacklab` | aktuell `C:\dev\corapan\webapp\config\blacklab` | **nach Rename mit App mitnehmen**, nicht nach `data/config` verschieben |
| `infra/` | unter `app/infra` | aktuell `webapp/infra` | **in App belassen** |
| app-spezifische Deploy-Skripte | unter `app/scripts` | aktuell `webapp/scripts` | **in App belassen** |

Kanonische Root-Verantwortung:

- Workspace-/Systembeschreibung
- lokale Governance und kuenftige Root-Workflows
- Root-Dev-Wrapper
- Maintenance-Orchestrierung
- nicht versionierte Runtime-Baeume `data/`, `media/`, `logs/`

Kanonische App-Verantwortung:

- versionierter Anwendungscode
- Deploy-/Infra-Implementierung
- tests, migrations, package metadata
- versionierte BlackLab-Config

## 3. webapp -> app Bewertung / Umsetzung

### Bewertung

Ein direkter physischer Rename in diesem Run war **noch nicht sicher pushbar**.

Begruendung:

1. Das echte Git-Root liegt noch unter `webapp/`.
2. Die aktive versionierte Deploy-/CI-Wahrheit liegt noch unter `webapp/.github/workflows`.
3. Ein physischer Rename ohne gleichzeitigen Git-Root-Wechsel wuerde zwar lokal machbar sein, aber keinen belastbaren Push-Vertrag erzeugen.
4. Mehrere Root-Vorbereitungsdateien mussten zuerst app-faehig gemacht werden, damit der spaetere Rename nicht gleichzeitig Wrapper-, Pipeline- und Workflow-Bruecken zerreisst.

### In diesem Run direkt vorbereitet

- Root-Wrapper unter `scripts/` loesen jetzt `app/` zuerst und `webapp/` zweitens auf.
- Root-BlackLab-Wrapper wurden gleichartig app-faehig gemacht.
- Root-Dev-Compose wurde ueber `${CORAPAN_APP_REPO_DIR:-webapp}` rename-vorbereitet.
- Maintenance-Pipelines erkennen jetzt `app/`, dann `webapp/`, dann erst den Workspace-Root.
- Root-`.github`-Vorbereitungsdateien wurden auf das Zielbild `app/` ausgerichtet.

### Direkte Blocker gegen sofortigen physischen Rename

| Blocker | Risiko | Muss vor Push gefixt werden |
|---|---|---|
| Git-Root liegt nicht auf `C:\dev\corapan` | hoch | ja |
| aktive versionierte Workflows liegen noch unter `webapp/.github/workflows` | hoch | ja |
| mehrere aktive App-Skripte und Hilfetexte nennen noch `webapp` als Ist-Zustand | mittel | teilweise; fuer Push-Vertrag dokumentieren, fuer finalen Rename bereinigen |
| heutige lokale Laufzeit und Container-Mounts wurden noch nicht auf eine echte `app/`-Verzeichnislage umgestellt | mittel | ja, wenn Rename physisch ausgefuehrt wird |

## 4. Deploy- und Serververtrag: Pre-Push-Impact

### a) Serververtrag

Produktiver Vertrag:

- App unter `/srv/webapps/corapan/app`
- Runtime-Daten unter `/srv/webapps/corapan/data`
- Media unter `/srv/webapps/corapan/media`
- Logs unter `/srv/webapps/corapan/logs`
- Runtime-Web-Config unter `/srv/webapps/corapan/data/config -> /app/config`
- versionierte BlackLab-Config unter `/srv/webapps/corapan/app/config/blacklab`

Bewertung:

- dieser Serververtrag passt **zum Zielbild** `corapan/app`
- er widerspricht **nicht** dem Root-Lift
- kritisch ist nur, dass die lokale versionierte Workflow-Wahrheit den Wechsel des Repo-Roots noch nicht mitvollzogen hat

### b) Deploy-Skripte

| Fund | Risiko | Muss vor Push gefixt werden | Bewertung |
|---|---|---|---|
| `webapp/scripts/deploy_prod.sh` deployt bereits nach `/srv/webapps/corapan/app` | niedrig | nein | serverseitiger Vertrag ist bereits app-zentriert |
| Root-Prep-Workflow `C:\dev\corapan\.github\workflows\deploy.yml` war noch nur lokal/prep | mittel | ja | wurde als Pre-Push-Vorbereitung gepflegt, ist aber noch nicht versionierte Wahrheit |
| `publish_blacklab.ps1` nutzt bereits Remote-App-Config unter `/srv/webapps/corapan/app/config/blacklab` | niedrig | nein | korrekt |

### c) CI / .github / Runner / Hooks

| Fund | Risiko | Muss vor Push gefixt werden | Bewertung |
|---|---|---|---|
| aktive versionierte Workflows liegen noch unter `webapp/.github/workflows` | hoch | ja | ohne Root-Workflow-Uebergabe kein sauberer Root-Push-Vertrag |
| lokale Root-Workflow-Prep-Dateien liefen noch auf `webapp` | mittel | ja | in diesem Run auf `app` vorbereitet |
| Root-Instructions `applyTo` waren noch nur `webapp/**` | mittel | ja | in diesem Run um `app/**` erweitert |

### d) Maintenance-Pipelines

| Fund | Risiko | Muss vor Push gefixt werden | Bewertung |
|---|---|---|---|
| App-Repo-Resolver suchten bislang nur `webapp` oder Root | hoch | ja | in diesem Run auf `app -> webapp -> root` erweitert |
| Maintenance-Orchestrierung nutzt bereits serverseitig `app`-Pfadannahmen | niedrig | nein | positiv fuer Zielbild |

## 5. Maintenance-Pipelines / rsync / Deploy-Helfer

Positiv bestaetigt:

- `maintenance_pipelines/_2_deploy/publish_blacklab.ps1` verwendet produktionsseitig bereits `app/config/blacklab`
- `deploy_data.ps1` und `deploy_media.ps1` arbeiten gegen Root-Workspace und aktive App-Repo-Erkennung
- `webapp/scripts/deploy_sync/sync_core.ps1` nutzt produktionsseitig Runtime-Root `/srv/webapps/corapan`

In diesem Run direkt korrigiert:

- `maintenance_pipelines/_1_blacklab/blacklab_export.py`: App-Repo-Aufloesung erweitert auf `app/`
- `maintenance_pipelines/_2_deploy/publish_blacklab.ps1`: App-Repo-Aufloesung erweitert auf `app/`
- `maintenance_pipelines/_2_deploy/deploy_data.ps1`: App-Repo-Aufloesung erweitert auf `app/`
- `maintenance_pipelines/_2_deploy/deploy_media.ps1`: App-Repo-Aufloesung erweitert auf `app/`

Offen fuer den finalen Push:

- verbleibende Hilfe-/Beispieltexte in `webapp/scripts/**` sollten mit dem echten Rename bereinigt werden
- erst nach physischem Rename und Git-Root-Lift kann bewertet werden, ob die Root-Fallback-Stufe auf Workspace-Root noch ueberhaupt gebraucht wird

## 6. README / .gitignore / Root-Artefakte

### README.md

Status:

- Root-README fehlte
- wurde in diesem Run neu angelegt

Inhaltlich festgezogen:

- Systembeschreibung auf Root-Ebene
- Trennung Root vs App
- Runtime-Config `data/config`
- versionierte BlackLab-Config `app/config/blacklab`
- aktueller Uebergangszustand `webapp -> app`

### .gitignore

Status:

- vorhandene Root-.gitignore war fuer das kuenftige Root-Repo zu schmal
- wurde in diesem Run erweitert

Direkt korrigiert:

- `logs/` aufgenommen
- `data/`, `media/`, `runtime/` klar ignoriert
- Root- und App-lokale Secret-/Temp-/Cache-Artefakte aufgenommen
- keine pauschale `*.sql`-Ignorierung eingefuehrt, damit versionierte Migrationen nicht ausgeblendet werden

### Root-Artefakte

| Artefakt | Bewertung |
|---|---|
| `C:\dev\corapan\docker-compose.dev-postgres.yml` | aktiver Root-Dev-Einstieg, jetzt rename-vorbereitet |
| `C:\dev\corapan\scripts\*` | Root-Wrapper, jetzt app-faehig vorbereitet |
| `C:\dev\corapan\.github\workflows` | prep-layer fuer kuenftigen Root-Push, noch nicht aktive versionierte Wahrheit |

## 7. Doppelte oder veraltete Dateien

| Datei/Gruppe | Aktuell noch noetig | Nach diesem Run entfernbar | Bewertung |
|---|---|---|---|
| `webapp/docker-compose.dev-postgres.yml` | vorerst ja | nein | Uebergangskopie; erst nach finalem Root-/App-Wechsel pruefen |
| `C:\dev\corapan\.github\workflows` vs `webapp/.github/workflows` | ja | nein | bewusst doppelte Ebenen; Root ist Prep, webapp ist aktuell versioniert aktiv |
| Root-Wrapper, die auf `webapp` verwiesen | nein in alter Form | alte Einzweck-Logik ersetzt | app/webapp-Resolver jetzt als Uebergangsbruecke |
| `C:\dev\corapan\config\blacklab` | wahrscheinlich nein | noch nicht | bereits als Drift klassifiziert; separate Laufzeitverifikation bleibt offen |
| `webapp/` als Verzeichnisname | vorerst ja | erst nach Git-Root-Lift | physischer Rename nicht vorziehen ohne gleichzeitige Repo-Vertragsumstellung |

## 8. Durchgeführte Änderungen

| Datei | Art der Änderung | Warum nötig | Push-relevant oder strukturell |
|---|---|---|---|
| `C:\dev\corapan\scripts\dev-start.ps1` | Resolver erweitert | Root-Wrapper fuer `app/` vorbereiten | push-relevant |
| `C:\dev\corapan\scripts\dev-setup.ps1` | Resolver erweitert | Root-Wrapper fuer `app/` vorbereiten | push-relevant |
| `C:\dev\corapan\scripts\blacklab\start_blacklab_docker_v3.ps1` | Resolver erweitert | Root-Wrapper fuer `app/` vorbereiten | push-relevant |
| `C:\dev\corapan\scripts\blacklab\build_blacklab_index.ps1` | Resolver erweitert | Root-Wrapper fuer `app/` vorbereiten | push-relevant |
| `C:\dev\corapan\scripts\blacklab\migrate_legacy_blacklab_dev_layout.ps1` | Resolver erweitert | Root-Wrapper fuer `app/` vorbereiten | push-relevant |
| `C:\dev\corapan\scripts\blacklab\run_export.py` | Resolver erweitert | Root-Wrapper fuer `app/` vorbereiten | push-relevant |
| `C:\dev\corapan\docker-compose.dev-postgres.yml` | app-dir-indirektion | Root-Compose rename-vorbereiten ohne aktuellen `webapp`-Betrieb zu brechen | push-relevant |
| `C:\dev\corapan\maintenance_pipelines\_1_blacklab\blacklab_export.py` | App-Resolver erweitert | Maintenance-Pipelines fuer `app/` vorbereiten | push-relevant |
| `C:\dev\corapan\maintenance_pipelines\_2_deploy\publish_blacklab.ps1` | App-Resolver erweitert | Maintenance-Pipelines fuer `app/` vorbereiten | push-relevant |
| `C:\dev\corapan\maintenance_pipelines\_2_deploy\deploy_data.ps1` | App-Resolver erweitert | Maintenance-Pipelines fuer `app/` vorbereiten | push-relevant |
| `C:\dev\corapan\maintenance_pipelines\_2_deploy\deploy_media.ps1` | App-Resolver erweitert | Maintenance-Pipelines fuer `app/` vorbereiten | push-relevant |
| `C:\dev\corapan\.github\instructions\backend.instructions.md` | `applyTo` erweitert | Root-Governance fuer `app/**` vorbereiten | strukturell |
| `C:\dev\corapan\.github\instructions\database.instructions.md` | `applyTo` erweitert | Root-Governance fuer `app/**` vorbereiten | strukturell |
| `C:\dev\corapan\.github\instructions\devops.instructions.md` | `applyTo` erweitert | Root-Governance fuer `app/**` vorbereiten | strukturell |
| `C:\dev\corapan\.github\workflows\ci.yml` | Prep-Workflow auf `app` umgestellt | kuenftigen Root-Push vorbereiten | strukturell, spaeter push-relevant |
| `C:\dev\corapan\.github\workflows\deploy.yml` | Prep-Workflow-Namen/Boundary angepasst | kuenftigen Root-Push vorbereiten | strukturell, spaeter push-relevant |
| `C:\dev\corapan\.github\workflows\md3-lint.yml` | Prep-Workflow auf `app` umgestellt | kuenftigen Root-Push vorbereiten | strukturell, spaeter push-relevant |
| `C:\dev\corapan\.github\workflows\README.md` | Boundary ergaenzt | Root-Prep-Layer explizit dokumentieren | strukturell |
| `C:\dev\corapan\.gitignore` | kanonisiert | kuenftiges Root-Repo korrekt abdecken | push-relevant |
| `C:\dev\corapan\README.md` | neu angelegt | Root-Systembeschreibung herstellen | push-relevant |
| `C:\dev\corapan\docs\repo_finish\repo_finish.md` | Plan aktualisiert | Pre-Push-Reihenfolge und Regeln praezisieren | push-relevant |

## 9. Offene Blocker

1. **Git-Root-Blocker (hoch)**
   - `C:\dev\corapan` ist noch kein echtes Git-Root.
   - Solange `.git` nur unter `webapp/` liegt, bleiben Root-README, Root-.gitignore, Root-Workflows und Maintenance-Vorbereitung ausserhalb der aktuellen versionierten Wahrheit.

2. **Workflow-Truth-Blocker (hoch)**
   - die echte versionierte CI-/Deploy-Wahrheit liegt noch unter `webapp/.github/workflows`
   - fuer den echten Root-Push muessen diese Workflows bewusst auf Root gehoben oder kontrolliert ersetzt werden

3. **Physischer Rename-Blocker (hoch)**
   - `webapp -> app` sollte nicht isoliert vor Git-Root-Lift passieren
   - sonst entsteht ein lokal veraenderter Pfad ohne vollstaendigen push-/workflow-sicheren Vertrag

4. **Restliche Text-/Hilfspfad-Altlasten (mittel)**
   - mehrere App-Skripte und Dokus nennen noch `webapp` als aktuellen Pfad
   - diese sind fuer den Pre-Push-Vertrag meist nicht hart blockierend, muessen aber im finalen Rename-Wave bereinigt werden

5. **Laufzeit-Nachverifikation (mittel)**
   - nach echtem Rename und Git-Root-Lift muessen Root-Compose, Root-Wrapper und aktive Mounts erneut kontrolliert validiert werden

## 10. Go / No-Go für Push

**NO-GO** fuer einen sofortigen Push, der gleichzeitig

- das Git-Root auf `C:\dev\corapan` hebt
- `webapp` physisch nach `app` umbenennt
- und den neuen Root-/Deploy-Vertrag ohne weitere Umstellung aktivieren soll

Begruendung:

- Git-Root ist noch nicht umgestellt
- die aktive versionierte Workflow-Wahrheit ist noch nicht von `webapp/.github/workflows` auf einen Root-konformen Zustand ueberfuehrt
- ein physischer Rename jetzt wuerde lokal vorbereiten, aber noch keinen abgesicherten Push-Vertrag herstellen

**GO mit Voraussetzungen** fuer den naechsten echten Schritt, wenn die Umstellung als kontrollierte atomare Root-Lift-Wave erfolgt:

1. Git-Root kontrolliert von `webapp/` nach `corapan/` heben.
2. Root-Workflow-Wahrheit bewusst etablieren.
3. `webapp -> app` in derselben Wave physisch ausfuehren.
4. Direkt danach Root-Compose, Wrapper, CI und Deploy einmal gegen das neue `app/`-Layout verifizieren.

Erst unter diesen vier Bedingungen ist ein Push nach Root-Lift/Rename belastbar freigabefaehig.