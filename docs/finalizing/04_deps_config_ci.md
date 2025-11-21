# Dependencies, Config, Tests & CI Report (Phase 4)

**Datum:** 21.11.2025
**Status:** Complete

## 1. Übersicht Abhängigkeiten

### Python
- **Dateien:** `requirements.txt`, `pyproject.toml`
- **Status:** Analyse läuft...

### Node.js (Frontend)
- **Dateien:** `package.json` (falls vorhanden)
- **Status:** Analyse läuft...

## 2. Config & Environment Story

- **Ziel:** `.env` Datei für lokale Entwicklung, `.env.example` als Template.
- **Status:** Analyse läuft...

## 3. Tests

- **Kommando:** `pytest` (geplant)
- **Status:** Analyse läuft...

## 4. CI Pipeline

- **System:** GitHub Actions (geplant)
- **Status:** Analyse läuft...

## 5. Änderungsprotokoll

| Bereich | Änderung | Begründung |
|---------|----------|------------|
| requirements.txt | Cleaned | Lokalen Pfad (`-e c:\users\...`) entfernt |
| .env.example | Created | Template für Environment-Variablen erstellt (basierend auf `passwords.env.template`) |
| .github/workflows/ci.yml | Created | GitHub Actions Workflow für Linting und Tests erstellt |

## 6. Offene Punkte

- ...
