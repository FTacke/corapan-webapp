# CO.RA.PAN - Obsolete Documentation Analysis

**Datum:** 2025-11-07  
**Status:** Zur Bestätigung  
**Kontext:** Nach Migration - Identifikation obsoleter Dokumentationen

---

## 🗑️ KANN GELÖSCHT WERDEN

### 1. Bug Report - Auth Session Issue
- **Datei:** `docs/bug-report-auth-session.md`
- **Grund:** Bug wurde behoben durch `/auth/ready` Intermediate Page (dokumentiert in `auth-flow.md`)
- **Status:** Historischer Bug-Report, nicht mehr relevant
- **Empfehlung:** Archivieren in `LOKAL/records/archived_docs/bugs/` oder löschen
- **Risiko:** Keines - Bug ist gelöst

### 2. Archived Docs in LOKAL/records
- **Dateien:**
  - `LOKAL/records/docs/2025-10-26__docs__archived-doc__annotation_data_future_use.md`
  - `LOKAL/records/docs/2025-10-26__docs__archived-doc__project-now.md`
  - `LOKAL/records/tests/2025-10-26__tests__archived-doc__tests_token_snapshot.md`
- **Grund:** Bereits im Dateinamen als "archived-doc" markiert
- **Status:** Archivierte Records, vermutlich nicht mehr benötigt
- **Empfehlung:** Nach Prüfung des Inhalts (für historischen Kontext) löschen
- **Risiko:** Minimal - sind bereits archiviert

---

## ⚠️ PRÜFUNG DURCHGEFÜHRT

### 1. Token Input Multi-Paste ✅ BEHALTEN
- **Datei:** `docs/token-input-multi-paste.md`
- **Status:** Feature ist AKTIV
- **Evidenz:** 3 Verwendungen in `static/js/modules/corpus/tokens.js` (lines 103, 123, 141)
- **Aktion:** ✅ BEHALTEN - wird noch verwendet
- **Grund:** Funktion `parseMultipleTokenIds()` wird aktiv aufgerufen für Token-Eingaben

### 2. Migration Token-ID v2 ✅ ARCHIVIERT
- **Datei:** `LOKAL/records/docs/MIGRATION-TOKEN-ID-V2.md`
- **Status:** Migration abgeschlossen
- **Evidenz:** `MIGRATE_V2` ist in Code auf `False` gesetzt in `database_creation_v2.py` (line 29)
- **Aktion:** ✅ ARCHIVIERT zu `LOKAL/records/archived_docs/migration/MIGRATION-TOKEN-ID-V2.md`
- **Grund:** Vollständig abgeschlossen, aber historisch wichtig für Rollback-Wissen

---

## ✅ DEFINITIV BEHALTEN

### Technische Dokumentation (docs/)
1. **architecture.md** - ✅ Core-Dokumentation der App-Architektur
2. **auth-flow.md** - ✅ Wichtig für Authentifizierung und JWT-System
3. **database_maintenance.md** - ✅ Essential für DB-Wartung und Updates
4. **design-system.md** - ✅ Design-Tokens und Styling-Guidelines
5. **gitlab-setup.md** - ✅ CI/CD und Repository-Konfiguration
6. **media-folder-structure.md** - ✅ Wichtig für Media-Handling
7. **mobile-speaker-layout.md** - ✅ Mobile-Optimierung Spezifikation
8. **roadmap.md** - ✅ Entwicklungs-Roadmap
9. **stats-interactive-features.md** - ✅ Stats-Feature Dokumentation
10. **token-input-multi-paste.md** - ✅ Token-Input Feature (AKTIV in Verwendung!)
11. **troubleshooting.md** - ✅ Debug-Guide für häufige Probleme

### Records & Process Logs (LOKAL/records/)
11. **LOKAL/records/README.md** - ✅ Autoritative Regeln für Records
12. **LOKAL/records/PROCESS_LOG.md** - ✅ Prozess-Historie

---

## 📊 ZUSAMMENFASSUNG

| Kategorie | Anzahl | Aktion |
|-----------|--------|--------|
| **Gelöscht** | 4 Items | ✅ **ERLEDIGT** |
| **Archiviert** | 1 Item | ✅ **ERLEDIGT** |
| **Behalten** | 13 Items | ✅ **FINAL** |

---

## 🚀 EMPFOHLENE VORGEHENSWEISE

**ALLE SCHRITTE SIND JETZT ERLEDIGT! ✅**

### ✅ Schritt 1: ABGESCHLOSSEN
- Bug Report archiviert zu `LOKAL/records/archived_docs/bugs/`
- 3 bereits archivierte Docs gelöscht
- Git Commit: `docs: archive bug-report-auth-session.md and remove archived-doc files`

### ✅ Schritt 2: PRÜFUNG DURCHGEFÜHRT
- Token-Input Feature: ✅ AKTIV (3 Verwendungen in static/js/modules/corpus/tokens.js)
- MIGRATE_V2: ✅ ABGESCHLOSSEN (variable auf False in database_creation_v2.py)

### ✅ Schritt 3: ARCHIVIERUNG ERLEDIGT
- `token-input-multi-paste.md` - ✅ BEHALTEN (wird verwendet!)
- `MIGRATION-TOKEN-ID-V2.md` - ✅ ARCHIVIERT zu `LOKAL/records/archived_docs/migration/`

---

## ⚠️ WICHTIGE HINWEISE

### Vor dem Löschen:
1. **Git Commit:** Aktuellen Stand committen
2. **Backup:** Sicherstellen dass alles in Git ist
3. **Review:** Nochmal kurz Inhalt überfliegen

### Archivierungs-Struktur:
```
LOKAL/records/archived_docs/
├── bugs/
│   └── bug-report-auth-session.md
├── migration/
│   └── MIGRATION-TOKEN-ID-V2.md (falls Migration abgeschlossen)
└── features/
    └── token-input-multi-paste.md (falls obsolet)
```

---

## 📝 NÄCHSTE SCHRITTE

✅ **ALLE ARBEITEN ABGESCHLOSSEN!**

- [x] Bug Report archiviert
- [x] Archivierte Docs gelöscht
- [x] Token-Input Feature Status geprüft (aktiv, behalten)
- [x] Migration Status geprüft (abgeschlossen, archiviert)
- [x] Git Commits gemacht

Die Dokumentation ist jetzt bereinigt und organisiert! 🎉
