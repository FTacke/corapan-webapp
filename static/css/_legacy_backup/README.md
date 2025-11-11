# Legacy CSS Backup

**Datum:** 2025-10-31  
**Aktion:** Phase 1 - Legacy-CSS-Cleanup

## Verschobene Dateien

Diese CSS-Dateien wurden in der MD3-Migration nicht mehr verwendet und in dieses Backup-Verzeichnis verschoben:

| Datei | Größe | Beschreibung | Status |
|-------|-------|--------------|--------|
| `tokens.css` | 1.7 KB | Alte Token-Definitionen (pre-MD3) | ❌ Ersetzt durch `md3/tokens.css` |
| `components.css` | 58.8 KB | Monolithische Komponenten-Datei | ❌ Ersetzt durch `md3/components/*.css` |
| `md3-tokens.css` | 12.0 KB | Frühe MD3-Token-Implementierung | ❌ Ersetzt durch `md3/tokens.css` |
| `md3-components.css` | 81.6 KB | Frühe MD3-Komponenten (3.329 Zeilen!) | ❌ Styles in neue Komponenten übertragen |
| `nav_new.css` | 13.4 KB | Alte Navigation-Styles | ❌ Ersetzt durch `md3/components/navbar.css` |
| `editor.css` | 21.8 KB | Alte Editor-Styles | ❌ Ersetzt durch `md3/components/editor-*.css` |

**Gesamt:** 189 KB Legacy-CSS entfernt

## Verifizierung

Alle verschobenen Dateien wurden vor dem Verschieben geprüft:

```powershell
# Prüfung: Werden diese Dateien noch geladen?
grep -r "tokens.css" templates/            # Nur md3/tokens.css gefunden
grep -r "components.css" templates/        # Keine Treffer
grep -r "md3-tokens.css" templates/        # Keine Treffer
grep -r "md3-components.css" templates/    # Keine Treffer (nur Kommentare)
grep -r "nav_new.css" templates/           # Keine Treffer
grep -r "editor.css" templates/            # Keine Treffer
```

**Ergebnis:** ✅ Keine der Legacy-Dateien wird mehr von aktiven Templates geladen!

## Kann ich diese Dateien löschen?

**Nach erfolgreicher QA (alle Seiten getestet):** JA

**Empfohlene QA-Schritte:**

1. Dev-Server starten: `python -m src.app.main`
2. Alle Seiten im Browser öffnen (mit Hard-Refresh: Strg+Shift+R)
3. Visuell prüfen: Design sieht korrekt aus?
4. Mobile-Ansicht testen (DevTools Responsive Mode)

**Getestete Seiten:**
- [ ] http://localhost:8000/ (Index)
- [ ] http://localhost:8000/atlas
- [ ] http://localhost:8000/corpus
- [ ] http://localhost:8000/player
- [ ] http://localhost:8000/proyecto/overview
- [ ] http://localhost:8000/proyecto/diseno
- [ ] http://localhost:8000/proyecto/estadisticas
- [ ] http://localhost:8000/proyecto/quienes-somos
- [ ] http://localhost:8000/proyecto/como-citar
- [ ] http://localhost:8000/impressum
- [ ] http://localhost:8000/privacy

**Falls alle Seiten korrekt aussehen:**

```powershell
# Backup dauerhaft löschen
Remove-Item "static/css/_legacy_backup" -Recurse -Force
```

## Was wurde migriert?

Alle Styles aus den Legacy-Dateien wurden in das neue MD3-System übertragen:

### `md3-components.css` → Neue Struktur

| Legacy-Section | Neue Datei |
|----------------|------------|
| Buttons (Lines 646-800) | `md3/components/buttons.css` |
| Textfields (Lines 1298-1470) | `md3/components/textfields.css` |
| Forms (Lines 1471-1732) | `md3/components/forms.css` |
| Tabs (Lines 1734-1788) | `md3/components/tabs.css` |
| DataTables (Lines 2200-2700) | `md3/components/datatables.css` |
| Navbar | `md3/components/navbar.css` |
| Hero | `md3/components/hero.css` |
| Text Pages | `md3/components/text-pages.css` |

Siehe Kommentare in den neuen CSS-Dateien für Details.

---

**Erstellt von:** GitHub Copilot  
**Referenz:** `LOKAL/records/frontend/finding/2025-01-31__webapp-audit-report.md`
