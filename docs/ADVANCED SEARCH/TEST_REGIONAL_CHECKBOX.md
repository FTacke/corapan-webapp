# Test: Regional Checkbox mit País-Dropdown

## Implementierte Änderungen

### 1. ✅ Checkbox "Incluir emisoras regionales"
- **Template**: `templates/search/advanced.html` - Checkbox existiert bereits als `include-regional`
- **FormHandler**: `static/js/modules/advanced/formHandler.js` - Parameter wird korrekt serialisiert (`include_regional=1`)

### 2. ✅ Backend-Filter in `cql.py`
Die `build_filters()` Funktion wurde erweitert:

#### Standardfall (Checkbox NICHT gesetzt):
```python
# Wenn country_code = "ESP" → nur nationale Sendungen
if is_iso3 and not include_regional:
    filters["country_parent_code"] = ["ESP"]
    filters["country_scope"] = "national"
```

**CQL-Effekt**: `country_parent_code="ESP" & country_scope="national"`

#### Checkbox gesetzt (include_regional = True):
```python
# Wenn country_code = "ESP" → nationale + regionale Sendungen
if is_iso3 and include_regional:
    filters["country_parent_code"] = ["ESP"]
    # Kein country_scope → beide Scopes
```

**CQL-Effekt**: `country_parent_code="ESP"` (ohne Scope-Filter)

#### Regionale Codes (nur bei aktivierter Checkbox):
```python
# Wenn country_code = "ESP-CAN" und Checkbox gesetzt
if is_regional and include_regional:
    parent, region = country_code.split("-", 1)
    filters["country_parent_code"] = ["ESP"]
    filters["country_region_code"] = ["ESP-CAN"]
    filters["country_scope"] = "regional"
```

**CQL-Effekt**: `country_parent_code="ESP" & country_region_code="ESP-CAN" & country_scope="regional"`

### 3. ✅ País-Dropdown mit regionalen Codes
**Template-Änderungen**:
- Nationale Codes (immer sichtbar): `ARG`, `ESP`, `MEX`, etc.
- Regionale Codes (nur bei Checkbox): `ARG-CBA`, `ARG-CHU`, `ARG-SDE`, `ESP-CAN`, `ESP-SEV`
- JavaScript-Toggle-Logik für Ein-/Ausblenden

**Regionale Codes im System**:
- Argentinien: `ARG-CBA` (Córdoba), `ARG-CHU` (Chubut), `ARG-SDE` (Santiago del Estero)
- Spanien: `ESP-CAN` (Canarias), `ESP-SEV` (Sevilla)

### 4. ✅ Lowercasing aufgeräumt
**Beibehaltene Lowercasing-Stellen**:
- `lemma` → `.lower()` (Lemmata sind normalisiert)
- `norm` Feld → `.lower()` (für case-insensitive Forma-Suche)
- `pos` → `.upper()` (POS-Tags sind uppercase)

**Entfernte Lowercasing-Stellen**:
- `country_code`, `country_parent_code`, `country_region_code` → kein `.lower()`
- `speaker_type`, `speaker_sex`, `speaker_mode`, `speaker_discourse` → kein `.lower()`
- `radio`, `city` → kein `.lower()`

**Begründung**: BlackLab-Felder sind als `ONLY_INSENSITIVE` konfiguriert → case-insensitive Suche ohne Lowercasing notwendig. Großbuchstaben (ARG, ESP-CAN) sind lesbarer.

---

## Testplan

### Test 1: Checkbox aus, País = ESP
**Erwartung**:
- Im Dropdown: nur `ESP` (keine `ESP-CAN`, `ESP-SEV`)
- Treffer: nur `country_scope="national"` + `country_parent_code="ESP"`
- CQL: `country_parent_code="ESP" & country_scope="national"`

