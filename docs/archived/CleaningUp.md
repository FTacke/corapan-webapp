# CO.RA.PAN - Cleaning Up Analysis

**Datum:** 2025-11-07  
**Status:** Zur Bestätigung  
**Kontext:** Nach erfolgreicher Migration zur neuen Webapp - Identifikation von Legacy-Files und Backups

---

## 🟢 DEFINITIV LÖSCHBAR

### Ruff Cache
- **Pfad:** `.ruff_cache/`
- **Grund:** Automatisch generierter Linter-Cache, wird bei Bedarf neu erstellt
- **Aktion:** Löschen und zu `.gitignore` hinzufügen (falls noch nicht)

---

## 🟡 VERMUTLICH LÖSCHBAR (Bitte Bestätigen)

### 1. Temporary Stats Files
- **Pfad:** `data/stats_temp/*.json`
- **Dateien:** 11 JSON-Files (07c84814ea42dfa1.json, 3031e1c20f169905.json, etc.)
- **Grund:** Temporäre Cache-Dateien für Stats-Feature, werden automatisch regeneriert
- **Empfehlung:** Löschen, da Cache-Files. Werden bei Bedarf neu erstellt
- **Risiko:** Minimal - nur Performance-Impact bei erster Stats-Abfrage nach Löschung

### 2. Log Files (falls vorhanden)
- **Pfad:** `logs/*.log`
- **Grund:** Alte Log-Einträge, die nicht mehr benötigt werden
- **Empfehlung:** Archivieren oder löschen (abhängig von Debug-Bedarf)
- **Risiko:** Gering - historische Logs können hilfreich sein, aber nicht essentiell

### 3. Node Modules Build-Artefakte
- **Pfad:** `node_modules/`
- **Grund:** Wird durch `npm install` neu erstellt
- **Status:** Bereits in `.gitignore`, aber könnte lokal gelöscht und neu installiert werden
- **Empfehlung:** Bei Bedarf durch `npm install` neu erstellen
- **Risiko:** Keines - wird automatisch regeneriert

### 4. Python Virtual Environment Cache
- **Pfad:** `.venv/`
- **Grund:** Lokale Entwicklungsumgebung, wird durch `python -m venv .venv` neu erstellt
- **Status:** Bereits in `.gitignore`
- **Empfehlung:** Nur bei Problemen neu erstellen
- **Risiko:** Keines - vollständig reproduzierbar

---

## 🔴 UNSICHER / KLÄRUNGSBEDARF

### 1. GitLab-Ordner
- **Pfad:** `.gitlab/`
- **Status:** Prüfung erforderlich
- **Frage:** Enthält dieser Ordner CI/CD-Konfigurationen oder Templates?
- **Empfehlung:** Inhalt prüfen bevor Entscheidung getroffen wird
- **Aktion:** `ls -la .gitlab/` ausführen und Inhalt dokumentieren

### 2. Static-Build Ordner
- **Pfad:** `static-build/assets/`
- **Grund:** Build-Artefakte von Vite
- **Frage:** Werden diese für Production-Builds benötigt oder nur lokal generiert?
- **Empfehlung:** Falls durch `npm run build` reproduzierbar → löschbar
- **Risiko:** Mittel - falls für Docker-Deployment benötigt, könnte es Probleme geben
- **Aktion:** Prüfen ob `Dockerfile` diese Dateien kopiert

### 3. Data Public Ordner
- **Pfad:** `data/db_public/`
- **Status:** Leer oder mit Inhalt?
- **Frage:** Wird dieser Ordner von der App genutzt?
- **Empfehlung:** Inhalt prüfen und Verwendung in Code suchen
- **Aktion:** `grep -r "db_public" src/` ausführen

### 4. MP3-Temp Ordner Inhalt
- **Pfad:** `media/mp3-temp/`
- **Grund:** Temporäre Audio-Snippets, sollten auto-cleanup haben
- **Frage:** Enthält er alte Files die nicht automatisch gelöscht wurden?
- **Empfehlung:** Files älter als 30 Minuten löschen (gemäß Dokumentation)
- **Risiko:** Gering - sind temporär, aber aktive Sessions könnten betroffen sein

### 5. Passwords.env vs. Template
- **Pfad:** `passwords.env`
- **Status:** Enthält echte Credentials (nicht in Git)
- **Frage:** Wird diese Datei noch benötigt oder durch Environment-Variables ersetzt?
- **Empfehlung:** Behalten, aber sicherstellen dass sie nicht versehentlich committed wird
- **Risiko:** Hoch - enthält sensible Daten

---

## ✅ DEFINITIV BEHALTEN

