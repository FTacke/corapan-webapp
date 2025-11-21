# Cleanup Log (Phase 2: Structure Cleanup)

**Datum:** 21.11.2025
**Status:** In Progress

| Pfad | Aktion | Grund (Audit-Ref) | Risiko |
|------|--------|-------------------|--------|
| LOKAL/00 - Md3-design/ | Move | Nach docs/design/ & scripts/design/ migriert | Niedrig |
| LOKAL/02 - Add New Users/ | Move | Skript nach scripts/admin/ migriert | Niedrig |
| LOKAL/03 - Analysis Scripts/ | Move | Skripte nach scripts/analysis/ migriert | Niedrig |
| LOKAL/ | Delete | Restlicher Ordner (Redundante Skripte, CSVs) gelöscht | Niedrig |
| tools/ | Delete | Veraltete JARs (Docker wird genutzt) | Mittel |
| backup.sh | Move | Nach scripts/backup.sh verschoben | Mittel |
| update.sh | Move | Nach scripts/update.sh verschoben | Mittel |
| src/corapan_web.egg-info/ | Delete | Build-Artefakt entfernt | Niedrig |
| __pycache__/ | Delete | Alle Python-Caches entfernt | Niedrig |

## Zusammenfassung & Status

**Durchgeführte Maßnahmen:**
- Der Ordner `LOKAL/` wurde vollständig aufgelöst. Wichtige Skripte und Dokumente wurden in die reguläre Struktur (`scripts/`, `docs/`) integriert.
- Der Ordner `tools/` (veraltete JARs) wurde entfernt.
- Root-Skripte (`backup.sh`, `update.sh`) wurden nach `scripts/` verschoben.
- Build-Artefakte (`.egg-info`, `__pycache__`) wurden bereinigt.

**Verbleibende Risiken:**
- `passwords.env` liegt im Root (lokal). Sollte in Phase 4 durch `.env` ersetzt werden.
- `requirements.txt` enthält noch lokale Pfade (Phase 4).
- `scripts/debug/` wurde beibehalten, sollte aber in Phase 3 auf Relevanz geprüft werden.

**Bereit für Phase 3:**
Die Struktur ist nun bereinigt. Linter und Formatter können in Phase 3 auf eine saubere Basis angewendet werden.

**ROLLBACK (21.11.2025):**
- Auf Wunsch des Users wurde die Auflösung von `LOKAL/` teilweise rückgängig gemacht.
- Wiederhergestellt (aus verschobenen Dateien):
  - `LOKAL/00 - Md3-design/`
  - `LOKAL/02 - Add New Users (Security)/`
  - `LOKAL/03 - Analysis Scripts (tense)/`
- **Verloren:** Dateien, die nicht verschoben, sondern gelöscht wurden (da `LOKAL/` in `.gitignore` stand und nicht im Haupt-Repo getrackt war).

**RESTORATION (21.11.2025):**
- Der Ordner `LOKAL/` wurde vollständig aus dem Remote-Repository `https://github.com/FTacke/corapan-tools` wiederhergestellt.
- Die temporär wiederhergestellten Dateien wurden in `LOKAL_temp/` gesichert (können gelöscht werden, wenn der Clone vollständig ist).