**Schritte**:
1. Öffne `/search/advanced`
2. Stelle sicher, dass Checkbox "Incluir emisoras regionales" NICHT angehakt ist
3. Öffne País-Dropdown → nur nationale Codes sichtbar
4. Wähle `ESP`
5. Gib eine Query ein (z.B. `casa`)
6. Suche starten
7. Browser DevTools → Network Tab → CQL-Parameter prüfen
8. Ergebnisse prüfen: nur nationale ESP-Sendungen

### Test 2: Checkbox an, País = ESP
**Erwartung**:
- Im Dropdown: `ESP` + `ESP-CAN` + `ESP-SEV` (eingerückt)
- Treffer: `country_parent_code="ESP"` (beide Scopes)
- CQL: `country_parent_code="ESP"` (ohne Scope-Filter)

**Schritte**:
1. Hacke Checkbox "Incluir emisoras regionales" an
2. Öffne País-Dropdown → regionale Codes unter ESP sichtbar
3. Wähle nur `ESP` (nationale)
4. Gib Query ein
5. Suche starten
6. CQL prüfen: `country_parent_code="ESP"` (kein `country_scope`)
7. Ergebnisse: nationale + regionale ESP-Sendungen

### Test 3: Checkbox an, País = ESP-CAN
**Erwartung**:
- Treffer: nur regionale Sendungen aus ESP-CAN
- CQL: `country_parent_code="ESP" & country_region_code="ESP-CAN" & country_scope="regional"`

**Schritte**:
1. Checkbox "Incluir emisoras regionales" angehakt
2. País-Dropdown öffnen
3. Wähle `ESP-CAN` (regionaler Code)
4. Query eingeben
5. Suche starten
6. CQL prüfen: alle drei Filter gesetzt
7. Ergebnisse: nur ESP-CAN-Sendungen

### Test 4: Checkbox an → aus (mit ausgewähltem regionalem Code)
**Erwartung**:
- Beim Abwählen der Checkbox werden regionale Codes ausgeblendet UND deselektiert
- Suche läuft nur mit nationalen Codes

**Schritte**:
1. Checkbox anhaken, `ESP-CAN` auswählen
2. Checkbox wieder abhaken
3. Prüfen: `ESP-CAN` sollte deselektiert werden
4. Suche starten → nur nationale Codes aktiv

### Test 5: Lowercasing-Prüfung
**Erwartung**:
- Country-Codes in CQL: `ARG`, `ESP`, `ESP-CAN` (Großbuchstaben, kein lowercase)
- Lemma-Suche: `lemma="casa"` (lowercase)
- Radio/City: keine Umwandlung in lowercase

**Schritte**:
1. Suche mit País=ARG
2. DevTools → CQL prüfen: `country_parent_code="ARG"` (nicht "arg")
3. Lemma-Suche mit "Casa"
4. CQL prüfen: `lemma="casa"` (lowercase)

---

## Debugging-Tipps

### CQL in Browser DevTools prüfen
1. Browser DevTools öffnen (F12)
2. Network Tab
3. Suche ausführen
4. Request zu `/bls/corpora/corapan/hits` suchen
5. Query-Parameter `patt=` oder `cql=` prüfen

### Backend-Logs
```powershell
# Flask-Logs in Terminal beobachten
# Logger in cql.py schreibt Filter-Info:
# "Metadata CQL constraints: country_parent_code=\"ESP\" & country_scope=\"national\""
```

### Häufige Probleme
1. **Regionale Codes nicht sichtbar**: JavaScript nicht geladen oder Checkbox-Event nicht gebunden
2. **Falsche CQL-Constraints**: `build_filters()` prüfen, Logger-Ausgabe checken
3. **Keine Treffer**: Prüfen ob regionale Codes im Index existieren (BlackLab `/listvalues/country_region_code`)

---

## Zusammenfassung

✅ Checkbox "Incluir emisoras regionales" vollständig integriert
✅ Backend-Filter für national/regional-Logik implementiert
✅ País-Dropdown zeigt regionale Codes bei aktivierter Checkbox
✅ Lowercasing auf notwendige Stellen reduziert (lemma, norm, pos)
✅ Keine Breaking Changes, vollständig rückwärtskompatibel

**Bereit für Tests!**