### Produktions-Critical
1. **src/app/** - Gesamter Anwendungscode
2. **templates/** - HTML-Templates
3. **static/css/, static/js/, static/fonts/, static/img/** - Frontend-Assets
4. **media/mp3-full/, media/mp3-split/, media/transcripts/** - Media-Dateien
5. **data/db/** - Produktions-Datenbank
6. **data/counters/** - Counter-JSON (wird von App geschrieben)
7. **config/keys/** - JWT-Keys (sensibel!)

### Build & Deployment
8. **Dockerfile** - Container-Build
9. **docker-compose.yml** - Container-Orchestration
10. **requirements.txt** - Python-Dependencies
11. **package.json, package-lock.json** - Node-Dependencies
12. **pyproject.toml** - Python-Projekt-Konfiguration
13. **backup.sh, update.sh** - Deployment-Scripts
14. **.dockerignore, .gitignore** - Git/Docker-Konfiguration

### Dokumentation & Config
15. **README.md** - Projekt-Dokumentation
16. **DEPLOYMENT.md** - Deployment-Guide
17. **GIT_SECURITY_CHECKLIST.md** - Security-Checklist
18. **startme.md** - Quick-Start-Guide
19. **docs/** - Gesamte Dokumentation
20. **passwords.env.template** - Template für Credentials

### Entwicklungs-Tools
21. **tailwind.config.js** - Tailwind-Konfiguration
22. **vite.config.js** - Vite-Build-Konfiguration
23. **.htmlhintrc** - HTML-Linter-Config
24. **.vscode/** - VS Code-Settings (für Entwicklung)

### Git & CI/CD
25. **.git/** - Git-Repository
26. **.gitattributes** - Git-Attribut-Konfiguration
27. **.gitlab-ci.yml** - CI/CD-Pipeline
28. **.gitlab/** - GitLab-spezifische Configs (nach Prüfung)

### LOKAL-Ordner
29. **LOKAL/** - Maintenance-Scripts und lokale Dokumentation
    - **LOKAL/00 - Md3-design/** - Design-System-Dokumentation
    - **LOKAL/01 - Add New Transcriptions/** - Maintenance-Scripts
    - **LOKAL/02 - Add New Users (Security)/** - User-Management-Scripts
    - **LOKAL/03 - Analysis Scripts (tense)/** - Analyse-Scripts
    - **LOKAL/records/** - Prozess-Dokumentation und Records
    - **Alle anderen Unterordner in LOKAL/** - Wie vereinbart nicht antasten

---

## 📊 ZUSAMMENFASSUNG

| Kategorie | Anzahl | Status |
|-----------|--------|--------|
| **Definitiv löschbar** | 1 Item | 🟢 Kann sofort gelöscht werden |
| **Vermutlich löschbar** | 4 Kategorien | 🟡 Nach Bestätigung löschen |
| **Unsicher** | 5 Items | 🔴 Klärung erforderlich |
| **Behalten** | 29 Kategorien | ✅ Essential für Betrieb |

---

## 🚀 EMPFOHLENE VORGEHENSWEISE

### Phase 1: Sofortige Aktionen
1. `.ruff_cache/` löschen
2. Prüfung der unsicheren Items durchführen:
   ```powershell
   # GitLab-Ordner prüfen
   Get-ChildItem -Path ".gitlab" -Recurse
   
   # db_public Verwendung suchen
   Select-String -Pattern "db_public" -Path "src\**\*.py" -Recurse
   
   # Static-Build in Dockerfile prüfen
   Select-String -Pattern "static-build" -Path "Dockerfile"
   
   # Alte mp3-temp Files finden (älter als 1 Tag)
   Get-ChildItem -Path "media\mp3-temp" -Filter "*.mp3" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-1) }
   ```

### Phase 2: Nach Bestätigung
3. `data/stats_temp/*.json` löschen (werden regeneriert)
4. Alte Logs archivieren oder löschen
5. Entscheidung zu `static-build/` basierend auf Dockerfile-Analyse

### Phase 3: Wartung
6. Automatisches Cleanup für `media/mp3-temp/` einrichten (falls noch nicht vorhanden)
7. Log-Rotation konfigurieren
8. Backup-Strategie für wichtige Dateien überprüfen

---

## ⚠️ WICHTIGE HINWEISE

### Vor dem Löschen IMMER:
1. **Backup erstellen:** `./backup.sh --full`
2. **Git-Status prüfen:** `git status` (nichts Wichtiges uncommitted?)
3. **App-Status prüfen:** Läuft die App? Sind User aktiv?
4. **Rollback-Plan:** Wie kann ich wiederherstellen?

### Nach dem Löschen:
1. **Functionality-Test:** App starten und grundlegende Features testen
2. **Log-Check:** Logs auf Fehler prüfen
3. **Performance-Check:** Sind Stats/Search noch schnell?

---

## 📝 NÄCHSTE SCHRITTE

1. **Bestätigung der "Vermutlich löschbar" Items**
2. **Klärung der "Unsicher" Items** (siehe empfohlene Prüfbefehle oben)
3. **Ausführung Phase 1** (siehe oben)
4. **Feedback geben** für Phase 2 Entscheidungen
