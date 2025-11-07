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

## ⚠️ PRÜFUNG ERFORDERLICH

### 1. Token Input Multi-Paste
- **Datei:** `docs/token-input-multi-paste.md`
- **Grund:** Feature-Dokumentation vom 2025-10-17
- **Frage:** Ist dieses Feature noch in Verwendung oder wurde es durch neuere Implementierung ersetzt?
- **Empfehlung:** Falls Feature aktiv → behalten, sonst → löschen oder zu `design-system.md` mergen
- **Risiko:** Mittel - falls Feature noch genutzt wird

### 2. Migration Token-ID v2
- **Datei:** `LOKAL/records/docs/MIGRATION-TOKEN-ID-V2.md`
- **Grund:** Migrations-Dokumentation für Token-ID-System
- **Frage:** Ist die Migration abgeschlossen?
- **Status:** Sehr detailliert (320 Zeilen), scheint wichtig
- **Empfehlung:** Falls Migration abgeschlossen → in `LOKAL/records/archived_docs/migration/` verschieben
- **Risiko:** Hoch - enthält wichtige technische Details für Rollback

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
10. **troubleshooting.md** - ✅ Debug-Guide für häufige Probleme

### Records & Process Logs (LOKAL/records/)
11. **LOKAL/records/README.md** - ✅ Autoritative Regeln für Records
12. **LOKAL/records/PROCESS_LOG.md** - ✅ Prozess-Historie

---

## 📊 ZUSAMMENFASSUNG

| Kategorie | Anzahl | Aktion |
|-----------|--------|--------|
| **Kann gelöscht werden** | 4 Items | 🗑️ Nach Bestätigung löschen |
| **Prüfung erforderlich** | 2 Items | ⚠️ Inhalt/Status prüfen |
| **Behalten** | 12 Items | ✅ Essential für Betrieb |

---

## 🚀 EMPFOHLENE VORGEHENSWEISE

### Schritt 1: Sofortige Löschung (nach Bestätigung)
```powershell
# Bug Report archivieren
Move-Item "docs\bug-report-auth-session.md" "LOKAL\records\archived_docs\bugs\bug-report-auth-session.md"

# Bereits archivierte Docs löschen
Remove-Item "LOKAL\records\docs\2025-10-26__docs__archived-doc__*.md"
Remove-Item "LOKAL\records\tests\2025-10-26__tests__archived-doc__*.md"
```

### Schritt 2: Prüfung durchführen
```powershell
# Token-Input Feature-Verwendung prüfen
Select-String -Pattern "parseMultipleTokenIds" -Path "static\js\**\*.js" -Recurse

# Migration-Status prüfen
Select-String -Pattern "MIGRATE_V2" -Path "LOKAL\**\*.py" -Recurse
```

### Schritt 3: Nach Prüfung
- Falls Token-Input aktiv → `token-input-multi-paste.md` behalten
- Falls Migration abgeschlossen → `MIGRATION-TOKEN-ID-V2.md` nach `LOKAL/records/archived_docs/migration/` verschieben

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

1. **Bestätigung** der "Kann gelöscht werden" Items
2. **Prüfung** der "Prüfung erforderlich" Items durchführen
3. **Archivierung** statt Löschung für historisch wichtige Docs
4. **Git Commit** nach allen Änderungen
